# AI Researcher Backend - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [API Endpoints](#api-endpoints)
4. [RAG Implementation & Retrieval Methods](#rag-implementation--retrieval-methods)
5. [Metrics & Quality Assessment](#metrics--quality-assessment)
6. [Pipeline Flow](#pipeline-flow)
7. [Code References](#code-references)

---

## System Overview

The AI Researcher backend is a FastAPI-based REST API that automates academic research workflows. It uses a multi-agent system to:
- Retrieve academic papers from multiple sources
- Analyze and code documents
- Generate thematic analysis
- Create comprehensive academic reports

**Key Technologies:**
- **FastAPI**: Web framework for building APIs
- **Weaviate**: Vector database for semantic search
- **OpenAI**: Embeddings and LLM for text processing
- **Cross-Encoder**: Reranking model for retrieval accuracy

**Location**: `ai_researcher/api/`

---

## Backend Architecture

### Main Application Entry Point
**File**: `api/app.py`

The FastAPI application is initialized here with:
- Route registration (pipelines, agents, data, reports)
- Middleware (CORS, error handling)
- Health check endpoint

**Key Components:**
- `app`: Main FastAPI application instance
- Route routers registered with prefixes:
  - `/api/v1/pipelines` - Pipeline management
  - `/api/v1/agents` - Individual agent operations
  - `/api/v1/data` - Data management
  - `/api/v1/reports` - Report operations

---

## API Endpoints

### 1. Pipeline Endpoints
**Base Path**: `/api/v1/pipelines`  
**File**: `api/routes/pipeline_routes.py`

#### POST `/api/v1/pipelines/`
Start a full research pipeline (6 steps).

**Request Body:**
```json
{
  "query": "machine learning in healthcare",
  "research_domain": "Computer Science",
  "max_results": 20,
  "mode": "auto",
  "sources": ["openalex", "europe_pmc", "arxiv", "core"],
  "enrich": "standard",
  "year_from": 2020,
  "year_to": 2024,
  "store": true
}
```

**Pipeline Steps:**
1. Document Retrieval (with smart fallback)
2. Literature Review
3. Initial Coding
4. Thematic Grouping
5. Theme Refinement
6. Report Generation

**Response**: Pipeline ID, status, and results

**Code Location**: `api/services/pipeline_service.py` - `run_full_pipeline()`

---

#### POST `/api/v1/pipelines/lite`
Start a lite pipeline (3 steps, no coding/thematic analysis).

**Steps:**
1. Document Retrieval
2. Literature Review
3. Report Generation

**Code Location**: `api/services/pipeline_service.py` - `run_lite_pipeline()`

---

#### GET `/api/v1/pipelines/`
List all pipelines with optional filtering.

**Query Parameters:**
- `limit`: Max pipelines to return (default: 10)
- `status`: Filter by status (running, completed, failed)
- `research_domain`: Filter by domain

**Code Location**: `api/services/pipeline_service.py` - `list_pipelines()`

---

#### GET `/api/v1/pipelines/{pipeline_id}/progress`
Get real-time progress of a running pipeline.

**Response Includes:**
- Current step and percentage
- Step-by-step status
- Quality scores
- Estimated completion time

**Code Location**: `api/services/pipeline_service.py` - `get_pipeline_progress()`

---

#### GET `/api/v1/pipelines/{pipeline_id}/results`
Get final results from a completed pipeline.

**Response Includes:**
- Retrieved documents
- Literature review results
- Coding results
- Thematic analysis
- Final report information

**Code Location**: `api/services/pipeline_service.py` - `get_pipeline_results()`

---

#### GET `/api/v1/pipelines/{pipeline_id}/download`
Download the generated report.

**Query Parameters:**
- `format`: pdf, markdown, or text

**Code Location**: `api/services/pipeline_service.py` - `download_pipeline_report()`

---

#### GET `/api/v1/pipelines/statistics/overview`
Get comprehensive pipeline statistics.

**Metrics Returned:**
- Total pipelines
- Success rates
- Average processing times
- Quality score trends
- Research domain distribution

**Code Location**: `api/services/pipeline_service.py` - `get_pipeline_statistics()`

---

### 2. Agent Endpoints
**Base Path**: `/api/v1/agents`  
**File**: `api/routes/agent_routes.py`

#### POST `/api/v1/agents/data-extractor/extract`
Extract documents from CORE API.

**Request**: `DataExtractorRequest`
- `query`: Search query
- `max_results`: Number of papers
- `year_from`, `year_to`: Year range
- `research_domain`: Domain filter

**Code Location**: `api/agents/data_extractor_agent.py`

---

#### POST `/api/v1/agents/retriever/search`
Retrieve documents from vector store.

**Request**: `RetrieverRequest`
- `query`: Search query
- `top_k`: Number of results
- `collection_name`: Vector collection
- `research_domain`: Domain filter

**Code Location**: `api/agents/retriever_agent.py`

---

#### POST `/api/v1/agents/literature-review/generate`
Generate literature review from documents.

**Request**: `LiteratureReviewRequest`
- `documents`: List of documents
- `research_domain`: Domain context

**Code Location**: `api/agents/literature_review_agent.py`

---

#### POST `/api/v1/agents/initial-coding/code`
Perform initial coding on documents.

**Request**: `InitialCodingRequest`
- `documents`: Documents to code
- `research_domain`: Domain context

**Code Location**: `api/agents/initial_coding_agent.py`

---

#### POST `/api/v1/agents/thematic-grouping/group`
Group codes into themes.

**Request**: `ThematicGroupingRequest`
- `coded_units`: Coded document units
- `research_domain`: Domain context

**Code Location**: `api/agents/thematic_grouping_agent.py`

---

#### POST `/api/v1/agents/theme-refiner/refine`
Refine themes with academic polish.

**Request**: `ThemeRefinementRequest`
- `themes`: Themes to refine
- `research_domain`: Domain context

**Code Location**: `api/agents/theme_refiner_agent.py`

---

#### POST `/api/v1/agents/report-generator/generate`
Generate final academic report.

**Request**: `ReportGenerationRequest`
- `sections`: Pipeline sections to include

**Code Location**: `api/agents/report_generator_agent.py`

---

#### POST `/api/v1/agents/supervisor/check-quality`
Check quality of agent output.

**Request**: `SupervisorRequest`
- `agent_type`: Type of agent
- `agent_output`: Output to assess
- `original_agent_input`: Original input

**Code Location**: `api/agents/enhanced_supervisor_agent.py`

---

#### POST `/api/v1/agents/multi-source-extractor/extract`
Extract from multiple sources (OpenAlex, Europe PMC, arXiv, CORE).

**Request**: `MultiSourceExtractorRequest`
- `query`: Search query
- `sources`: List of sources
- `enrich`: Enrichment level (none, standard, deep)
- `store`: Whether to store in vector DB

**Code Location**: `api/agents/multi_source_data_extractor_agent.py`

---

### 3. Data Management Endpoints
**Base Path**: `/api/v1/data`  
**File**: `api/routes/data_routes.py`

#### GET `/api/v1/data/retrieve/{collection_name}`
Retrieve all documents from a collection.

**Code Location**: `api/services/data_service.py` - `retrieve_all_documents()`

---

#### POST `/api/v1/data/store`
Store documents in vector database.

**Request**: `DataRequest`
- `documents`: List of documents
- `collection_name`: Target collection
- `research_domain`: Domain classification

**Code Location**: `api/services/data_service.py` - `store_documents()`

---

#### GET `/api/v1/data/collections`
List all vector database collections.

**Code Location**: `api/services/data_service.py` - `list_collections()`

---

#### GET `/api/v1/data/collections/{collection_name}`
Get detailed information about a collection.

**Code Location**: `api/services/data_service.py` - `get_collection_info()`

---

#### DELETE `/api/v1/data/collections/{collection_name}`
Delete a collection and all its documents.

**Code Location**: `api/services/data_service.py` - `delete_collection()`

---

#### GET `/api/v1/data/statistics`
Get comprehensive data statistics.

**Code Location**: `api/services/data_service.py` - `get_data_statistics()`

---

### 4. Report Endpoints
**Base Path**: `/api/v1/reports`  
**File**: `api/routes/report_routes.py`

#### POST `/api/v1/reports/generate`
Generate a new academic report.

**Code Location**: `api/services/report_service.py` - `generate_report()`

---

#### GET `/api/v1/reports/`
List all generated reports.

**Code Location**: `api/services/report_service.py` - `list_reports()`

---

#### GET `/api/v1/reports/{report_id}`
Get detailed report information.

**Code Location**: `api/services/report_service.py` - `get_report_details()`

---

#### GET `/api/v1/reports/{report_id}/download`
Download report in specified format.

**Code Location**: `api/services/report_service.py` - `download_report()`

---

## RAG Implementation & Retrieval Methods

### What is RAG?
**RAG (Retrieval-Augmented Generation)** combines:
- **Retrieval**: Finding relevant documents from a knowledge base
- **Augmentation**: Adding retrieved context to prompts
- **Generation**: Using LLMs to generate responses with context

### Our RAG Flow

The system uses a sophisticated multi-stage retrieval pipeline to maximize accuracy:

```
User Query
    ↓
1. Vector Similarity Search (Wide Retrieval)
    ↓
2. Vector Distance Filtering
    ↓
3. Cross-Encoder Reranking
    ↓
4. Adaptive Threshold Filtering
    ↓
5. Paper-Level Diversification
    ↓
6. Quality Metrics Calculation
    ↓
7. Evidence Sufficiency Assessment
    ↓
Final Results
```

**Code Location**: `api/services/smart_retrieval_service.py` - `smart_retrieve_documents()`

---

### Retrieval Methods Explained

#### 1. Vector Similarity Search (Initial Retrieval)
**Purpose**: Find semantically similar documents using embeddings.

**How it works:**
- Converts query to embedding using OpenAI (text2vec-openai, ada model)
- Searches Weaviate vector database for similar embeddings
- Uses cosine similarity to rank candidates
- Retrieves 5x requested candidates (candidate_multiplier = 5)

**Example**: If requesting 10 docs, retrieves 50 candidates

**Code Location**: 
- `api/utils/vector_store_manager.py` - `similarity_search()`
- `api/services/smart_retrieval_service.py` - Line 282

**Configuration**:
- Embedding model: OpenAI ada
- Candidate multiplier: 5x
- Research domain filtering enabled

---

#### 2. Vector Distance Filtering
**Purpose**: Remove documents that are too dissimilar.

**How it works:**
- Weaviate returns distance scores (lower = more similar)
- Filters out documents with distance > 0.35
- Applied before expensive reranking

**Code Location**: 
- `api/agents/retriever_agent.py` - Lines 51-60
- `MAX_DISTANCE = 0.35` threshold

**Why it matters**: Reduces noise before reranking, saving computation.

---

#### 3. Cross-Encoder Reranking
**Purpose**: More accurate relevance scoring than vector similarity alone.

**How it works:**
- Uses `cross-encoder/ms-marco-MiniLM-L-6-v2` model
- Scores each query-document pair directly
- More accurate than bi-encoder (vector search) because it sees query and document together
- Normalizes scores to [0,1] using sigmoid if needed

**Code Location**: 
- `api/utils/reranking.py` - `CrossEncoderReranker.rerank_with_scores()`
- `api/services/retrieval_quality.py` - `attach_rerank_scores()`

**Model Details**:
- Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Requires: `sentence-transformers` and `torch`
- Graceful fallback if unavailable (returns 0.0 scores)

**Why it's better**: 
- Vector search: Fast but less accurate (compares embeddings separately)
- Cross-encoder: Slower but more accurate (compares query+document together)

---

#### 4. Adaptive Threshold Filtering
**Purpose**: Dynamically filter based on score distribution, not fixed thresholds.

**How it works:**
- Calculates score distribution statistics (min, max, mean, percentiles)
- Sets threshold at 60th percentile (keeps top 40% by default)
- Ensures minimum 8 results are kept even if scores are low
- Adapts to different query types and score distributions

**Code Location**: 
- `api/services/retrieval_quality.py` - `adaptive_rerank_threshold()`
- `api/services/retrieval_quality.py` - `filter_by_rerank_threshold()`

**Configuration**:
- `rerank_keep_percentile: 0.60` (60th percentile)
- `min_results_after_filter: 8` (minimum to keep)

**Why adaptive**: Different queries produce different score distributions. A fixed threshold would be too strict for some queries and too lenient for others.

---

#### 5. Paper-Level Diversification
**Purpose**: Ensure variety across papers, not just many chunks from one paper.

**How it works:**
- Groups chunks by paper (using DOI, title, or paper_id)
- Limits to 1 chunk per paper by default
- Selects best chunk per paper based on rerank score
- Ranks papers by their best chunk score

**Code Location**: 
- `api/services/retrieval_quality.py` - `diversify_by_paper()`
- `api/services/retrieval_quality.py` - `_paper_key()` (paper identification)

**Configuration**:
- `max_chunks_per_paper: 1` (default)
- `max_papers: max_results` (requested number)

**Why it matters**: Without this, you might get 20 chunks from the same paper, reducing diversity and coverage.

---

#### 6. Quality Metrics Calculation
**Purpose**: Multi-dimensional assessment of retrieval quality.

**Metrics Calculated:**

**a) Quantity Score**
- Ratio of results vs requested
- Formula: `min(1.0, len(results) / requested)`
- Target: 30% minimum

**b) Certainty Score**
- Average Weaviate certainty scores
- Range: 0.0 to 1.0
- Target: 0.7 minimum

**c) Recency Score**
- Percentage of recent documents (last 2 years)
- Formula: `recent_docs / total_docs`
- Target: 20% minimum

**d) Overall Score**
- Weighted average:
  - Quantity: 20%
  - Certainty: 50%
  - Recency: 30%

