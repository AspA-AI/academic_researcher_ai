# B2B AI Research Automation Platform - Specification

## 1. Overview

### 1.1 Purpose
Build a B2B-focused AI research automation platform that automates the entire research workflow from topic input to a **structured, machine-readable JSON report**.

The platform accepts user research parameters, fetches content from external sources, performs multi-agent thematic analysis, and returns a **canonical JSON output** that can later be rendered into PDFs/PPTX/DOCX/HTML via templates.

### 1.2 Key Features
- **Multi-Source Content Ingestion**: Fetches research content from CoreAPI, Google Web Search, arXiv, and other academic sources
- **Intelligent Document Processing**: Chunks, embeds, and stores documents in Weaviate vector database
- **Multi-Agent Analysis Pipeline**: Orchestrates specialized AI agents for literature review, coding, thematic analysis, and validation
- **JSON-first Report Generation**: Produces a structured report object (themes, citations, sections, metadata) as the system-of-record output
- **B2B Focus**: Designed for enterprise research teams requiring structured, citation-rich outputs

### 1.3 MVP Scope
- **Included**:
  - Multi-source content fetching
  - Vector database storage (Weaviate)
  - Complete agent pipeline (6 agents)
  - JSON-first final report output (no templates yet)
  - Harvard-style citations
  
- **Excluded** (for MVP):
  - Complex database operations
  - Internal document uploads
  - User authentication system
  - Advanced analytics dashboard
  - Multi-user collaboration features
  - Template rendering (PDF/PPTX/DOCX/HTML) — planned next

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐
│   Frontend UI   │
│  (Next.js/React)│
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼─────────────────────────────────────────┐
│         FastAPI Backend                          │
│  ┌──────────────────────────────────────────┐   │
│  │     Pipeline Orchestrator                 │   │
│  │  - State Management                      │   │
│  │  - Agent Coordination                    │   │
│  │  - Error Handling                        │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Research │  │ Retrieval│  │ Initial │        │
│  │ & Ingestion│ │  Logic   │  │ Coding  │        │
│  │  Agent   │  │  Agent   │  │  Agent  │        │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Thematic  │  │Validation│  │  Report  │        │
│  │ Grouping │  │ & Refine │  │Generator │        │
│  │  Agent   │  │  Agent   │  │  Agent   │        │
│  └──────────┘  └──────────┘  └──────────┘        │
└────────┬─────────────────────────────────────────┘
         │
         ├─────────────────┬─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌─────▼─────┐    ┌─────▼─────┐
    │ Weaviate│      │  OpenAI   │    │  Google   │
    │  Vector │      │   API     │    │   Drive   │
    │  Store  │      │           │    │    API    │
    └─────────┘      └───────────┘    └───────────┘
         │
    ┌────▼────┐
    │ External│
    │ Sources │
    │(CoreAPI,│
    │arXiv...)│
    └─────────┘
```

### 2.2 Technology Stack

**Backend:**
- FastAPI (Python 3.10+)
- LangChain & LangChain OpenAI
- Weaviate Client (v4.0+)
- OpenAI API (GPT-4, Embeddings)
- aiohttp (async HTTP client)

**Vector Database:**
- Weaviate (cloud or self-hosted)
- OpenAI embeddings (text-embedding-3-small or text-embedding-ada-002)

**External APIs:**
- CORE API (academic papers)
- OpenAlex API (academic metadata)
- Europe PMC API
- arXiv API
- Google Custom Search API (optional)

**Frontend (Future):**
- Next.js / React
- TypeScript

## 3. User Inputs & Requirements

### 3.1 Required Inputs

| Input Field | Type | Required | Description |
|------------|------|----------|-------------|
| `query` | string | Yes | Research topic/question to investigate |
| `research_domain` | string | No | Domain/context label (default: "General") |
| `year_from` | integer | No | Start year filter |
| `year_to` | integer | No | End year filter |
| `max_results` | integer | No | Maximum documents to retrieve |
| `mode` | enum | No | `"auto"` (default) or `"manual"` |
| `sources` | array[string] | No | Used when `mode=manual`: `["core","arxiv","openalex","europe_pmc"]` |
| `output_format` | enum | No | MVP: `"json"` only |

### 3.2 Optional Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_results` | integer | 30 | Maximum documents to retrieve |
| `quality_threshold` | float | 0.6 | Minimum quality score for documents |
| `language` | string | "en" | Content language filter |
| `oa_only` | boolean | true | Open access only filter |
| `full_text` | boolean | false | Fetch full text when available |

