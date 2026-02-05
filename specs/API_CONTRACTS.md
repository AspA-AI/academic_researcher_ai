# API Contracts Specification

## 1. Pipeline Management Endpoints

### 1.1 Start Research Pipeline

**Endpoint**: `POST /api/v1/pipelines/`

**Description**: Initiates a new research pipeline with the provided parameters.

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "query": "AI applications in medical diagnosis",
  "research_domain": "Healthcare",
  "max_results": 20,
  "year_from": 2020,
  "year_to": 2024,
  "quality_threshold": 0.6,
  "mode": "auto",
  "sources": ["openalex", "arxiv", "core"],
  "output_format": "json",
  "pipeline_config": {
    "enable_supervisor": false,
    "auto_retry_failed_steps": true,
    "save_intermediate_results": true,
    "max_retries": 3
  }
}
```

**Request Schema**:
```python
class DateRange(BaseModel):
    from_year: int = Field(..., ge=1900, le=2100)
    to_year: int = Field(..., ge=1900, le=2100)
    
    @validator('to_year')
    def validate_year_range(cls, v, values):
        if 'from_year' in values and v < values['from_year']:
            raise ValueError('to_year must be >= from_year')
        return v

class PipelineRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    research_domain: str = Field(default="General")
    max_results: int = Field(default=20, ge=1)
    year_from: int = Field(default=2020, ge=1990, le=2024)
    year_to: int = Field(default=2024, ge=1990, le=2025)
    quality_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    mode: Literal["auto", "manual"] = "auto"
    sources: List[str] = Field(default_factory=list)
    output_format: Literal["json"] = "json"
    pipeline_config: Optional[Dict[str, Any]] = None