**Code Location**: 
- `api/services/smart_retrieval_service.py` - `_calculate_quality_metrics()`

---

#### 7. Evidence Sufficiency Assessment
**Purpose**: Validate that retrieved evidence is sufficient for downstream analysis.

**Checks Performed:**

**a) Unique Papers Count**
- Counts distinct papers (not just chunks)
- Compares to requested number
- Reported as flag (doesn't hard-fail)

**b) Average Rerank Score**
- Average of all rerank scores
- Target: 0.80 minimum
- Indicates overall relevance

**c) Results Count**
- Number of results after filtering
- Target: 8 minimum (or requested, whichever is smaller)

**d) Evidence OK Flag**
- Overall assessment: `ok = (count >= min) AND (avg_score >= 0.80)`
- Flags issues but allows pipeline to continue with warnings

**Code Location**: 
- `api/services/retrieval_quality.py` - `assess_evidence_sufficiency()`

**Configuration**:
- `min_avg_rerank_score: 0.80` (strong match threshold)
- `min_results_after_filter: 8` (minimum documents)

---

### Smart Fallback System

When retrieval quality is insufficient, the system automatically triggers fallback:

**Fallback Triggers:**
- Insufficient quantity (< 30% of requested)
- Low certainty scores (< 0.7)
- Few recent documents (< 20%)
- Low overall quality (< 0.6)
- Evidence sufficiency failure