## 4. Agent Specifications

### 4.1 Research & Ingestion Agent

**Purpose**: Fetches, cleans, and stores content from external sources.

**Responsibilities**:
1. Accept user query, date range, authors, and source selection
2. Query external APIs (CoreAPI, arXiv, OpenAlex, Europe PMC, Google)
3. Clean and normalize retrieved content
4. Chunk large documents into processable units (500-1000 tokens)
5. Generate embeddings using OpenAI
6. Store documents and embeddings in Weaviate vector store

**Input**:
```json
{
  "query": "AI in healthcare",
  "date_range": {"from": 2024, "to": 2025},
  "authors": ["Smith, J."],
  "sources": ["core", "arxiv"],
  "max_results": 30,
  "research_domain": "Healthcare"
}
```

**Output**:
```json
{
  "status": "success",
  "documents_retrieved": 25,
  "documents_stored": 25,
  "chunks_created": 150,
  "collection_name": "ResearchPaper_Healthcare",
  "metadata": {
    "sources_queried": ["core", "arxiv"],
    "retrieval_time": "2024-01-15T10:30:00Z"
  }
}
```

**Implementation Details**:
- Uses existing `MultiSourceDataExtractorAgent`
- Chunking strategy: RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
- Embedding model: `text-embedding-3-small`
- Weaviate collection naming: `{ResearchPaper}_{research_domain}`

### 4.2 Retriever Logic Agent

**Purpose**: Retrieves relevant documents from vector store based on semantic queries.

**Responsibilities**:
1. Perform semantic similarity search in Weaviate
2. Rerank results using cross-encoder models (optional)
3. Verify document provenance and metadata
4. Filter by research domain
5. Return ranked list with relevance scores

**Input**:
```json
{
  "query": "machine learning applications in medical diagnosis",
  "top_k": 10,
  "research_domain": "Healthcare",
  "filters": {
    "year_from": 2024,
    "year_to": 2025
  }
}
```

**Output**:
```json
{
  "status": "success",
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
}
```

