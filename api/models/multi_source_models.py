from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class YearsWindow(BaseModel):
    from_year: Optional[int] = Field(default=None, alias="from")
    to_year: Optional[int] = Field(default=None, alias="to")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {"from": 2023, "to": 2025}
        },
    }


class SourceId(str, Enum):
    openalex = "openalex"
    europe_pmc = "europe_pmc"
    arxiv = "arxiv"
    core = "core"


class EnrichPreset(str, Enum):
    none = "none"
    standard = "standard"
    deep = "deep"


class MultiSourceExtractorRequest(BaseModel):
    """Simplified request model for Multi-Source Data Extractor Agent."""
    query: str
    mode: Literal["auto", "manual"] = "auto"
    sources: List[SourceId] = Field(default_factory=list, description="Discovery sources (used only when mode=manual)")
    enrich: EnrichPreset = EnrichPreset.standard
    limit: int = 20
    years: Optional[YearsWindow] = None
    store: bool = False
    collection_name: str = "ResearchPaper"
    research_domain: str = "General"
    auto_fallback: bool = True

    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "query": "blockchain governance",
    #             "mode": "auto",
    #             "enrich": "standard",
    #             "limit": 12,
    #             "years": {"from": 2023, "to": 2025},
    #             "store": False,
    #             "collection_name": "ResearchPaper",
    #             "research_domain": "Technology",
    #             "auto_fallback": True,
    #             "sources": []
    #         }
    #     } 