**Fallback Actions:**
1. Multi-source extraction from:
   - OpenAlex
   - Europe PMC
   - arXiv
   - CORE API
2. Optional enrichment with:
   - Crossref (metadata)
   - Unpaywall (open access status)
   - Semantic Scholar (citations)
3. Re-query vector store after extraction
4. Merge and deduplicate results

**Code Location**: 
- `api/services/smart_retrieval_service.py` - `_should_fallback_to_core_api()`
- `api/services/smart_retrieval_service.py` - Lines 324-393

---

## Metrics & Quality Assessment

### Retrieval Quality Metrics

All metrics are calculated and returned in the retrieval response:

**Location**: `api/services/smart_retrieval_service.py` - `smart_retrieve_documents()`

**Response Structure:**
```json
{
  "quality_metrics": {
    "quantity_score": 0.95,
    "certainty_score": 0.82,
    "recency_score": 0.35,
    "overall_score": 0.71,
    "total_results": 19,
    "recent_results": 7,
    "avg_rerank_score": 0.85,
    "unique_papers": 15,
    "evidence_ok": true
  },
  "evidence_assessment": {
    "ok": true,
    "unique_papers": 15,
    "unique_papers_goal": 20,
    "meets_unique_papers_goal": false,
    "results_count": 19,
    "avg_rerank_score": 0.85,
    "requested": 20,
    "flags": ["unique_papers_below_requested:15<20"],
    "thresholds": {
      "min_unique_papers": 0,
      "min_results_after_filter": 8,
      "min_avg_rerank_score": 0.80
    }
  }
}
```