**Implementation Details**:
- Uses Weaviate's `nearText` query with `certainty` threshold
- Optional reranking: Cross-encoder model (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Filters: `where` clauses for year, authors, source

### 4.3 Initial Coding Agent

**Purpose**: Performs open coding on academic texts to extract meaningful units and assign codes.

**Responsibilities**:
1. Segment documents into meaningful units (sentences/paragraphs)
2. Assign descriptive codes to each unit
3. Maintain code dictionary for consistency
4. Generate Harvard-style citations for each coded unit
5. Track code confidence scores
6. Create code-to-document mapping

**Input**:
```json
{
  "documents": [...], // Retrieved documents from Retriever
  "research_domain": "Healthcare",
  "research_question": "How is AI used in medical diagnosis?"
}
```

**Output**:
```json
{
  "status": "success",
  "coded_units": [
    {
      "unit_id": "unit_001",
      "text": "Machine learning algorithms have shown promise...",
      "code": "ML_DIAGNOSTIC_ACCURACY",
      "code_definition": "References to ML improving diagnostic accuracy",
      "confidence": 0.92,
      "citation": {
        "author": "Smith, J.",
        "year": 2024,
        "title": "AI in Medical Diagnosis",
        "doi": "10.1234/example",
        "harvard_format": "Smith, J. (2024) AI in Medical Diagnosis. DOI: 10.1234/example"
      },
      "source_document_id": "uuid-123",
      "chunk_index": 0
    }
  ],
  "code_dictionary": {
    "ML_DIAGNOSTIC_ACCURACY": {
      "definition": "References to ML improving diagnostic accuracy",
      "frequency": 15,
      "examples": ["unit_001", "unit_045", ...]
    }
  },
  "total_units_coded": 150,
  "unique_codes": 25
}
```

**Implementation Details**:
- Uses existing `InitialCodingAgent`
- LLM: GPT-4-turbo for code assignment
- Citation format: Harvard style (Author, Year, Title, DOI)
- Confidence scoring: Based on LLM certainty and code consistency

### 4.4 Thematic Grouping Agent

**Purpose**: Clusters individual codes into broader conceptual themes.

**Responsibilities**:
1. Analyze code relationships and patterns
2. Group related codes into themes
3. Provide justification for groupings
4. Identify cross-cutting ideas
5. Ensure theme distinctness
6. Include illustrative quotes from coded units

**Input**:
```json
{
  "coded_units": [...], // From Initial Coding Agent
  "code_dictionary": {...},
  "research_domain": "Healthcare"
}
```

**Output**:
```json
{
  "status": "success",
  "themes": [
    {
      "theme_id": "theme_001",
      "theme_name": "AI-Enhanced Diagnostic Accuracy",
      "description": "Themes related to improvements in diagnostic precision through AI",
      "codes_included": [
        "ML_DIAGNOSTIC_ACCURACY",
        "DEEP_LEARNING_IMAGING",
        "PREDICTIVE_ANALYTICS"
      ],
      "justification": "These codes all relate to AI improving diagnostic capabilities...",
      "illustrative_quotes": [
        {
          "text": "Machine learning algorithms have shown promise...",
          "citation": "Smith, J. (2024)...",
          "code": "ML_DIAGNOSTIC_ACCURACY"
        }
      ],
      "cross_cutting_ideas": [
        "Integration with existing medical workflows",
        "Need for validation studies"
      ],
      "theme_confidence": 0.88
    }
  ],
  "total_themes": 8,
  "codes_grouped": 25,
  "ungrouped_codes": []
}
```

**Implementation Details**:
- Uses GPT-4-turbo for semantic clustering
- Theme validation: Ensure themes are distinct (cosine similarity < 0.7)
- Cross-cutting identification: Codes that appear in multiple themes

### 4.5 Validation & Refinement Agent

**Purpose**: Reviews and refines thematic outputs for coherence and academic polish.

**Responsibilities**:
1. Review theme outputs for coherence
2. Ensure all critical themes are included
3. Adjust unclear labels or section names
4. Refine theme definitions and scope
5. Add supporting academic quotes with citations
6. Identify key concepts and theoretical frameworks
7. Describe research implications

**Input**:
```json
{
  "themes": [...], // From Thematic Grouping Agent
  "coded_units": [...],
  "research_question": "How is AI used in medical diagnosis?",
  "research_domain": "Healthcare"
}
```

**Output**:
```json
{
  "status": "success",
  "refined_themes": [
    {
      "theme_id": "theme_001",
      "theme_name": "AI-Enhanced Diagnostic Accuracy",
      "precise_definition": "This theme encompasses research demonstrating how artificial intelligence, particularly machine learning and deep learning algorithms, improves the accuracy, speed, and reliability of medical diagnostic processes across various medical specialties.",
      "scope": {
        "included": [
          "ML-based diagnostic tools",
          "Deep learning for medical imaging",
          "Predictive analytics in diagnosis"
        ],
        "excluded": [
          "Treatment recommendations",
          "Drug discovery applications"
        ]
      },
      "supporting_quotes": [
        {
          "quote": "Machine learning algorithms have shown promise in improving diagnostic accuracy by up to 15% compared to traditional methods...",
          "citation": "Smith, J. (2024) AI in Medical Diagnosis. DOI: 10.1234/example",
          "relevance": "high"
        }
      ],
      "key_concepts": [
        "Supervised learning",
        "Transfer learning",
        "Ensemble methods"
      ],
      "theoretical_frameworks": [
        "Computer-aided diagnosis (CAD)",
        "Clinical decision support systems"
      ],
      "research_implications": [
        "Need for large-scale validation studies",
        "Integration challenges with existing workflows",
        "Regulatory considerations for AI diagnostics"
      ],
      "validation_status": "approved"
    }
  ],
  "validation_summary": {
    "themes_reviewed": 8,
    "themes_approved": 7,
    "themes_refined": 1,
    "themes_rejected": 0,
    "overall_quality_score": 0.91
  }
}
```

**Implementation Details**:
- Uses GPT-4-turbo with validation prompts
- Quality criteria: Coherence, completeness, academic rigor
- Iterative refinement: Up to 2 refinement passes

### 4.6 Report Generation Agent

**Purpose**: Assembles all agent outputs into a single **canonical JSON report payload**.

**Responsibilities**:
1. Combine literature review, coding results, and themes
2. Generate complete academic paper structure:
   - Abstract
   - Introduction
   - Literature Review
   - Methodology
   - Findings (themes with evidence)
   - Discussion
   - Conclusion
   - References (Harvard style)
3. Format citations in Harvard style
4. Create reference list
5. Ensure logical flow and coherence
6. Output strict JSON that includes both structured fields and (optionally) a markdown preview string

**Input**:
```json
{
  "literature_review": {...},
  "coded_units": [...],
  "themes": [...],
  "research_question": "How is AI used in medical diagnosis?",
  "output_format": "json"
}
```

**Output**:
```json
{
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
  "rendered": { "markdown": "# AI in Medical Diagnosis\n\n..." },
  "report_summary": {
    "themes_count": 8,
    "references_count": 25
  }
}
```

**Implementation Details**:
- Google Docs API: `documents.create()` and `documents.batchUpdate()`
- Google Slides API: `presentations.create()` and `presentations.batchUpdate()`
- Citation formatting: Harvard style automation
- Section templates: Pre-defined academic paper structure

## 5. Data Models

### 5.1 Pipeline Request Model (Current)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum

class SourceId(str, Enum):
    openalex = "openalex"
    europe_pmc = "europe_pmc"
    arxiv = "arxiv"
    core = "core"

class PipelineConfig(BaseModel):
    enable_supervisor: bool = False
    auto_retry_failed_steps: bool = True
    save_intermediate_results: bool = True
    max_retries: int = 3

class PipelineRequest(BaseModel):
    query: str
    research_domain: str = "General"
    max_results: int = 20
    year_from: int = 2020
    year_to: int = 2024
    quality_threshold: float = 0.6
    pipeline_config: Optional[PipelineConfig] = None

    mode: Literal["auto", "manual"] = "auto"
    sources: List[SourceId] = []
    # Output for MVP is JSON-only; template rendering comes later
    output_format: Literal["json"] = "json"
```

### 5.2 Document Model

```python
class Document(BaseModel):
    id: str
    title: str
    content: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    source: str  # "core", "arxiv", "openalex", etc.
    url: Optional[str] = None
    abstract: Optional[str] = None
    chunk_index: Optional[int] = 0
    research_domain: str
    metadata: Optional[Dict[str, Any]] = {}
```

### 5.3 Coded Unit Model

```python
class Citation(BaseModel):
    author: str
    year: int
    title: str
    doi: Optional[str] = None
    harvard_format: str

class CodedUnit(BaseModel):
    unit_id: str
    text: str
    code: str
    code_definition: str
    confidence: float
    citation: Citation
    source_document_id: str
    chunk_index: int
```

### 5.4 Theme Model

```python
class Theme(BaseModel):
    theme_id: str
    theme_name: str
    description: str
    codes_included: List[str]
    justification: str
    illustrative_quotes: List[Dict[str, Any]]
    cross_cutting_ideas: List[str]
    theme_confidence: float
    # Refined fields (from Validation Agent)
    precise_definition: Optional[str] = None
    scope: Optional[Dict[str, List[str]]] = None
    supporting_quotes: Optional[List[Dict[str, Any]]] = None
    key_concepts: Optional[List[str]] = None
    theoretical_frameworks: Optional[List[str]] = None
    research_implications: Optional[List[str]] = None
```

### 5.5 Pipeline State Model

```python
class PipelineStatus(str, Enum):
    INITIALIZED = "initialized"
    INGESTING = "ingesting"
    RETRIEVING = "retrieving"
    CODING = "coding"
    THEMATIC_GROUPING = "thematic_grouping"
    VALIDATING = "validating"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineState(BaseModel):
    pipeline_id: str
    status: PipelineStatus
    topic: str
    date_range: DateRange
    research_domain: str
    documents_retrieved: Optional[int] = None
    coded_units: Optional[List[CodedUnit]] = None
    themes: Optional[List[Theme]] = None
    report_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

## 6. API Endpoints

### 6.1 Start Research Pipeline

**POST** `/api/v1/pipelines/`

**Request Body**:
```json
{
  "query": "AI applications in medical diagnosis",
  "research_domain": "Healthcare",
  "year_from": 2020,
  "year_to": 2024,
  "max_results": 20,
  "mode": "auto",
  "sources": ["openalex", "arxiv", "core"],
  "output_format": "json"
}
```

**Response** (202 Accepted):
```json
{
  "success": true,
  "pipeline_id": "pipeline_12345",
  "status": "initialized",
  "message": "Pipeline started successfully",
  "estimated_completion_time_minutes": 15
}
```

### 6.2 Get Pipeline Status

**GET** `/api/v1/pipelines/{pipeline_id}`

**Response**:
```json
{
  "success": true,
  "pipeline_id": "pipeline_12345",
  "status": "thematic_grouping",
  "progress": {
    "current_step": "Thematic Grouping",
    "steps_completed": 4,
    "total_steps": 6,
    "percentage": 66.7
  },
  "results": {
    "documents_retrieved": 25,
    "coded_units": 150,
    "themes_identified": 8
  },
  "estimated_time_remaining_minutes": 5
}
```

### 6.3 Get Pipeline Results

**GET** `/api/v1/pipelines/{pipeline_id}/results`

**Response** (only when status = "completed"):
```json
{
  "success": true,
  "pipeline_id": "pipeline_12345",
  "report": {
    "google_drive_file_id": "1a2b3c4d5e6f7g8h9i0j",
    "google_drive_url": "https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/edit",
    "file_name": "AI_in_Medical_Diagnosis_Research_Report_2024-01-15.docx"
  },
  "summary": {
    "documents_analyzed": 25,
    "coded_units": 150,
    "themes_identified": 8,
    "total_citations": 25
  }
}
```

## 7. Output & Templates (Post-MVP)

The system-of-record output is a structured JSON payload. Post-MVP, the platform will add renderers/templates to produce downloadable artifacts:

- PDF via HTML+CSS templates
- PPTX via slide templates
- DOCX via document templates

These renderers will consume the canonical JSON and will not change the pipeline/agent semantics.

## 8. Error Handling

### 8.1 Error Types

1. **Validation Errors** (400): Invalid input parameters
2. **Authentication Errors** (401): Reserved for future user auth (not in MVP)
3. **External API Errors** (502): CoreAPI, arXiv, etc. unavailable
4. **Processing Errors** (500): Agent failures, LLM errors
5. **Storage Errors** (500): Weaviate connection issues

### 8.2 Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "EXTERNAL_API_ERROR",
  "details": {
    "source": "core_api",
    "status_code": 503,
    "retry_after_seconds": 60
  },
  "pipeline_id": "pipeline_12345",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

## 9. Performance Requirements

### 9.1 Response Times

- Pipeline initiation: < 2 seconds
- Document retrieval: < 30 seconds (for 30 documents)
- Initial coding: < 5 minutes (for 150 units)
- Thematic grouping: < 3 minutes
- Report generation: < 2 minutes
- **Total pipeline time**: < 15 minutes (for typical research query)

### 9.2 Scalability

- Support concurrent pipelines: 10+ simultaneous
- Vector store: Handle 10,000+ documents per research domain
- Rate limiting: 100 requests/minute per user (future)

## 10. Security Considerations

1. **OAuth Token Security**:
   - Tokens never logged
   - Tokens validated before use
   - Refresh tokens stored encrypted

2. **API Key Management**:
   - Environment variables for all API keys
   - No keys in code or logs

3. **Data Privacy**:
   - User research data not shared between users
   - Vector store collections isolated by user (future)

## 11. Future Enhancements (Post-MVP)

1. User authentication and multi-user support
2. Advanced analytics dashboard
3. Custom report templates
4. Collaborative editing features
5. Export to PDF/Word formats
6. Citation style options (APA, MLA, etc.)
7. Real-time progress updates via WebSocket
8. Research project history and management

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Status**: Draft for Review