```

**Response** (202 Accepted):
```json
{
  "success": true,
  "pipeline_id": "pipeline_abc123def456",
  "status": "initialized",
  "message": "Pipeline started successfully",
  "estimated_completion_time_minutes": 15,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses**:

**400 Bad Request** - Validation Error:
```json
{
  "success": false,
  "error": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "topic",
    "message": "Topic must be between 5 and 500 characters"
  }
}
```

**401 Unauthorized**:
Reserved for future user authentication (not used in MVP).

### 1.2 Get Pipeline Status

**Endpoint**: `GET /api/v1/pipelines/{pipeline_id}`

**Description**: Retrieves the current status and progress of a pipeline.

**Path Parameters**:
- `pipeline_id` (string, required): Unique pipeline identifier

**Response** (200 OK):
```json
{
  "success": true,
  "pipeline_id": "pipeline_abc123def456",
  "status": "thematic_grouping",
  "progress": {
    "current_step": "Thematic Grouping",
    "steps_completed": 4,
    "total_steps": 6,
    "percentage": 66.7,
    "step_details": {
      "step_1": {"name": "Research & Ingestion", "status": "completed", "duration_seconds": 45},
      "step_2": {"name": "Document Retrieval", "status": "completed", "duration_seconds": 12},
      "step_3": {"name": "Initial Coding", "status": "completed", "duration_seconds": 180},
      "step_4": {"name": "Thematic Grouping", "status": "in_progress", "duration_seconds": 90},
      "step_5": {"name": "Validation & Refinement", "status": "pending"},
      "step_6": {"name": "Report Generation", "status": "pending"}
    }
  },
  "results": {
    "documents_retrieved": 25,
    "documents_stored": 25,
    "coded_units": 150,
    "unique_codes": 25,
    "themes_identified": 8
  },
  "estimated_time_remaining_minutes": 5,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

**Error Responses**:

**404 Not Found**:
```json
{
  "success": false,
  "error": "Pipeline not found",
  "error_code": "PIPELINE_NOT_FOUND",
  "pipeline_id": "pipeline_abc123def456"
}
```

### 1.3 Get Pipeline Results

**Endpoint**: `GET /api/v1/pipelines/{pipeline_id}/results`

**Description**: Retrieves the final results of a completed pipeline.

**Path Parameters**:
- `pipeline_id` (string, required): Unique pipeline identifier

**Response** (200 OK - Only when status = "completed"):
```json
{
  "success": true,
  "pipeline_id": "pipeline_abc123def456",
  "status": "completed",
  "report_result": {
    "report": {
      "title": "AI in Medical Diagnosis — Thematic Literature Review",
      "research_domain": "Healthcare",
      "generated_at": "2026-01-27T12:00:00Z",
      "sections": {
        "abstract": "...",
        "introduction": "...",
        "literature_review": "...",
        "methodology": "...",
        "findings": [
          {
            "theme_name": "AI-Enhanced Diagnostic Accuracy",
            "precise_definition": "...",
            "scope": {"included": ["..."], "excluded": ["..."]},
            "supporting_quotes": [{"quote": "...", "citation": "Smith (2024)"}],
            "key_concepts": ["..."],
            "theoretical_frameworks": ["..."],
            "research_implications": ["..."]
          }
        ],
        "discussion": "...",
        "conclusion": "..."
      },
      "references": [{"full_citation": "Smith, J. (2024) ..."}]
    },
    "rendered": {"markdown": "# Title\n\n..."},
    "report_summary": {"themes_count": 8, "references_count": 25}
  },
  "summary": {
    "documents_analyzed": 25,
    "documents_retrieved": 25,
    "coded_units": 150,
    "unique_codes": 25,
    "themes_identified": 8,
    "total_citations": 25
  },
  "themes": [
    {
      "theme_id": "theme_001",
      "theme_name": "AI-Enhanced Diagnostic Accuracy",
      "codes_count": 3,
      "coded_units_count": 45
    }
  ],
  "completed_at": "2024-01-15T10:45:00Z",
  "total_duration_seconds": 900
}
```

**Error Responses**:

**400 Bad Request** - Pipeline not completed:
```json
{
  "success": false,
  "error": "Pipeline not yet completed",
  "error_code": "PIPELINE_INCOMPLETE",
  "current_status": "thematic_grouping"
}
```

## 2. Agent Endpoints

### 2.1 Execute Research & Ingestion Agent

**Endpoint**: `POST /api/v1/agents/research-ingestion`

**Description**: Manually execute the research and ingestion agent.

**Request Body**:
```json
{
  "query": "AI in healthcare",
  "date_range": {"from_year": 2024, "to_year": 2025},
  "authors": ["Smith, J."],
  "sources": ["core", "arxiv"],
  "max_results": 30,
  "research_domain": "Healthcare"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "agent": "research_ingestion",
  "status": "completed",
  "result": {
    "documents_retrieved": 25,
    "documents_stored": 25,
    "chunks_created": 150,
    "collection_name": "ResearchPaper_Healthcare",
    "sources_queried": ["core", "arxiv"],
    "retrieval_time": "2024-01-15T10:30:00Z"
  },
  "execution_time_seconds": 45
}
```

### 2.2 Execute Retriever Logic Agent

**Endpoint**: `POST /api/v1/agents/retriever`

**Description**: Execute semantic search and retrieval from vector store.

**Request Body**:
```json
{
  "query": "machine learning applications in medical diagnosis",
  "top_k": 10,
  "research_domain": "Healthcare",
  "collection_name": "ResearchPaper_Healthcare",
  "filters": {
    "year_from": 2024,
    "year_to": 2025,
    "authors": ["Smith, J."]
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "agent": "retriever",
  "status": "completed",
  "result": {
    "documents": [
      {
        "id": "uuid-123",
        "content": "Document text...",
        "title": "AI in Medical Diagnosis",
        "authors": ["Smith, J."],
        "year": 2024,
        "doi": "10.1234/example",
        "source": "core",
        "relevance_score": 0.89,
        "chunk_index": 0,
        "provenance": {
          "source_url": "https://core.ac.uk/...",
          "retrieved_at": "2024-01-15T10:30:00Z"
        }
      }
    ],
    "total_found": 10,
    "search_time_ms": 245
  },
  "execution_time_seconds": 0.5
}
```

### 2.3 Execute Initial Coding Agent

**Endpoint**: `POST /api/v1/agents/initial-coding`

**Description**: Perform open coding on documents.

**Request Body**:
```json
{
  "documents": [...],
  "research_domain": "Healthcare",
  "research_question": "How is AI used in medical diagnosis?"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "agent": "initial_coding",
  "status": "completed",
  "result": {
    "coded_units": [...],
    "code_dictionary": {...},
    "total_units_coded": 150,
    "unique_codes": 25
  },
  "execution_time_seconds": 180
}
```

### 2.4 Execute Thematic Grouping Agent

**Endpoint**: `POST /api/v1/agents/thematic-grouping`

**Description**: Cluster codes into themes.

**Request Body**:
```json
{
  "coded_units": [...],
  "code_dictionary": {...},
  "research_domain": "Healthcare"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "agent": "thematic_grouping",
  "status": "completed",
  "result": {
    "themes": [...],
    "total_themes": 8,
    "codes_grouped": 25,
    "ungrouped_codes": []
  },
  "execution_time_seconds": 90
}
```

### 2.5 Execute Validation & Refinement Agent

**Endpoint**: `POST /api/v1/agents/validation-refinement`

**Description**: Validate and refine themes.

**Request Body**:
```json
{
  "themes": [...],
  "coded_units": [...],
  "research_question": "How is AI used in medical diagnosis?",
  "research_domain": "Healthcare"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "agent": "validation_refinement",
  "status": "completed",
  "result": {
    "refined_themes": [...],
    "validation_summary": {
      "themes_reviewed": 8,
      "themes_approved": 7,
      "themes_refined": 1,
      "themes_rejected": 0,
      "overall_quality_score": 0.91
    }
  },
  "execution_time_seconds": 120
}
```

### 2.6 Execute Report Generation Agent

**Endpoint**: `POST /api/v1/agents/report-generation`

**Description**: Generate the canonical JSON report payload (JSON-first MVP).

**Request Body**:
```json
{
  "literature_review": {...},
  "coded_units": [...],
  "themes": [...],
  "research_question": "How is AI used in medical diagnosis?",
  "output_format": "json"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "agent": "report_generation",
  "status": "completed",
  "result": {
    "report": { "...": "..." },
    "rendered": {"markdown": "# Title\n\n..."},
    "report_summary": {"themes_count": 8, "references_count": 25}
  },
  "execution_time_seconds": 120
}
```

## 3. Data Management Endpoints

### 3.1 Store Documents

**Endpoint**: `POST /api/v1/data/store`

**Description**: Store documents in Weaviate vector database.

**Request Body**:
```json
{
  "documents": [
    {
      "title": "AI in Medical Diagnosis",
      "content": "Full document content...",
      "authors": ["Smith, J."],
      "year": 2024,
      "doi": "10.1234/example",
      "source": "core"
    }
  ],
  "research_domain": "Healthcare",
  "collection_name": "ResearchPaper_Healthcare"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "documents_stored": 25,
  "collection_name": "ResearchPaper_Healthcare",
  "chunks_created": 150
}
```

### 3.2 Retrieve Documents

**Endpoint**: `POST /api/v1/data/retrieve`

**Description**: Retrieve documents from vector store using semantic search.

**Request Body**:
```json
{
  "query": "machine learning in healthcare",
  "top_k": 10,
  "collection_name": "ResearchPaper_Healthcare",
  "filters": {
    "year_from": 2024,
    "year_to": 2025
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "documents": [...],
  "total_found": 10
}
```

### 3.3 List Collections

**Endpoint**: `GET /api/v1/data/collections`

**Description**: List all Weaviate collections.

**Response** (200 OK):
```json
{
  "success": true,
  "collections": [
    {
      "name": "ResearchPaper_Healthcare",
      "document_count": 1250,
      "created_at": "2024-01-10T08:00:00Z"
    },
    {
      "name": "ResearchPaper_Finance",
      "document_count": 850,
      "created_at": "2024-01-12T10:00:00Z"
    }
  ]
}
```

## 4. Report Management Endpoints

### 4.1 List Reports

**Endpoint**: `GET /api/v1/reports/`

**Description**: List all generated reports for a user (future: requires authentication).

**Query Parameters**:
- `pipeline_id` (optional): Filter by pipeline ID
- `limit` (optional, default=20): Maximum number of results
- `offset` (optional, default=0): Pagination offset

**Response** (200 OK):
```json
{
  "success": true,
  "reports": [
    {
      "report_id": "report_12345",
      "pipeline_id": "pipeline_abc123def456",
      "title": "AI in Medical Diagnosis",
      "output_format": "json",
      "has_markdown_preview": true,
      "created_at": "2024-01-15T10:45:00Z",
      "themes_count": 8,
      "references_count": 25
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

### 4.2 Get Report Details

**Endpoint**: `GET /api/v1/reports/{report_id}`

**Description**: Get detailed information about a specific report.

**Path Parameters**:
- `report_id` (string, required): Report identifier

**Response** (200 OK):
```json
{
  "success": true,
  "report": {
    "report_id": "report_12345",
    "pipeline_id": "pipeline_abc123def456",
    "output_format": "json",
    "total_citations": 25,
    "report_json": { "...": "..." },
    "rendered": { "markdown": "# Title\n\n..." },
    "created_at": "2024-01-15T10:45:00Z"
  }
}
```

## 5. Health & Monitoring Endpoints

### 5.1 Health Check

**Endpoint**: `GET /health`

**Description**: Check API health status.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": "2 days, 5 hours, 30 minutes",
  "total_requests": 1250,
  "active_pipelines": 3,
  "services": {
    "weaviate": "healthy",
    "openai": "healthy"
  }
}
```

### 5.2 Service Status

**Endpoint**: `GET /api/v1/status`

**Description**: Detailed status of all services and dependencies.

**Response** (200 OK):
```json
{
  "success": true,
  "services": {
    "weaviate": {
      "status": "healthy",
      "response_time_ms": 45,
      "collections_count": 5
    },
    "openai": {
      "status": "healthy",
      "response_time_ms": 120,
      "rate_limit_remaining": 5000
    },
    "core_api": {
      "status": "healthy",
      "response_time_ms": 300
    },
    "arxiv": {
      "status": "healthy",
      "response_time_ms": 250
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 6. Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "optional_field_name",
    "message": "Detailed error message",
    "retry_after_seconds": 60
  },
  "pipeline_id": "optional_pipeline_id",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AUTH_ERROR`: Reserved for future user authentication
- `PIPELINE_NOT_FOUND`: Pipeline ID does not exist
- `PIPELINE_INCOMPLETE`: Pipeline not yet completed
- `EXTERNAL_API_ERROR`: External API (CoreAPI, arXiv, etc.) error
- `VECTOR_STORE_ERROR`: Weaviate connection or operation error
- `LLM_ERROR`: OpenAI API error
- `REPORT_GENERATION_ERROR`: Report JSON generation error
- `INTERNAL_ERROR`: Internal server error

## 7. Rate Limiting

**Current**: No rate limiting (MVP)

**Future**:
- 100 requests/minute per user
- 10 concurrent pipelines per user
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## 8. Authentication

**Current**: OAuth token passed in request body (MVP)

**Future**:
- JWT-based authentication
- API key authentication
- OAuth token in Authorization header

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15