---

### Quality Service Metrics

**Location**: `api/services/quality_service.py`

**Agent Quality Thresholds:**
- Literature Review: min_score 0.6, halt_threshold 0.3
- Initial Coding: min_score 0.6, halt_threshold 0.3
- Thematic Grouping: min_score 0.6, halt_threshold 0.3
- Theme Refinement: min_score 0.6, halt_threshold 0.3
- Report Generation: min_score 0.7, halt_threshold 0.4

**Actions Based on Scores:**
- **APPROVE**: Score >= min_score (proceed)
- **REVISE**: Score >= halt_threshold but < min_score (warning)
- **HALT**: Score < halt_threshold (stop pipeline)

---

### Pipeline Metrics

**Location**: `api/services/pipeline_service.py` - `get_pipeline_statistics()`

**Metrics Tracked:**
- Total pipelines
- Completed vs failed
- Success rate
- Average processing time
- Quality score trends
- Research domain distribution

---

## Pipeline Flow

### Full Pipeline Flow

**Location**: `api/services/pipeline_service.py` - `run_full_pipeline()`

```
1. Early Academic Validation
   ↓ (if not academic, stop)
2. Document Retrieval
   ↓ (if empty, trigger extraction fallback)
3. Retrieval Validation
   ↓ (if not related, trigger extraction fallback)
4. Literature Review
   ↓ (optional supervisor check)
5. Initial Coding
   ↓ (optional supervisor check)
6. Thematic Grouping
   ↓ (optional supervisor check)
7. Theme Refinement
   ↓ (optional supervisor check)
8. Report Generation
   ↓ (optional supervisor check)
9. Finalize Pipeline
```

