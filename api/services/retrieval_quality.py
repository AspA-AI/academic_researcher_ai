"""
Retrieval quality utilities:
- rerank + threshold filtering
- evidence sufficiency gates
- user-facing failure messages

This module is intentionally standalone to keep retrieval policy separate from
pipeline orchestration and vector DB plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from api.utils.reranking import CrossEncoderReranker


@dataclass(frozen=True)
class RetrievalQualityConfig:
    # Candidate pool size factor (retrieve wide, then rerank+filter)
    candidate_multiplier: int = 5

    # Evidence sufficiency
    # NOTE: We'll report "unique papers vs requested" as a flag, but do not hard-fail the pipeline on it.
    min_unique_papers: int = 0
    min_results_after_filter: int = 8

    # Rerank thresholds (scores are model-dependent; treat as tunables)
    # Hard floor (still useful as a safeguard), but filtering should be adaptive.
    min_rerank_score: float = 0.0
    # User guidance: 0.8+ is a reasonable "strong match" signal when scores are normalized to [0,1].
    min_avg_rerank_score: float = 0.80

    # Adaptive filtering: keep docs with score >= percentile(score_distribution)
    # Example: 0.60 means keep roughly the top 40% by score.
    rerank_keep_percentile: float = 0.60

    # Paper-level diversification (avoid 20 chunks from 1 paper)
    max_chunks_per_paper: int = 1

    # Loop protection
    max_retrieval_attempts: int = 2
    max_extraction_attempts: int = 1


def _paper_key(doc: Dict[str, Any]) -> str:
    doi = (doc.get("doi") or "").strip().lower()
    if doi and doi != "none":
        return f"doi:{doi}"
    title = (doc.get("title") or "").strip().lower()
    if title:
        return f"title:{title}"
    paper_id = (doc.get("paper_id") or "").strip().lower()
    if paper_id and paper_id != "none":
        return f"id:{paper_id}"
    # Fallback to uuid/chunk identity
    return f"uuid:{(doc.get('uuid') or '')}:{doc.get('chunk_index', 0)}"


def count_unique_papers(docs: Sequence[Dict[str, Any]]) -> int:
    return len({_paper_key(d) for d in docs})


def diversify_by_paper(
    docs: Sequence[Dict[str, Any]],
    *,
    max_papers: int,
    max_chunks_per_paper: int = 1,
) -> List[Dict[str, Any]]:
    """
    Ensure retrieval returns diverse papers instead of many chunks from a single paper.
    Uses rerank_score (if present) to pick best chunks per paper.
    """
    if not docs:
        return []

    # Group docs by paper
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for d in docs:
        groups.setdefault(_paper_key(d), []).append(d)

    def doc_score(x: Dict[str, Any]) -> float:
        meta = x.get("metadata") or {}
        s = meta.get("rerank_score")
        return float(s) if isinstance(s, (int, float)) else 0.0

    # Sort each paper's chunks by rerank_score desc
    for k in groups:
        groups[k].sort(key=doc_score, reverse=True)

    # Rank papers by their best chunk score desc
    ranked_papers = sorted(groups.keys(), key=lambda k: doc_score(groups[k][0]), reverse=True)

    out: List[Dict[str, Any]] = []
    for pk in ranked_papers[:max_papers]:
        out.extend(groups[pk][: max(1, int(max_chunks_per_paper))])
    return out


def attach_rerank_scores(
    query: str, docs: Sequence[Dict[str, Any]], top_k: int
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Return docs with rerank scores. If reranker is unavailable, scores will be 0.0.
    """
    ranked = CrossEncoderReranker.rerank_with_scores(query, docs, top_k=top_k)
    out: List[Tuple[Dict[str, Any], float]] = []
    for doc, score in ranked:
        if isinstance(doc, dict):
            meta = doc.get("metadata") or {}
            meta["rerank_score"] = float(score)
            doc["metadata"] = meta
        out.append((doc, float(score)))
    return out


def rerank_score_stats(ranked: Sequence[Tuple[Dict[str, Any], float]]) -> Dict[str, Any]:
    scores = [float(s) for _, s in ranked]
    if not scores:
        return {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "p50": 0.0, "p80": 0.0}
    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    mean = sum(scores_sorted) / n

    def percentile(p: float) -> float:
        p = max(0.0, min(1.0, p))
        if n == 1:
            return scores_sorted[0]
        idx = int(round((n - 1) * p))
        return scores_sorted[idx]

    return {
        "count": n,
        "min": scores_sorted[0],
        "max": scores_sorted[-1],
        "mean": mean,
        "p50": percentile(0.50),
        "p80": percentile(0.80),
    }


