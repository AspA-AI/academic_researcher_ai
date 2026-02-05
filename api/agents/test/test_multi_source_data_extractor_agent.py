import sys, os
# Add repo root so `api.*` imports work

import asyncio
import os as _os
import pytest

from api.agents.multi_source_data_extractor_agent import MultiSourceDataExtractorAgent


@pytest.mark.asyncio
async def test_multi_source_extractor_auto_mode(capfd):
    agent = MultiSourceDataExtractorAgent(collection_name="ResearchPaper", research_domain="General")

    # Ensure Unpaywall email to avoid 403/401
    _os.environ.setdefault("UNPAYWALL_EMAIL", "opensource@waga.local")

    res = await agent.run(
        query="blockchain governance",
        research_domain="Technology",
        max_results=4,
        per_source_limit=2,
        year_from=2023,
        year_to=2025,
        oa_only=True,
        auto_fallback=True,
        store=False,
    )

    assert res.get("success") is True
    data = res.get("data") or {}

    # Print diagnostics for human assessment
    print("\n===== MULTI-SOURCE EXTRACTOR DIAGNOSTICS =====")
    print("Query:", data.get("query"))
    print("Found:", data.get("total_found"))

    docs = data.get("documents") or []
    for i, d in enumerate(docs, 1):
        print(f"Doc {i}: source={d.get('source')} title={(d.get('title') or '')[:100]} doi={d.get('doi')} oa_pdf={(d.get('links') or {}).get('oa_pdf')}")

    print("\n-- Source Stats --")
    for s in data.get("source_stats") or []:
        print(f"{s['name']}: fetched={s['fetched']} errors={s['errors']} details={s.get('details')}")

    print("\n-- Enrichment Stats --")
    for s in data.get("enrichment_stats") or []:
        print(f"{s['name']}: fetched={s['fetched']} errors={s['errors']} details={s.get('details')}")

    # Minimal assertions: at least one source attempted and enrichment ran
    assert any(s.get("name") == "europe_pmc" for s in data.get("source_stats") or [])
    assert any(s.get("name") == "arxiv" for s in data.get("source_stats") or [])
    assert any(s.get("name") == "crossref" for s in data.get("enrichment_stats") or [])
    assert any(s.get("name") == "unpaywall" for s in data.get("enrichment_stats") or [])


@pytest.mark.asyncio
async def test_multi_source_extractor_manual_sources():
    agent = MultiSourceDataExtractorAgent(collection_name="ResearchPaper", research_domain="General")

    res = await agent.run(
        query="machine learning interpretability",
        research_domain="Technology",
        sources=["openalex", "arxiv"],
        enrich_with=["crossref", "unpaywall"],
        max_results=3,
        per_source_limit=2,
        store=False,
    )

    assert res.get("success") is True
    data = res.get("data") or {}
    # Validate that only the requested sources appear in source_stats set
    names = {s.get("name") for s in data.get("source_stats") or []}
    assert "openalex" in names or "arxiv" in names
    assert "europe_pmc" not in names 