---

### Lite Pipeline Flow

**Location**: `api/services/pipeline_service.py` - `run_lite_pipeline()`

```
1. Early Academic Validation
   ↓
2. Document Retrieval
   ↓
3. Retrieval Validation
   ↓
4. Literature Review
   ↓
5. Report Generation
   ↓
6. Finalize Pipeline
```

---

### Document Retrieval Flow (Detailed)

**Location**: `api/services/data_service.py` - `retrieve_documents()`

```
1. Smart Retrieval Service Called
   ↓
2. Initialize Vector Store
   ↓
3. Wide Candidate Retrieval (5x multiplier)
   ↓
4. Cross-Encoder Reranking
   ↓
5. Adaptive Threshold Filtering
   ↓
6. Paper-Level Diversification
   ↓
7. Quality Metrics Calculation
   ↓
8. Evidence Sufficiency Assessment
   ↓
9. Fallback Decision
   ↓ (if needed)
10. Multi-Source Extraction
   ↓
11. Re-query Vector Store
   ↓
12. Merge Results
   ↓
13. Final Quality Assessment
   ↓
14. Return Results
```

---

## Code References

### Core Services

| Component | File Location | Key Methods |
|-----------|---------------|-------------|
| Pipeline Service | `api/services/pipeline_service.py` | `run_full_pipeline()`, `run_lite_pipeline()`, `get_pipeline_progress()` |
| Smart Retrieval | `api/services/smart_retrieval_service.py` | `smart_retrieve_documents()`, `_calculate_quality_metrics()` |
| Data Service | `api/services/data_service.py` | `retrieve_documents()`, `store_documents()` |
| Quality Service | `api/services/quality_service.py` | `check_quality()`, `assess_quality()` |
| Agent Service | `api/services/agent_service.py` | Agent orchestration methods |

### Retrieval Components

