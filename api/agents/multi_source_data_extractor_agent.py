import asyncio
import os
import sys
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import pdfplumber
from io import BytesIO
import aiohttp
from api.services.extraction_logic import extract_paper_content

# Ensure local imports resolve when deployed serverlessly

# Robust import to work in both direct and package contexts
try:
    from utils.vector_store_manager import VectorStoreManager  # noqa: E402
except ImportError:  # pragma: no cover - fallback for pytest/package
    from api.utils.vector_store_manager import VectorStoreManager  # type: ignore

from .data_extractor_agent import DataExtractorAgent  # reuse CORE logic without modifying it


@dataclass
class MultiSourceExtractorConfig:
    max_results: int = 30
    per_source_limit: int = 20
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    language: Optional[str] = None
    research_domain: str = "General"
    sources: Optional[List[str]] = None  # ["core", "openalex", "europe_pmc", "arxiv"]
    enrich_with: Optional[List[str]] = None  # ["crossref", "unpaywall", "sem_scholar"]
    oa_only: bool = True
    auto_fallback: bool = True
    collection_name: str = "ResearchPaper"


@dataclass
class SourceStats:
    name: str
    fetched: int = 0
    errors: int = 0
    details: List[str] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)


class MultiSourceDataExtractorAgent:
    """
    Multi-source academic data extractor.

    - Discovery providers (free): CORE (existing), OpenAlex, Europe PMC, arXiv
    - Enrichment providers (free): Crossref, Unpaywall, Semantic Scholar

    This class is self-contained and does NOT modify existing agents.
    """

    def __init__(self, collection_name: str = "ResearchPaper", research_domain: str = "General") -> None:
        self.collection_name = collection_name
        self.research_domain = research_domain
        # Lazy-init vector store to avoid noisy logs if store=False
        self.vector_store_manager: Optional[VectorStoreManager] = None
        self._concurrency_limit = int(os.getenv("EXTRACTOR_CONCURRENCY", "8"))
        self._sem = asyncio.Semaphore(self._concurrency_limit)

    # Helper to reconstruct OpenAlex abstract text from inverted index
    @staticmethod
    def _reconstruct_openalex_abstract(abstract_field: Any) -> Optional[str]:
        if isinstance(abstract_field, str):
            return abstract_field
        inv = abstract_field
        if not isinstance(inv, dict) or not inv:
            return None
        try:
            max_pos = -1
            for _, positions in inv.items():
                for pos in positions:
                    if isinstance(pos, int) and pos > max_pos:
                        max_pos = pos
            if max_pos < 0:
                return None
            tokens: List[str] = [""] * (max_pos + 1)
            for word, positions in inv.items():
                for pos in positions:
                    if isinstance(pos, int) and 0 <= pos <= max_pos:
                        tokens[pos] = word
            text = " ".join(t for t in tokens if isinstance(t, str))
            return text.strip() or None
        except Exception:
            return None

    async def run(
        self,
        query: str,
        research_domain: str = "General",
        max_results: int = 30,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        language: Optional[str] = None,
        sources: Optional[List[str]] = None,
        enrich_with: Optional[List[str]] = None,
        per_source_limit: int = 20,
        oa_only: bool = True,
        auto_fallback: bool = True,
        store: bool = True,
        full_text: Optional[bool] = None,
        use_playwright_fallback: bool = False,
    ) -> Dict[str, Any]:

        started_at = datetime.now(timezone.utc).isoformat()

        config = MultiSourceExtractorConfig(
            max_results=max_results,
            per_source_limit=per_source_limit,
            year_from=year_from,
            year_to=year_to,
            language=language,
            research_domain=research_domain,
            sources=sources,
            enrich_with=enrich_with,
            oa_only=oa_only,
            auto_fallback=auto_fallback,
            collection_name=self.collection_name,
        )

        selected_sources = set((sources or ["openalex", "europe_pmc", "arxiv", "core"]))
        selected_enrichers = set((enrich_with or ["crossref", "unpaywall", "sem_scholar"]))

        discovery_stats: List[SourceStats] = []
        enrichment_stats: List[SourceStats] = []

        items: List[Dict[str, Any]] = []
        seen_dois: Set[str] = set()
        seen_hashes: Set[str] = set()

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            discovery_tasks: List[asyncio.Task] = []

            if "core" in selected_sources:
                discovery_tasks.append(asyncio.create_task(self._discover_core(query, config)))
            if "openalex" in selected_sources:
                discovery_tasks.append(asyncio.create_task(self._discover_openalex(session, query, config)))
            if "europe_pmc" in selected_sources:
                discovery_tasks.append(asyncio.create_task(self._discover_europe_pmc(session, query, config)))
            if "arxiv" in selected_sources:
                discovery_tasks.append(asyncio.create_task(self._discover_arxiv(session, query, config)))

            discovery_results = await asyncio.gather(*discovery_tasks, return_exceptions=True)

            for result in discovery_results:
                if isinstance(result, tuple):
                    src_name, docs, stats = result
                    discovery_stats.append(stats)
                    for d in docs:
                        doi = (d.get("doi") or "").lower().strip()
                        if doi:
                            if doi in seen_dois:
                                continue
                            seen_dois.add(doi)
                        else:
                            h = f"{(d.get('title') or '').lower()}::{d.get('year') or ''}"
                            if h in seen_hashes:
                                continue
                            seen_hashes.add(h)
                        items.append(d)
                        if len(items) >= config.max_results:
                            break
                elif isinstance(result, Exception):
                    discovery_stats.append(SourceStats(name="unknown", fetched=0, errors=1, details=[str(result)]))

        # Telemetry: discovery summary with detailed paper info
        try:
            by_src = {s.name: {"fetched": s.fetched, "errors": s.errors} for s in discovery_stats}
            print(
                "[EXTRACTOR] Discovery summary "
                f"query='{query}' domain='{research_domain}' "
                f"sources={sorted(list(selected_sources))} "
                f"per_source_limit={config.per_source_limit} max_results={config.max_results} "
                f"year_from={config.year_from} year_to={config.year_to} "
                f"unique_items={len(items)} stats={by_src}"
            )
            
            # Log detailed paper information to verify relevance
            print(f"[EXTRACTOR] 📄 Discovered {len(items)} papers:")
            for idx, item in enumerate(items[:10], 1):  # Show first 10 papers
                title = item.get("title", "No title")[:100]
                source = item.get("source", "unknown")
                year = item.get("year", "N/A")
                doi = item.get("doi", "")[:50] if item.get("doi") else "No DOI"
                abstract = (item.get("abstract") or "")[:150] if item.get("abstract") else "No abstract"
                pdf_url = self._select_pdf_url(item)
                has_pdf = "✅ PDF" if pdf_url else "❌ No PDF"
                print(
                    f"[EXTRACTOR]   {idx}. [{source}] {title} ({year}) | {has_pdf}\n"
                    f"              DOI: {doi}\n"
                    f"              Abstract: {abstract}..."
                )
            if len(items) > 10:
                print(f"[EXTRACTOR]   ... and {len(items) - 10} more papers")
        except Exception as e:
            print(f"[EXTRACTOR] Error logging discovery details: {e}")

        if not items and config.auto_fallback:
            retry_cfg = MultiSourceExtractorConfig(
                **{**config.__dict__, "year_from": None, "year_to": None, "oa_only": False}
            )
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                retry_tasks = []
                if "openalex" in selected_sources:
                    retry_tasks.append(asyncio.create_task(self._discover_openalex(session, query, retry_cfg)))
                if "europe_pmc" in selected_sources:
                    retry_tasks.append(asyncio.create_task(self._discover_europe_pmc(session, query, retry_cfg)))
                if "arxiv" in selected_sources:
                    retry_tasks.append(asyncio.create_task(self._discover_arxiv(session, query, retry_cfg)))
                if "core" in selected_sources:
                    retry_tasks.append(asyncio.create_task(self._discover_core(query, retry_cfg)))

                retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
                for result in retry_results:
                    if isinstance(result, tuple):
                        _, docs, stats = result
                        discovery_stats.append(stats)
                        for d in docs:
                            doi = (d.get("doi") or "").lower().strip()
                            if doi:
                                if doi in seen_dois:
                                    continue
                                seen_dois.add(doi)
                            else:
                                h = f"{(d.get('title') or '').lower()}::{d.get('year') or ''}"
                                if h in seen_hashes:
                                    continue
                                seen_hashes.add(h)
                            items.append(d)
                            if len(items) >= config.max_results:
                                break

        if items and selected_enrichers:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                if "crossref" in selected_enrichers:
                    enrichment_stats.append(await self._enrich_crossref(session, items))
                if "unpaywall" in selected_enrichers:
                    enrichment_stats.append(await self._enrich_unpaywall(session, items))
                if "sem_scholar" in selected_enrichers:
                    enrichment_stats.append(await self._enrich_semantic_scholar(session, items))

        # CRITICAL DEBUG: Force flush and log before storage section
        import sys
        sys.stdout.flush()
        print(f"[EXTRACTOR] 🔍🔍🔍 REACHED STORAGE SECTION 🔍🔍🔍", flush=True)
        print(f"[EXTRACTOR] 🔍 Storage decision: items={len(items)} store={store} (type={type(store)}, bool(store)={bool(store)})", flush=True)
        print(f"[EXTRACTOR] 🔍 Condition check: items={bool(items)} store={bool(store)} items_and_store={bool(items and store)}", flush=True)
        
        stored = 0
        storage_telemetry: Dict[str, Any] = {
            "store_enabled": bool(store),
            "docs_considered": len(items),
            "docs_with_pdf_url": 0,
            "pdf_download_success": 0,
            "pdf_download_failed": 0,
            "pdf_extract_success": 0,
            "pdf_extract_failed": 0,
            "chunks_generated": 0,
            "chunks_stored": 0,
            "skipped_no_pdf_url": 0,
        }
        
        if items and store:
            print(f"[EXTRACTOR] 💾 Storage enabled. Initializing vector store for domain='{research_domain}' collection='{self.collection_name}'")
            if self.vector_store_manager is None:
                self.vector_store_manager = VectorStoreManager(
                    collection_name=self.collection_name,
                    research_domain=self.research_domain,
                )
                print(f"[EXTRACTOR] ✅ VectorStoreManager initialized with research_domain='{self.research_domain}'")

            for d in items:
                d.setdefault("research_domain", research_domain)

            # ONLY store extracted full-text PDFs
            print(f"[EXTRACTOR] 🔄 Starting PDF extraction and storage for {len(items)} papers...")
            stored, storage_telemetry = await self._extract_and_store_full_text(
                items, research_domain, use_playwright_fallback
            )
            print(f"[EXTRACTOR] ✅ Storage complete: {stored} chunks stored")
        else:
            if items and not store:
                print(
                    "[EXTRACTOR] Store disabled (store=false) — discovery ran but nothing will be written to Weaviate. "
                    f"unique_items={len(items)}"
                )

        # Telemetry: storage summary
        try:
            print(f"[EXTRACTOR] Storage summary: {storage_telemetry}")
        except Exception:
            pass

        return {
            "success": True,
            "data": {
                "query": query,
                "research_domain": research_domain,
                "documents": items[: config.max_results],
                "total_found": len(items),
                "stored": stored,
                "source_stats": [s.__dict__ for s in discovery_stats],
                "enrichment_stats": [s.__dict__ for s in enrichment_stats],
                "storage_telemetry": storage_telemetry,
                "started_at": started_at,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------- Discovery providers -----------------------------

    async def _discover_core(self, query: str, cfg: MultiSourceExtractorConfig):
        name = "core"
        stats = SourceStats(name=name)
        try:
            agent = DataExtractorAgent()
            # Respect per_source_limit to avoid long scrolls
            max_results = min(cfg.per_source_limit, cfg.max_results)
            papers = await agent.fetch_papers(query, max_results=max_results, year_from=cfg.year_from, year_to=cfg.year_to)
            results: List[Dict[str, Any]] = []
            for p in papers or []:
                # Robustly build authors string (handle list of dicts or strings)
                raw_authors = p.get("authors")
                authors_str = ""
                if isinstance(raw_authors, str):
                    authors_str = raw_authors
                elif isinstance(raw_authors, list):
                    names: List[str] = []
                    for a in raw_authors:
                        if isinstance(a, dict):
                            n = a.get("name") or a.get("fullName") or a.get("full_name") or a.get("display_name") or ""
                            if n:
                                names.append(str(n))
                        else:
                            names.append(str(a))
                    authors_str = ", ".join([n for n in names if n])

                results.append({
                    "title": p.get("title", "Unknown Title"),
                    "authors": authors_str,
                    "year": p.get("year"),
                    "abstract": p.get("abstract", ""),
                    "doi": (p.get("doi") or "").lower().strip(),
                    "source": name,
                    "url": p.get("downloadUrl") or p.get("pdfUrl") or p.get("url") or None,
                })
            stats.fetched = len(results)
            return name, results, stats
        except Exception as e:
            stats.errors += 1
            stats.details.append(str(e))
            return name, [], stats

    async def _discover_openalex(self, session: aiohttp.ClientSession, query: str, cfg: MultiSourceExtractorConfig):
        name = "openalex"
        stats = SourceStats(name=name)
        try:
            params = {
                "search": query,
                "per_page": min(cfg.per_source_limit, cfg.max_results),
            }
            if cfg.year_from or cfg.year_to:
                yfrom = cfg.year_from or 1900
                yto = cfg.year_to or datetime.now().year
                params["from_publication_date"] = f"{yfrom}-01-01"
                params["to_publication_date"] = f"{yto}-12-31"
            if cfg.language:
                params["language"] = cfg.language

            # OpenAlex prefers a contact email via mailto parameter and UA
            mailto = os.getenv("OPENALEX_MAILTO") or os.getenv("UNPAYWALL_EMAIL") or ""
            if mailto:
                params["mailto"] = mailto

            url = "https://api.openalex.org/works"
            print(f"[DISCOVERY][OpenAlex] GET {url} params={params}")
            async with self._sem:
                ua = f"Waga-Academy-Extractor/1.0 ({mailto})" if mailto else "Waga-Academy-Extractor/1.0"
                async with session.get(url, params=params, headers={"User-Agent": ua, "Accept": "application/json"}) as resp:
                    if resp.status != 200:
                        stats.errors += 1
                        reason = f"HTTP {resp.status}"
                        if resp.status == 403 and not mailto:
                            reason += " (tip: set OPENALEX_MAILTO env to reduce blocks)"
                        stats.details.append(reason)
                        return name, [], stats
                    data = await resp.json()

            results = []
            for w in data.get("results", []) or []:
                doi = (w.get("doi") or "").replace("https://doi.org/", "").lower().strip()
                title = (w.get("display_name") or "").strip()
                year = None
                try:
                    if w.get("publication_year"):
                        year = int(w.get("publication_year"))
                except Exception:
                    year = None
                authors = ", ".join([a.get("author", {}).get("display_name", "") for a in (w.get("authorships") or [])])
                abstract_text = self._reconstruct_openalex_abstract(
                    w.get("abstract") or w.get("abstract_inverted_index")
                )
                results.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": abstract_text,
                    "doi": doi,
                    "source": name,
                    "url": w.get("primary_location", {}).get("landing_page_url") or w.get("id"),
                })
            stats.fetched = len(results)
            if results:
                samples = ", ".join([r.get("title","")[:100] for r in results[:2]])
                print(f"[DISCOVERY][OpenAlex] sample titles: {samples}")
            return name, results, stats
        except Exception as e:
            stats.errors += 1
            stats.details.append(str(e))
            return name, [], stats

    async def _discover_europe_pmc(self, session: aiohttp.ClientSession, query: str, cfg: MultiSourceExtractorConfig):
        name = "europe_pmc"
        stats = SourceStats(name=name)
        try:
            # Europe PMC REST
            params = {
                "query": query,
                "pageSize": str(min(cfg.per_source_limit, cfg.max_results)),
                "format": "json",
            }
            if cfg.year_from or cfg.year_to:
                yfrom = cfg.year_from or 1900
                yto = cfg.year_to or datetime.now().year
                params["query"] += f" PUB_YEAR:[{yfrom} TO {yto}]"
            if cfg.oa_only:
                params["query"] += " OPEN_ACCESS:y"

            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            print(f"[DISCOVERY][EuropePMC] GET {url} params={{'query': params['query'], 'pageSize': params['pageSize']}}")
            async with self._sem:
                async with session.get(url, params=params, headers={"User-Agent": "Waga-Academy-Extractor/1.0"}) as resp:
                    if resp.status != 200:
                        stats.errors += 1
                        stats.details.append(f"HTTP {resp.status}")
                        return name, [], stats
                    data = await resp.json()

            results = []
            for r in (data.get("resultList", {}) or {}).get("result", []) or []:
                doi = (r.get("doi") or "").lower().strip()
                title = (r.get("title") or "").strip()
                authors = r.get("authorString") or ""
                year = None
                try:
                    if r.get("pubYear"):
                        year = int(r.get("pubYear"))
                except Exception:
                    year = None
                results.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": r.get("abstractText"),
                    "doi": doi,
                    "source": name,
                    "url": r.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url") if r.get("fullTextUrlList") else r.get("pmcid") or r.get("id"),
                })
            stats.fetched = len(results)
            if results:
                samples = ", ".join([r.get("title","")[:100] for r in results[:2]])
                print(f"[DISCOVERY][EuropePMC] sample titles: {samples}")
            return name, results, stats
        except Exception as e:
            stats.errors += 1
            stats.details.append(str(e))
            return name, [], stats

    async def _discover_arxiv(self, session: aiohttp.ClientSession, query: str, cfg: MultiSourceExtractorConfig):
        name = "arxiv"
        stats = SourceStats(name=name)
        try:
            max_results = min(cfg.per_source_limit, cfg.max_results)
            url = "https://export.arxiv.org/api/query"
            params = {"search_query": f"all:{query}", "start": 0, "max_results": max_results}
            print(f"[DISCOVERY][arXiv] GET {url} params={params}")

            async with self._sem:
                async with session.get(url, params=params, headers={"User-Agent": "Waga-Academy-Extractor/1.0"}) as resp:
                    if resp.status != 200:
                        stats.errors += 1
                        stats.details.append(f"HTTP {resp.status}")
                        return name, [], stats
                    text = await resp.text()

            results: List[Dict[str, Any]] = []

            for chunk in text.split("<entry>")[1:]:
                title = self._extract_between(chunk, "<title>", "</title>") or ""
                summary = self._extract_between(chunk, "<summary>", "</summary>") or ""

                # ✅ Extract arXiv ID
                arxiv_id = None
                entry_id = self._extract_between(chunk, "<id>", "</id>")

                if entry_id and "/abs/" in entry_id:
                    arxiv_id = entry_id.split("/abs/")[-1]

                year = None
                published = self._extract_between(chunk, "<published>", "</published>")
                if published:
                    try:
                        year = int(published[:4])
                    except Exception:
                        pass

                content = summary.strip()  # fallback

                # ✅ Download & extract PDF content
                if arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    try:
                        async with self._sem:
                            async with session.get(pdf_url) as pdf_resp:
                                if pdf_resp.status == 200:
                                    pdf_bytes = await pdf_resp.read()
                                    content = self._extract_pdf_text(pdf_bytes)  # cap size
                    except Exception as e:
                        stats.details.append(f"PDF extract failed for {arxiv_id}: {e}")

                # Set both abstract URL and PDF URL for arXiv papers
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None
                results.append({
                    "title": title.strip(),
                    "authors": "",
                    "year": year,
                    "content": content,   # ✅ FULL TEXT HERE (pre-extracted)
                    "abstract": summary.strip(),
                    "source": name,
                    "paper_id": arxiv_id,
                    "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
                    "links": {"oa_pdf": pdf_url} if pdf_url else {},  # Set PDF URL so storage can find it
                })

            stats.fetched = len(results)
            return name, results, stats

        except Exception as e:
            stats.errors += 1
            stats.details.append(str(e))
            return name, [], stats
    
 

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        texts = []
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texts.append(t)
        return "\n".join(texts)

    # ----------------------------- Enrichment providers -----------------------------

    async def _enrich_crossref(self, session: aiohttp.ClientSession, items: List[Dict[str, Any]]) -> SourceStats:
        stats = SourceStats(name="crossref")
        base = "https://api.crossref.org/works/"
        tasks = []

        for doc in items:
            doi = (doc.get("doi") or "").strip()
            if doi:
                tasks.append(self._throttled_get(
                    session,
                    f"{base}{doi}",
                    headers={"User-Agent": "Waga-Academy-Extractor/1.0"}
                ))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for resp in responses:
            if not isinstance(resp, dict) or resp.get("status") != 200:
                stats.errors += 1
                continue

            message = (resp.get("json") or {}).get("message", {})
            doi = (message.get("DOI") or "").lower().strip()

            for d in items:
                if (d.get("doi") or "").lower().strip() != doi:
                    continue

                d.setdefault("metadata", {}).update({
                    "publisher": message.get("publisher"),
                    "journal": (message.get("container-title") or [None])[0],
                })

                pdf_url = d.get("links", {}).get("oa_pdf")
                if pdf_url:
                    extraction = await extract_paper_content(pdf_url, d.get("paper_id"))
                    if extraction["status"] == "success":
                        d["full_text"] = extraction["content"]

                        chunks = self._simple_chunk(
                            extraction["content"],
                            chunk_size=2000,
                            overlap=200
                        )
                        meta = [{
                            "paper_id": d.get("paper_id"),
                            "source": "crossref",
                            "title": d.get("title"),
                            "doi": d.get("doi"),
                            "year": d.get("year"),
                            "chunk_index": i,
                        } for i in range(len(chunks))]

                        self.vector_store_manager.add_chunks(chunks, meta)

                stats.fetched += 1
                break

        return stats

    async def _enrich_unpaywall(self, session: aiohttp.ClientSession, items: List[Dict[str, Any]]) -> SourceStats:
        """
        Enrich items with Unpaywall metadata + PDF URLs.

        IMPORTANT: This function SHOULD NOT write to the vector store directly.
        All chunking/embedding/storage happens later in `_extract_and_store_full_text`,
        after `self.vector_store_manager` has been initialized for the run.
        """
        stats = SourceStats(name="unpaywall")
        email = os.getenv("UNPAYWALL_EMAIL", "opensource@waga.local")
        tasks = []

        for doc in items:
            doi = (doc.get("doi") or "").strip()
            if doi:
                tasks.append(self._throttled_get(
                    session,
                    f"https://api.unpaywall.org/v2/{doi}?email={email}"
                ))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for resp in responses:
            if not isinstance(resp, dict) or resp.get("status") != 200:
                stats.errors += 1
                continue

            data = resp["json"]
            doi = (data.get("doi") or "").lower().strip()
            best = data.get("best_oa_location") or {}
            pdf_url = best.get("url_for_pdf") or best.get("url")

            for d in items:
                if (d.get("doi") or "").lower().strip() != doi:
                    continue

                d.setdefault("metadata", {})["oa_status"] = data.get("oa_status")

                # Only attach the PDF URL here; the main storage path will take care
                # of downloading, chunking, and storing into Weaviate.
                if pdf_url:
                    d.setdefault("links", {})["oa_pdf"] = pdf_url

                stats.fetched += 1
                break

        return stats

    async def _enrich_semantic_scholar(self, session: aiohttp.ClientSession, items: List[Dict[str, Any]]) -> SourceStats:
        stats = SourceStats(name="sem_scholar")
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        headers = {"User-Agent": "Waga-Academy-Extractor/1.0"}
        if api_key:
            headers["x-api-key"] = api_key

        base = "https://api.semanticscholar.org/graph/v1/paper/"
        fields = "citationCount,influentialCitationCount,fieldsOfStudy"
        tasks = []

        for doc in items:
            doi = (doc.get("doi") or "").strip()
            if doi:
                tasks.append(self._throttled_get(
                    session,
                    f"{base}DOI:{doi}?fields={fields}",
                    headers=headers
                ))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for resp in responses:
            if not isinstance(resp, dict) or resp.get("status") != 200:
                stats.errors += 1
                continue

            data = resp["json"]
            doi = (data.get("externalIds", {}).get("DOI") or "").lower().strip()

            for d in items:
                if (d.get("doi") or "").lower().strip() != doi:
                    continue

                d.setdefault("signals", {}).update({
                    "citationCount": data.get("citationCount"),
                    "influentialCitationCount": data.get("influentialCitationCount"),
                    "fieldsOfStudy": data.get("fieldsOfStudy"),
                })

                pdf_url = d.get("links", {}).get("oa_pdf")
                if pdf_url:
                    extraction = await extract_paper_content(pdf_url, d.get("paper_id"))
                    if extraction["status"] == "success":
                        d["full_text"] = extraction["content"]

                        chunks = self._simple_chunk(
                            extraction["content"],
                            chunk_size=2000,
                            overlap=200
                        )
                        meta = [{
                            "paper_id": d.get("paper_id"),
                            "source": "semantic_scholar",
                            "title": d.get("title"),
                            "doi": d.get("doi"),
                            "year": d.get("year"),
                            "chunk_index": i,
                        } for i in range(len(chunks))]

                        self.vector_store_manager.add_chunks(chunks, meta)

                stats.fetched += 1
                break

        return stats

    # ----------------------------- Helpers -----------------------------

    async def _throttled_get(self, session: aiohttp.ClientSession, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET with concurrency control and simple retry/backoff."""
        max_attempts = 3
        backoff = 0.8
        for attempt in range(max_attempts):
            try:
                async with self._sem:
                    async with session.get(url, headers=headers) as resp:
                        status = resp.status
                        if status == 200:
                            try:
                                return {"status": status, "json": await resp.json()}
                            except Exception:
                                return {"status": status, "text": await resp.text()}
                        if status in (429, 500, 502, 503, 504):
                            await asyncio.sleep((backoff ** attempt) + 0.2 * attempt)
                            continue
                        return {"status": status}
            except asyncio.TimeoutError:
                await asyncio.sleep((backoff ** attempt) + 0.2 * attempt)
            except Exception as _:
                await asyncio.sleep((backoff ** attempt) + 0.2 * attempt)
        return {"status": 599}

    @staticmethod
    def _extract_between(text: str, start_tag: str, end_tag: str) -> Optional[str]:
        try:
            i = text.index(start_tag) + len(start_tag)
            j = text.index(end_tag, i)
            return text[i:j]
        except Exception:
            return None

    @staticmethod
    def _extract_attr(tag_line: str, attr: str) -> Optional[str]:
        try:
            # naive parse href="..."
            key = f"{attr}="
            if key not in tag_line:
                return None
            part = tag_line.split(key, 1)[1]
            quote = '"' if '"' in part else "'"
            start = part.index(quote) + 1
            end = part.index(quote, start)
            return part[start:end]
        except Exception:
            return None

    async def _resolve_pdf_with_playwright(self, url: str) -> Optional[str]:
        if not url:
            return None
        try:
            from playwright.async_api import async_playwright  # type: ignore
        except Exception:
            print("[PLAYWRIGHT] Not installed or unavailable; skipping browser fallback")
            return None
        try:
            async with self._sem:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context()
                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    # Try meta tag first
                    meta = page.locator('meta[name="citation_pdf_url"]')
                    if await meta.count():
                        href = await meta.first.get_attribute("content")
                        if href and href.lower().endswith(".pdf"):
                            await browser.close()
                            return href
                    # Try obvious anchors
                    link = page.locator('a[href$=".pdf"]')
                    if await link.count():
                        href = await link.first.get_attribute("href")
                        await browser.close()
                        return href
                    # Try button that opens PDF in new tab
                    # Fallback: look for any link containing 'pdf'
                    any_pdf = page.locator('a:has-text("PDF")')
                    if await any_pdf.count():
                        href = await any_pdf.first.get_attribute("href")
                        await browser.close()
                        return href
                    await browser.close()
            return None
        except Exception as e:
            print(f"[PLAYWRIGHT] Failed to resolve PDF from {url}: {e}")
            return None

    async def _extract_abstract_with_playwright(self, url: str) -> Optional[str]:
        if not url:
            return None
        try:
            from playwright.async_api import async_playwright  # type: ignore
        except Exception:
            return None
        try:
            async with self._sem:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context()
                    page = await context.new_page()
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    # Common meta
                    sel = 'meta[name="citation_abstract"], meta[name="dc.description"], meta[name="description"]'
                    loc = page.locator(sel)
                    if await loc.count():
                        content = await loc.first.get_attribute("content")
                        await browser.close()
                        return content
                    # Try visible abstract blocks
                    text = await page.locator('section:has-text("Abstract")').first.inner_text()
                    if text:
                        await browser.close()
                        return text
                    await browser.close()
            return None
        except Exception:
            return None

    def _select_pdf_url(self, d: Dict[str, Any]) -> Optional[str]:
        # Prefer Unpaywall OA link
        oa_pdf = (d.get("links") or {}).get("oa_pdf")
        if oa_pdf and ".pdf" in oa_pdf.lower():
            return oa_pdf
        # arXiv: convert abs URL to PDF URL, or use direct PDF URL
        url = d.get("url") or ""
        if "arxiv.org/abs/" in url:
            arxiv_id = url.split("/abs/")[-1].split("?")[0].split("#")[0]
            return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        if "arxiv.org/pdf" in url:
            return url
        # CORE downloadUrl (may be direct pdf)
        if d.get("source") == "core" and url:
            return url
        return None

    async def _download_and_extract_pdf_text(self, session: aiohttp.ClientSession, pdf_url: str) -> Optional[str]:
        try:
            async with self._sem:
                async with session.get(pdf_url, headers={"User-Agent": "Waga-Academy-Extractor/1.0"}) as resp:
                    if resp.status != 200:
                        return None
                    ctype = resp.headers.get("Content-Type", "").lower()
                    if "pdf" not in ctype and not pdf_url.lower().endswith(".pdf"):
                        return None
                    raw = await resp.read()
            from io import BytesIO
            bio = BytesIO(raw)
            import PyPDF2
            reader = PyPDF2.PdfReader(bio)
            pages = []
            for p in reader.pages:
                try:
                    pages.append(p.extract_text() or "")
                except Exception:
                    pages.append("")
            text = "\n\n".join([t.strip() for t in pages if t and t.strip()])
            return text.strip() or None
        except Exception as e:
            print(f"[PDF] Failed to extract PDF {pdf_url}: {e}")
            return None

    def _simple_chunk(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        chunks: List[str] = []
        if not text:
            return chunks
        start = 0
        n = len(text)
        while start < n:
            end = min(n, start + chunk_size)
            chunks.append(text[start:end])
            if end == n:
                break
            start = max(end - overlap, start + 1)
        return chunks 

    async def _extract_and_store_full_text(
        self,
        items: List[Dict[str, Any]],
        research_domain: str,
        use_playwright_fallback: bool,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Extract full text PDFs (when available) and store chunks in Weaviate.
        Returns: (chunks_stored_count, telemetry)
        """
        telemetry: Dict[str, Any] = {
            "store_enabled": True,
            "docs_considered": len(items),
            "docs_with_pdf_url": 0,
            "pdf_download_success": 0,
            "pdf_download_failed": 0,
            "pdf_extract_success": 0,
            "pdf_extract_failed": 0,
            "chunks_generated": 0,
            "chunks_stored": 0,
            "skipped_no_pdf_url": 0,
        }

        all_chunks: List[str] = []
        all_metadata: List[Dict[str, Any]] = []

        print(f"[EXTRACTOR][STORAGE] Processing {len(items)} papers for domain='{research_domain}'")
        
        for idx, doc in enumerate(items, 1):
            title = doc.get("title", "Unknown")[:80]
            source = doc.get("source", "unknown")
            pdf_url = self._select_pdf_url(doc)
            
            if use_playwright_fallback and not pdf_url:
                print(f"[EXTRACTOR][STORAGE] {idx}/{len(items)} [{source}] '{title}' - No PDF URL, trying Playwright fallback...")
                resolved = await self._resolve_pdf_with_playwright(doc.get("url") or "")
                if resolved:
                    pdf_url = resolved
                    doc.setdefault("links", {})["oa_pdf"] = pdf_url
                    print(f"[EXTRACTOR][STORAGE] {idx}/{len(items)} [{source}] '{title}' - ✅ Playwright resolved PDF: {pdf_url[:80]}...")
                else:
                    print(f"[EXTRACTOR][STORAGE] {idx}/{len(items)} [{source}] '{title}' - ❌ Playwright failed to resolve PDF")

            if not pdf_url:
                telemetry["skipped_no_pdf_url"] += 1
                print(f"[EXTRACTOR][STORAGE] {idx}/{len(items)} [{source}] '{title}' - ⏭️  SKIPPED (no PDF URL)")
                continue

            telemetry["docs_with_pdf_url"] += 1
            print(f"[EXTRACTOR][STORAGE] {idx}/{len(items)} [{source}] '{title}' - 📥 Downloading PDF from {pdf_url[:80]}...")
            
            extraction = await extract_paper_content(
                pdf_url=pdf_url,
                paper_id=doc.get("paper_id", "")
            )

            if extraction.get("status") != "success":
                telemetry["pdf_download_failed"] += 1
                telemetry["pdf_extract_failed"] += 1
                error = extraction.get("error", "Unknown error")
                print(f"[EXTRACTOR][STORAGE] {idx}/{len(items)} [{source}] '{title}' - ❌ PDF extraction FAILED: {error}")
                continue

            telemetry["pdf_download_success"] += 1
            telemetry["pdf_extract_success"] += 1

            text = extraction["content"]
            word_count = len(text.split())
            chunks = self._simple_chunk(text, chunk_size=2000, overlap=200)
            telemetry["chunks_generated"] += len(chunks)
            
            # Show sample content to verify relevance
            sample_text = text[:200].replace("\n", " ") if text else ""
            print(
                f"[EXTRACTOR][STORAGE] {idx}/{len(items)} [{source}] '{title}' - ✅ PDF extracted: {word_count} words, {len(chunks)} chunks\n"
                f"              Sample: {sample_text}..."
            )

            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadata.append({
                    "title": doc.get("title", ""),
                    "authors": doc.get("authors", ""),
                    "year": doc.get("year") or 0,
                    "doi": doc.get("doi", ""),
                    "source": doc.get("source", ""),
                    "paper_id": doc.get("paper_id", ""),
                    "research_domain": research_domain,
                    "chunk_index": i,
                })

        if all_chunks:
            try:
                assert self.vector_store_manager is not None
                print(f"[EXTRACTOR][STORAGE] 📤 Storing {len(all_chunks)} chunks to Weaviate (domain='{research_domain}')...")
                
                # Log sample metadata to verify research_domain
                if all_metadata:
                    sample_meta = all_metadata[0]
                    print(
                        f"[EXTRACTOR][STORAGE] Sample metadata: "
                        f"title='{sample_meta.get('title', '')[:60]}...' "
                        f"domain='{sample_meta.get('research_domain')}' "
                        f"source='{sample_meta.get('source')}' "
                        f"year={sample_meta.get('year')}"
                    )
                
                self.vector_store_manager.add_chunks(all_chunks, all_metadata)
                telemetry["chunks_stored"] = len(all_chunks)
                print(f"[EXTRACTOR][STORAGE] ✅ Successfully stored {len(all_chunks)} chunks to Weaviate")
            except Exception as e:
                print(f"[EXTRACTOR][STORAGE] ❌ Failed to store chunks: {e}")
                import traceback
                print(f"[EXTRACTOR][STORAGE] Traceback: {traceback.format_exc()}")
                telemetry["chunks_stored"] = 0
                return 0, telemetry
        else:
            print(f"[EXTRACTOR][STORAGE] ⚠️  No chunks to store (all PDFs failed or had no PDF URLs)")

        return int(telemetry["chunks_stored"]), telemetry