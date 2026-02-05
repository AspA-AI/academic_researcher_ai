"""
Request models for the Research Pipeline API.
Contains Pydantic models for all API request bodies.
"""

from typing import Optional, List, Dict, Any,  Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
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


class PipelineConfig(BaseModel):
    """Configuration model for pipeline execution."""
    enable_supervisor: bool = Field(default=False, description="Enable supervisor quality control")
    auto_retry_failed_steps: bool = Field(default=True, description="Automatically retry failed steps")
    save_intermediate_results: bool = Field(default=True, description="Save intermediate step results")
    max_retries: int = Field(default=3, description="Maximum retry attempts", ge=0, le=10)

class PipelineRequest(BaseModel):
    """Request model for creating a new research pipeline."""
    query: str = Field(..., description="Research query to analyze", min_length=1, max_length=500)
    research_domain: str = Field(default="General", description="Research domain or field")
    max_results: int = Field(default=20, description="Maximum number of documents to retrieve", ge=1) #, le=100
    year_from: int = Field(default=2020, description="Start year for document search", ge=1990, le=2024)
    year_to: int = Field(default=2024, description="End year for document search", ge=1990, le=2025)
    pipeline_config: Optional[PipelineConfig] = Field(default=None, description="Optional pipeline configuration")

    mode: Literal["auto", "manual"] = "auto"
    sources: List[SourceId] = Field(default_factory=list, description="Discovery sources (used only when mode=manual)")
    enrich: EnrichPreset = EnrichPreset.standard
    limit: int
    store: bool = False
    
    @field_validator('year_to')
    @classmethod
    def validate_year_range(cls, v, info):
        if hasattr(info, 'data') and 'year_from' in info.data and v < info.data['year_from']:
            raise ValueError('year_to must be greater than or equal to year_from')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "blockchain governance transparency",
                "research_domain": "Blockchain Technology",
                "max_results": 20,
                "year_from": 2020,
                "year_to": 2024,
                "pipeline_config": {
                    "enable_supervisor": False,
                    "auto_retry_failed_steps": True,
                    "save_intermediate_results": True,
                    "max_retries": 3
                },
                "mode": "auto",
                "sources": [
                    "openalex"
                ],
                "enrich": "standard",
                "limit": 20,
                "store": "true"
            }
        }
    }

class DataRequest(BaseModel):
    """Request model for data operations."""
    query: Optional[str] = Field(None, description="Search query", min_length=1, max_length=500)
    research_domain: str = Field(default="General", description="Research domain or field", max_length=100)
    max_results: int = Field(default=10, description="Maximum number of results to return", ge=1, le=100)
    documents: Optional[List[Dict[str, Any]]] = Field(None, description="Documents for storage or similarity search")
    collection_name: Optional[str] = Field(default="ResearchPaper", description="Collection name for operations")
    document_ids: Optional[List[str]] = Field(None, description="Document IDs for deletion")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "machine learning algorithms",
                "research_domain": "Computer Science",
                "max_results": 10,
                "documents": [
                    {
                        "title": "Sample Document",
                        "content": "Document content...",
                        "authors": "Author Name",
                        "year": 2024
                    }
                ],
                "collection_name": "ResearchPaper",
                "document_ids": ["doc1", "doc2"]
            }
        }
    }

class ReportRequest(BaseModel):
    """Request model for report generation."""
    pipeline_id: str = Field(..., description="Pipeline ID to generate report for")
    include_sections: Optional[List[str]] = Field(default=None, description="Specific sections to include")
    format: str = Field(default="markdown", description="Report format", pattern=r"^(markdown|html|pdf)$")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
                "include_sections": ["literature_review", "themes", "conclusions"],
                "format": "markdown"
            }
        }
    }

class AgentRequest(BaseModel):
    """Request model for individual agent execution."""
    agent_type: str = Field(..., description="Type of agent to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for the agent")
    research_domain: str = Field(default="General", description="Research domain or field")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Agent-specific configuration")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "agent_type": "literature_review",
                "input_data": {
                    "documents": [],
                    "query": "blockchain governance"
                },
                "research_domain": "Blockchain Technology",
                "config": {
                    "max_tokens": 2000
                }
            }
        }
    }

class QualityRequest(BaseModel):
    """Request model for quality assessment."""
    pipeline_id: str = Field(..., description="Pipeline ID to assess")
    step_name: Optional[str] = Field(default=None, description="Specific step to assess")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
                "step_name": "literature_review"
            }
        }
    }

class QualityOverrideRequest(BaseModel):
    """Request model for quality override decisions."""
    pipeline_id: str = Field(..., description="Pipeline ID")
    step_name: str = Field(..., description="Step name to override")
    decision: str = Field(..., description="Override decision", pattern=r"^(approve|revise|halt)$")
    reason: Optional[str] = Field(default=None, description="Reason for override")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
                "step_name": "literature_review",
                "decision": "approve",
                "reason": "Manual review confirms quality is sufficient"
            }
        }
    }

class QualityThresholdsRequest(BaseModel):
    """Request model for updating quality thresholds."""
    pipeline_id: Optional[str] = Field(default=None, description="Pipeline ID (if specific to pipeline)")
    thresholds: Dict[str, float] = Field(..., description="Quality thresholds to update")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pipeline_id": "550e8400-e29b-41d4-a716-446655440000",
                "thresholds": {
                    "literature_review": 0.7,
                    "initial_coding": 0.6,
                    "thematic_grouping": 0.8
                }
            }
        }
    } 