| Component | File Location | Key Functions |
|-----------|---------------|---------------|
| Retrieval Quality | `api/services/retrieval_quality.py` | `adaptive_rerank_threshold()`, `diversify_by_paper()`, `assess_evidence_sufficiency()` |
| Cross-Encoder Reranker | `api/utils/reranking.py` | `CrossEncoderReranker.rerank_with_scores()`, `is_available()` |
| Vector Store Manager | `api/utils/vector_store_manager.py` | `similarity_search()`, `add_chunks()` |
| Weaviate Client | `api/utils/weaviate_client.py` | `search_documents()`, `insert_documents()` |

### Agents

| Agent | File Location | Key Method |
|-------|---------------|------------|
| Retriever Agent | `api/agents/retriever_agent.py` | `run()` |
| Data Extractor | `api/agents/data_extractor_agent.py` | `run()` |
| Multi-Source Extractor | `api/agents/multi_source_data_extractor_agent.py` | `run()` |
| Literature Review | `api/agents/literature_review_agent.py` | `run()` |
| Initial Coding | `api/agents/initial_coding_agent.py` | `run()` |
| Thematic Grouping | `api/agents/thematic_grouping_agent.py` | `run()` |
| Theme Refiner | `api/agents/theme_refiner_agent.py` | `run()` |
| Report Generator | `api/agents/report_generator_agent.py` | `run()` |
| Supervisor | `api/agents/enhanced_supervisor_agent.py` | `evaluate_quality()` |

### Routes

| Route Group | File Location | Endpoints |
|-------------|---------------|-----------|
| Pipeline Routes | `api/routes/pipeline_routes.py` | `/api/v1/pipelines/*` |
| Agent Routes | `api/routes/agent_routes.py` | `/api/v1/agents/*` |
| Data Routes | `api/routes/data_routes.py` | `/api/v1/data/*` |
| Report Routes | `api/routes/report_routes.py` | `/api/v1/reports/*` |

### Configuration

| Config | File Location | Key Settings |
|--------|---------------|--------------|
| Retrieval Quality Config | `api/services/retrieval_quality.py` | `RetrievalQualityConfig` class |
| Quality Thresholds | `api/services/quality_service.py` | `quality_thresholds` dict |
| Smart Retrieval Thresholds | `api/services/smart_retrieval_service.py` | `quality_thresholds` dict |

---

## Key Configuration Values

### Retrieval Quality Configuration
**Location**: `api/services/retrieval_quality.py` - `RetrievalQualityConfig`

```python
candidate_multiplier: 5              # Retrieve 5x candidates
min_results_after_filter: 8           # Minimum docs to keep
min_avg_rerank_score: 0.80            # Strong match threshold
rerank_keep_percentile: 0.60          # Keep top 40% by score
max_chunks_per_paper: 1               # Diversification limit
```

### Quality Thresholds
**Location**: `api/services/smart_retrieval_service.py`

```python
min_quantity_ratio: 0.3               # 30% of requested minimum
min_certainty_score: 0.7              # Weaviate certainty minimum
min_relevance_score: 0.6              # Reranking score minimum
min_recent_ratio: 0.2                 # 20% recent docs minimum
max_years_old: 2                      # "Recent" = last 2 years
```

### Vector Distance Threshold
**Location**: `api/agents/retriever_agent.py`

```python
MAX_DISTANCE: 0.35                    # Maximum vector distance
```

---

## Summary

The AI Researcher backend implements a sophisticated RAG system with:

1. **8 Retrieval Methods** working together:
   - Vector similarity search
   - Distance filtering
   - Cross-encoder reranking
   - Adaptive thresholding
   - Paper diversification
   - Quality metrics
   - Evidence assessment
   - Smart fallback

2. **Comprehensive API** with 4 main route groups:
   - Pipelines (orchestration)
   - Agents (individual operations)
   - Data (vector database)
   - Reports (generation)

3. **Multi-dimensional Quality Assessment**:
   - Quantity, certainty, recency scores
   - Evidence sufficiency checks
   - Supervisor agent validation

4. **Intelligent Fallback System**:
   - Automatic multi-source extraction
   - Re-query and merge
   - Quality-driven decisions

This architecture ensures high retrieval accuracy through multiple validation layers and adaptive filtering strategies.

