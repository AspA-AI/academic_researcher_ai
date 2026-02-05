"""
Response models for the Research Pipeline API.
Contains Pydantic models for API responses and error handling.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class PipelineStatus(str, Enum):
    """Enumeration of pipeline status values."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"

class AgentStatus(str, Enum):
    """Enumeration of agent status values."""
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"

class QualityStatus(str, Enum):
    """Enumeration of quality assessment status values."""
    APPROVE = "APPROVE"
    REVISE = "REVISE"
    HALT = "HALT"

class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = Field(..., description="Whether the operation was successful")
    timestamp: str = Field(..., description="ISO timestamp of the response")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseResponse):
    """Standard error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Optional error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Pipeline not found",
                "error_code": "PIPELINE_NOT_FOUND",
                "details": {"pipeline_id": "invalid-id"},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class SuccessResponse(BaseResponse):
    """Standard success response model."""
    success: bool = Field(default=True, description="Always true for success")
    message: Optional[str] = Field(default=None, description="Optional success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class PipelineResponse(BaseResponse):
    """Response model for pipeline operations."""
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    status: PipelineStatus = Field(..., description="Current pipeline status")
    data: Dict[str, Any] = Field(..., description="Pipeline data and results")
    result: Dict[str, Any] = Field(..., description="Pipeline data and results")

    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "pipeline_id": "pipeline-123",
                "status": "running",
                "result": {},
                "data": {
                    "current_step": 2,
                    "total_steps": 6,
                    "started_at": "2024-01-15T10:30:00Z",
                    "query": "transparency in blockchain",
                    "research_domain": "Blockchain",
                    "quality_scores": {"literature_review": 0.8},
                    "supervisor_decisions": {"literature_review": "APPROVE"}
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class PipelineProgressResponse(BaseResponse):
    """Response model for pipeline progress."""
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    status: PipelineStatus = Field(..., description="Current pipeline status")
    data: Dict[str, Any] = Field(..., description="Detailed progress information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "pipeline_id": "pipeline-123",
                "status": "running",
                "data": {
                    "progress": {
                        "current_step": 3,
                        "total_steps": 6,
                        "percentage": 50.0
                    },
                    "steps": [
                        {
                            "step_number": 1,
                            "step_name": "Document Retrieval",
                            "status": "completed",
                            "message": "Retrieved 15 documents",
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "quality_scores": {"literature_review": 0.8},
                    "supervisor_decisions": {"literature_review": "APPROVE"},
                    "started_at": "2024-01-15T10:30:00Z",
                    "estimated_completion": "2024-01-15T10:45:00Z"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class PipelineResultsResponse(BaseResponse):
    """Response model for pipeline results."""
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    data: Dict[str, Any] = Field(..., description="Pipeline results and outputs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "pipeline_id": "pipeline-123",
                "data": {
                    "results": {
                        "literature_review": {"summary": "Literature review results"},
                        "initial_coding": {"coding_summary": {"total_units": 10}},
                        "thematic_grouping": {"thematic_summary": {"total_themes": 3}},
                        "theme_refinement": {"refinement_summary": {"total_themes": 3}},
                        "report_generation": {"report_id": "report-456"}
                    },
                    "quality_scores": {
                        "literature_review": 0.8,
                        "initial_coding": 0.7,
                        "thematic_grouping": 0.9,
                        "theme_refinement": 0.8,
                        "report_generation": 0.9
                    },
                    "supervisor_decisions": {
                        "literature_review": "APPROVE",
                        "initial_coding": "APPROVE",
                        "thematic_grouping": "APPROVE",
                        "theme_refinement": "APPROVE",
                        "report_generation": "APPROVE"
                    }
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class AgentResponse(BaseResponse):
    """Response model for agent operations."""
    agent_type: str = Field(..., description="Type of agent that was executed")
    data: Dict[str, Any] = Field(..., description="Agent output and results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "agent_type": "literature_review",
                "data": {
                    "summary": "Literature review summary",
                    "key_findings": ["Finding 1", "Finding 2"],
                    "research_gaps": ["Gap 1"],
                    "full_literature_review": "Complete literature review text"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class AgentStatusResponse(BaseResponse):
    """Response model for agent status information."""
    agents: Dict[str, Dict[str, Any]] = Field(..., description="Status of all agents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "agents": {
                    "literature_review": {
                        "status": "ready",
                        "last_used": "2024-01-15T10:30:00Z"
                    },
                    "initial_coding": {
                        "status": "running",
                        "last_used": "2024-01-15T10:35:00Z"
                    }
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class AgentHealthResponse(BaseResponse):
    """Response model for agent health information."""
    data: Dict[str, Any] = Field(..., description="Agent health information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "agent_type": "literature_review",
                    "status": "ready",
                    "last_used": "2024-01-15T10:30:00Z",
                    "healthy": True
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class QualityResponse(BaseResponse):
    """Response model for quality control operations."""
    assessment_id: str = Field(..., description="Unique assessment identifier")
    data: Dict[str, Any] = Field(..., description="Quality assessment results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "assessment_id": "assessment-123",
                "data": {
                    "agent_type": "literature_review",
                    "research_domain": "Blockchain",
                    "quality_score": 0.8,
                    "supervisor_status": "APPROVE",
                    "recommended_action": "APPROVE",
                    "confidence": 0.9,
                    "feedback": ["Good summary", "Clear findings"],
                    "action": "Proceed to next step",
                    "issues_found": [],
                    "thresholds": {"min_score": 0.6, "halt_threshold": 0.3}
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class QualityHistoryResponse(BaseResponse):
    """Response model for quality assessment history."""
    data: Dict[str, Any] = Field(..., description="Quality history and statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "assessments": [
                        {
                            "assessment_id": "assessment-123",
                            "agent_type": "literature_review",
                            "quality_score": 0.8,
                            "supervisor_status": "APPROVE",
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "statistics": {
                        "total_assessments": 10,
                        "approved": 8,
                        "revised": 1,
                        "halted": 1,
                        "manual_overrides": 0,
                        "approval_rate": 80.0
                    }
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class QualityAnalyticsResponse(BaseResponse):
    """Response model for quality analytics."""
    data: Dict[str, Any] = Field(..., description="Quality analytics and trends")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "total_assessments": 25,
                    "average_quality_score": 0.75,
                    "agent_performance": {
                        "literature_review": {
                            "total_assessments": 5,
                            "average_score": 0.8,
                            "approval_rate": 80.0
                        }
                    },
                    "recent_trend": "improving"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class DataResponse(BaseResponse):
    """Response model for data operations."""
    data: Dict[str, Any] = Field(..., description="Data operation results")
    operation_id: Optional[str] = Field(default=None, description="Unique operation identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "documents": [
                        {
                            "title": "Sample Paper",
                            "authors": ["Author 1", "Author 2"],
                            "year": 2023,
                            "abstract": "Sample abstract"
                        }
                    ],
                    "query": "blockchain transparency",
                    "research_domain": "Blockchain",
                    "total_count": 1,
                    "max_results": 10
                },
                "operation_id": "op-123",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class DataStatisticsResponse(BaseResponse):
    """Response model for data statistics."""
    data: Dict[str, Any] = Field(..., description="Data statistics and metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "current_collection": "ResearchPaper",
                    "research_domain": "Blockchain",
                    "total_operations": 15,
                    "recent_operations": 5
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class ReportResponse(BaseResponse):
    """Response model for report operations."""
    data: Dict[str, Any] = Field(..., description="Report operation results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "report_id": "report-123",
                    "pipeline_id": "pipeline-456",
                    "research_domain": "Blockchain",
                    "file_path": "/reports/report_123.md",
                    "word_count": 1500,
                    "total_references": 25,
                    "sections_included": {
                        "Abstract": True,
                        "Introduction": True,
                        "Literature Review": True,
                        "Methodology": True,
                        "Findings": True,
                        "Discussion": True,
                        "Conclusion": True
                    },
                    "report_preview": "This is a preview of the generated report..."
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class ReportListResponse(BaseResponse):
    """Response model for report list operations."""
    data: Dict[str, Any] = Field(..., description="Report list and metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "reports": [
                        {
                            "report_id": "report-123",
                            "pipeline_id": "pipeline-456",
                            "research_domain": "Blockchain",
                            "word_count": 1500,
                            "total_references": 25,
                            "generated_at": "2024-01-15T10:30:00Z",
                            "status": "completed"
                        }
                    ],
                    "total_reports": 10,
                    "filtered_count": 5
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class ReportDownloadResponse(BaseResponse):
    """Response model for report download operations."""
    data: Dict[str, Any] = Field(..., description="Report content and metadata")
    format: str = Field(..., description="Format of the downloaded report")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "report_id": "report-123",
                    "content": "# Thematic Literature Review\n\nThis is the report content..."
                },
                "format": "markdown",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class ReportStatisticsResponse(BaseResponse):
    """Response model for report statistics."""
    data: Dict[str, Any] = Field(..., description="Report statistics and metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "total_reports": 25,
                    "total_words": 37500,
                    "total_references": 625,
                    "average_words_per_report": 1500,
                    "average_references_per_report": 25,
                    "research_domain_distribution": {
                        "Blockchain": 10,
                        "AI": 8,
                        "Web3": 7
                    },
                    "reports_last_7_days": 5,
                    "most_common_domain": "Blockchain"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class PipelineStatisticsResponse(BaseResponse):
    """Response model for pipeline statistics."""
    data: Dict[str, Any] = Field(..., description="Pipeline statistics and metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "total_pipelines": 15,
                    "completed": 12,
                    "failed": 2,
                    "halted": 1,
                    "running": 0,
                    "success_rate": 80.0
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        } 