def adaptive_rerank_threshold(
    ranked: Sequence[Tuple[Dict[str, Any], float]],
    cfg: RetrievalQualityConfig,
) -> float:
    """
    Choose a threshold based on the observed score distribution, not a fixed number.
    """
    stats = rerank_score_stats(ranked)
    if stats["count"] <= 0:
        return cfg.min_rerank_score
    # Keep docs above this percentile; also apply an optional floor.
    scores_sorted = sorted(float(s) for _, s in ranked)
    n = len(scores_sorted)
    idx = int(round((n - 1) * max(0.0, min(1.0, cfg.rerank_keep_percentile))))
    p = scores_sorted[idx]
    return max(cfg.min_rerank_score, float(p))


def filter_by_rerank_threshold(
    ranked: Sequence[Tuple[Dict[str, Any], float]],
    min_score: float,
    *,
    reranker_available: bool = True,
    min_keep: int = 0,
) -> List[Dict[str, Any]]:
    # ranked is already sorted high->low by CrossEncoderReranker.rerank_with_scores
    ordered_docs = [doc for doc, _ in ranked]

    # If the reranker isn't available, do NOT threshold-filter; just preserve the
    # vector store ordering (or whatever ordering the caller provided).
    if not reranker_available:
        return ordered_docs

    kept = [doc for doc, score in ranked if float(score) >= float(min_score)]

    # Avoid dropping everything due to score-scale quirks; keep at least min_keep
    # (caller can still gate on evidence sufficiency later).
    if min_keep and len(kept) < min_keep:
        return ordered_docs[:min_keep]

    return kept


def average_rerank_score(docs: Sequence[Dict[str, Any]]) -> float:
    scores: List[float] = []
    for d in docs:
        meta = d.get("metadata") or {}
        s = meta.get("rerank_score")
        if isinstance(s, (int, float)):
            scores.append(float(s))
    return (sum(scores) / len(scores)) if scores else 0.0


def assess_evidence_sufficiency(
    docs: Sequence[Dict[str, Any]],
    requested: int,
    cfg: RetrievalQualityConfig,
) -> Dict[str, Any]:
    """
    Decide if the corpus is strong enough to proceed to downstream agents.
    """
    unique_papers = count_unique_papers(docs)
    avg_score = average_rerank_score(docs)

    # IMPORTANT: Do not hard-fail based on unique_papers; report it as a flag.
    ok = (
        len(docs) >= min(cfg.min_results_after_filter, requested)
        and avg_score >= cfg.min_avg_rerank_score
    )

    flags: List[str] = []
    if unique_papers < requested:
        flags.append(f"unique_papers_below_requested:{unique_papers}<{requested}")
    if len(docs) < min(cfg.min_results_after_filter, requested):
        flags.append(f"results_count_below_min:{len(docs)}<{min(cfg.min_results_after_filter, requested)}")
    if avg_score < cfg.min_avg_rerank_score:
        flags.append(f"avg_rerank_score_below_min:{avg_score:.2f}<{cfg.min_avg_rerank_score:.2f}")

    return {
        "ok": ok,
        "unique_papers": unique_papers,
        "unique_papers_goal": requested,
        "meets_unique_papers_goal": unique_papers >= requested,
        "results_count": len(docs),
        "avg_rerank_score": avg_score,
        "requested": requested,
        "flags": flags,
        "thresholds": {
            "min_unique_papers": cfg.min_unique_papers,
            "min_results_after_filter": min(cfg.min_results_after_filter, requested),
            "min_avg_rerank_score": cfg.min_avg_rerank_score,
        },
    }


def build_insufficient_evidence_message(
    query: str,
    research_domain: str,
    assessment: Dict[str, Any],
    searched_sources: Optional[List[str]] = None,
) -> str:
    sources_part = ""
    if searched_sources:
        sources_part = f" Sources searched: {', '.join(searched_sources)}."

    return (
        "We could not find enough *relevant* academic evidence to proceed with thematic analysis for your query.\n\n"
        f"- Query: '{query}'\n"
        f"- Research domain: '{research_domain}'\n"
        f"- Relevant papers found: {assessment.get('unique_papers', 0)} (minimum required: {assessment.get('thresholds', {}).get('min_unique_papers')})\n"
        f"- Relevant results kept after filtering: {assessment.get('results_count', 0)}\n"
        f"- Average relevance score: {assessment.get('avg_rerank_score', 0.0):.2f}\n"
        f"{sources_part}\n\n"
        "Try one of these:\n"
        "- Make the query more specific (e.g., include 'on-chain governance', 'DAO voting', 'protocol upgrades', 'accountability', 'auditability').\n"
        "- Expand the year range.\n"
        "- Enable more sources (OpenAlex, arXiv, Europe PMC, CORE) and rerun.\n"
    )


