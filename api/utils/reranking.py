from typing import Any, List, Sequence, Optional
import math
import os


class CrossEncoderReranker:
    """Lightweight cross-encoder reranker wrapper.
    - Removes Flask jsonify usage
    - Caches the model
    - Handles different document shapes (dict or object with page_content)
    """

    _model: Optional[Any] = None
    _unavailable_reason: Optional[str] = None

    @classmethod
    def _get_model(cls) -> Optional[Any]:
        if cls._model is None:
            # Skip loading on low-memory hosts (e.g. Render free tier 512MB)
            if os.environ.get("DISABLE_RERANKER", "").lower() in ("1", "true", "yes"):
                cls._unavailable_reason = "Reranker disabled via DISABLE_RERANKER (low-memory mode)"
                return None
            try:
                from sentence_transformers import CrossEncoder  # lazy import
                cls._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                cls._unavailable_reason = None
            except Exception:
                # sentence-transformers (and torch) not available; disable reranking
                cls._model = None
                # Best-effort to preserve a useful reason (do not raise at import time)
                try:
                    import sys
                    cls._unavailable_reason = (
                        "Cross-encoder reranker unavailable. This usually means `sentence-transformers` "
                        "and/or `torch` is not installed (or no compatible wheel for your Python). "
                        f"Python={sys.version.split()[0]}"
                    )
                except Exception:
                    cls._unavailable_reason = "Cross-encoder reranker unavailable (missing deps)."
        return cls._model

    @classmethod
    def is_available(cls) -> bool:
        """
        Returns True if the cross-encoder model is available in this environment.
        Note: this may attempt a lazy import + model init the first time it's called.
        """
        return cls._get_model() is not None

    @classmethod
    def availability_info(cls) -> dict:
        """
        Returns a small diagnostic payload explaining whether the reranker is usable.
        """
        import sys
        available = cls.is_available()
        return {
            "available": bool(available),
            "python": sys.version.split()[0],
            "reason": None if available else (cls._unavailable_reason or "unavailable"),
            "model": "cross-encoder/ms-marco-MiniLM-L-6-v2" if available else None,
        }

    @staticmethod
    def _maybe_normalize_scores(raw_scores: Sequence[float]) -> List[float]:
        """
        Normalize cross-encoder scores to [0, 1] if they appear to be logits / unbounded.
        Heuristic: if any score is outside [0, 1], apply a sigmoid.
        """
        if not raw_scores:
            return []
        needs_sigmoid = any((s < 0.0 or s > 1.0) for s in raw_scores)
        if not needs_sigmoid:
            return [float(s) for s in raw_scores]

        out: List[float] = []
        for s in raw_scores:
            # numerically stable-ish sigmoid
            s = float(s)
            if s >= 0:
                z = math.exp(-s) if s < 60 else 0.0
                out.append(1.0 / (1.0 + z))
            else:
                z = math.exp(s) if s > -60 else 0.0
                out.append(z / (1.0 + z))
        return out

    @staticmethod
    def _extract_text(doc: Any) -> str:
        # Support dicts and objects
        if isinstance(doc, dict):
            return (
                doc.get("content")
                or doc.get("text")
                or doc.get("page_content")
                or ""
            )
        return (
            getattr(doc, "page_content", None)
            or getattr(doc, "content", None)
            or ""
        )

    @classmethod
    def rerank(cls, query: str, retrieved_documents: Sequence[Any], top_k: int = 15) -> List[Any]:
        try:
            if not retrieved_documents:
                return []

            model = cls._get_model()
            # Fallback: if model is unavailable, return original order (trimmed)
            if model is None:
                return list(retrieved_documents)[:top_k]

            pairs = [[query, cls._extract_text(doc)] for doc in retrieved_documents]
            # If all texts are empty, just return original order
            if all(not p[1] for p in pairs):
                return list(retrieved_documents)[:top_k]

            scores = model.predict(pairs)
            # Sort by score descending without numpy
            norm_scores = cls._maybe_normalize_scores([float(s) for s in scores])
            indexed_scores = [(idx, float(score)) for idx, score in enumerate(norm_scores)]
            indexed_scores.sort(key=lambda x: x[1], reverse=True)
            top_indices = [idx for idx, _ in indexed_scores[: min(top_k, len(retrieved_documents))]]
            return [retrieved_documents[i] for i in top_indices]
        except Exception:
            # On any failure, return the original (unreranked) list trimmed to top_k
            return list(retrieved_documents)[:top_k]

    @classmethod
    def rerank_with_scores(
        cls, query: str, retrieved_documents: Sequence[Any], top_k: int = 15
    ) -> List[tuple[Any, float]]:
        try:
            if not retrieved_documents:
                return []

            model = cls._get_model()
            if model is None:
                return [(doc, 0.0) for doc in list(retrieved_documents)[:top_k]]

            pairs = [[query, cls._extract_text(doc)] for doc in retrieved_documents]
            if all(not p[1] for p in pairs):
                return [(doc, 0.0) for doc in list(retrieved_documents)[:top_k]]

            scores = model.predict(pairs)
            norm_scores = cls._maybe_normalize_scores([float(s) for s in scores])
            indexed_scores = [(idx, float(score)) for idx, score in enumerate(norm_scores)]
            indexed_scores.sort(key=lambda x: x[1], reverse=True)
            top = indexed_scores[: min(top_k, len(retrieved_documents))]
            return [(retrieved_documents[idx], score) for idx, score in top]
        except Exception:
            return [(doc, 0.0) for doc in list(retrieved_documents)[:top_k]]