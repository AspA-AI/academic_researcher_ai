# Agent Specifications - Detailed

## Overview

This document provides detailed specifications for each agent in the B2B AI Research Automation Platform. Each agent is designed to perform a specific task in the research pipeline, with clear inputs, outputs, and implementation requirements.

## 1. Research & Ingestion Agent

### 1.1 Purpose
Fetches research content from external sources, processes it, and stores it in the Weaviate vector database for subsequent analysis.

### 1.2 Responsibilities

1. **Multi-Source Content Fetching**:
   - Query CoreAPI for academic papers
   - Query arXiv for preprints
   - Query OpenAlex for academic metadata
   - Query Europe PMC for biomedical literature
   - Query Google Custom Search (optional) for web content

2. **Data Cleaning & Normalization**:
   - Remove duplicate documents (by DOI, title hash)
   - Normalize author names
   - Standardize date formats
   - Clean HTML/markup from content

3. **Document Chunking**:
   - Split large documents into chunks (500-1000 tokens)
   - Maintain chunk overlap (200 tokens) for context preservation
   - Preserve metadata (title, authors, year, DOI) with each chunk

4. **Embedding Generation**:
   - Generate embeddings using OpenAI `text-embedding-3-small`
   - Batch process embeddings for efficiency
   - Store embeddings with document chunks

5. **Vector Store Storage**:
   - Create/use Weaviate collection: `{ResearchPaper}_{research_domain}`
   - Store documents with metadata
   - Index for semantic search

### 1.3 Input Schema

```python
class ResearchIngestionInput(BaseModel):
    query: str
    date_range: DateRange
    authors: Optional[List[str]] = None
    sources: List[str]  # ["core", "arxiv", "openalex", "europe_pmc", "google"]
    max_results: int = 30
    research_domain: str
    language: str = "en"
    oa_only: bool = True
    full_text: bool = False
```

### 1.4 Output Schema

```python
class ResearchIngestionOutput(BaseModel):
    status: Literal["success", "partial", "failed"]
    documents_retrieved: int
    documents_stored: int
    chunks_created: int
    collection_name: str
    sources_queried: List[str]
    sources_successful: List[str]
    sources_failed: List[str]
    retrieval_time: datetime
    errors: Optional[List[str]] = None
```

### 1.5 Implementation Details

**Dependencies**:
- `MultiSourceDataExtractorAgent` (existing)
- `VectorStoreManager` (existing)
- `WeaviateClient` (existing)

**Chunking Strategy**:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

**Embedding Model**:
- Model: `text-embedding-3-small`
- Dimensions: 1536
- Batch size: 100

**Error Handling**:
- Retry failed API calls (max 3 attempts)
- Continue with successful sources if some fail
- Log all errors for debugging

### 1.6 Performance Targets
- Retrieve 30 documents: < 30 seconds
- Process and store: < 15 seconds
- Total: < 45 seconds

## 2. Retriever Logic Agent

### 2.1 Purpose
Performs semantic similarity search in Weaviate to retrieve relevant documents based on queries.

### 2.2 Responsibilities

1. **Semantic Search**:
   - Convert query to embedding
   - Perform `nearText` search in Weaviate
   - Apply certainty threshold (default: 0.7)

2. **Reranking** (Optional):
   - Use cross-encoder model for reranking
   - Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
   - Improve relevance ordering

3. **Filtering**:
   - Filter by year range
   - Filter by authors
   - Filter by source
   - Filter by research domain

4. **Provenance Verification**:
   - Verify document metadata
   - Ensure citations are valid
   - Check document completeness

### 2.3 Input Schema

```python
class RetrieverInput(BaseModel):
    query: str
    top_k: int = 10
    research_domain: str
    collection_name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    certainty_threshold: float = 0.7
    use_reranking: bool = False
```

### 2.4 Output Schema

```python
class RetrieverOutput(BaseModel):
    status: Literal["success", "failed"]
    documents: List[Document]
    total_found: int
    search_time_ms: int
    reranked: bool = False
```

### 2.5 Implementation Details

**Weaviate Query**:
```python
query = {
    "query": {
        "nearText": {
            "concepts": [query],
            "certainty": certainty_threshold
        }
    },
    "where": {
        "path": ["research_domain"],
        "operator": "Equal",
        "valueString": research_domain
    },
    "limit": top_k
}
```

**Reranking** (if enabled):
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = reranker.predict([(query, doc.content) for doc in documents])
ranked_indices = np.argsort(scores)[::-1]
```

### 2.6 Performance Targets
- Semantic search: < 200ms
- Reranking (if enabled): < 500ms
- Total: < 1 second

## 3. Initial Coding Agent

### 3.1 Purpose
Performs open coding on academic texts, breaking content into meaningful units and assigning descriptive codes with citations.

### 3.2 Responsibilities

1. **Document Segmentation**:
   - Split documents into meaningful units (sentences/paragraphs)
   - Preserve context around each unit
   - Maintain document structure

2. **Code Assignment**:
   - Assign descriptive codes to each unit
   - Use GPT-4-turbo for intelligent coding
   - Maintain code consistency across units

3. **Code Dictionary Management**:
   - Build code dictionary with definitions
   - Track code frequency
   - Identify code relationships

4. **Citation Generation**:
   - Generate Harvard-style citations
   - Format: `Author, Year. Title. DOI: xxxxx`
   - Link citations to source documents

5. **Confidence Scoring**:
   - Assign confidence scores (0.0-1.0)
   - Based on code clarity and consistency
   - Flag low-confidence codes for review

### 3.3 Input Schema

```python
class InitialCodingInput(BaseModel):
    documents: List[Document]
    research_domain: str
    research_question: Optional[str] = None
    supervisor_feedback: Optional[str] = None
    previous_attempts: Optional[List[Dict]] = None
```

### 3.4 Output Schema

```python
class CodedUnit(BaseModel):
    unit_id: str
    text: str
    code: str
    code_definition: str
    confidence: float
    citation: Citation
    source_document_id: str
    chunk_index: int

class CodeDictionary(BaseModel):
    code: str
    definition: str
    frequency: int
    examples: List[str]
    related_codes: List[str]

class InitialCodingOutput(BaseModel):
    status: Literal["success", "partial", "failed"]
    coded_units: List[CodedUnit]
    code_dictionary: Dict[str, CodeDictionary]
    total_units_coded: int
    unique_codes: int
    average_confidence: float
    errors: Optional[List[str]] = None
```

### 3.5 Implementation Details

**LLM Prompt Template**:
```
You are an expert qualitative researcher performing open coding on academic texts.

Research Domain: {research_domain}
Research Question: {research_question}

Documents to Code:
{document_texts}

Instructions:
1. Segment each document into meaningful units (sentences or paragraphs)
2. Assign a descriptive code to each unit
3. Provide a clear definition for each code
4. Generate Harvard-style citations for each unit
5. Assign confidence scores (0.0-1.0)

Output Format (JSON):
{
  "coded_units": [
    {
      "unit_id": "unit_001",
      "text": "...",
      "code": "CODE_NAME",
      "code_definition": "...",
      "confidence": 0.92,
      "citation": {
        "author": "Author Name",
        "year": 2024,
        "title": "Paper Title",
        "doi": "10.1234/example",
        "harvard_format": "Author Name (2024) Paper Title. DOI: 10.1234/example"
      }
    }
  ],
  "code_dictionary": {
    "CODE_NAME": {
      "definition": "...",
      "frequency": 5,
      "examples": ["unit_001", "unit_045"]
    }
  }
}
```

**LLM Configuration**:
- Model: `gpt-4-turbo-preview`
- Temperature: 0.3 (for consistency)
- Max tokens: 4000
- Response format: JSON

### 3.6 Performance Targets
- Code 150 units: < 5 minutes
- Average processing time per unit: < 2 seconds

## 4. Thematic Grouping Agent

### 4.1 Purpose
Clusters individual codes into broader conceptual themes with justifications and cross-cutting ideas.

### 4.2 Responsibilities

1. **Code Analysis**:
   - Analyze code relationships
   - Identify semantic similarities
   - Map code co-occurrences

2. **Theme Formation**:
   - Group related codes into themes
   - Ensure theme distinctness (cosine similarity < 0.7)
   - Create theme names and descriptions

3. **Justification Generation**:
   - Provide rationale for code groupings
   - Explain theme coherence
   - Identify supporting evidence

4. **Cross-Cutting Identification**:
   - Find codes that span multiple themes
   - Identify overarching concepts
   - Document inter-theme relationships

5. **Illustrative Quote Selection**:
   - Select representative quotes for each theme
   - Include citations with quotes
   - Ensure quote diversity

### 4.3 Input Schema

```python
class ThematicGroupingInput(BaseModel):
    coded_units: List[CodedUnit]
    code_dictionary: Dict[str, CodeDictionary]
    research_domain: str
    min_codes_per_theme: int = 2
    max_themes: Optional[int] = None
```

### 4.4 Output Schema

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

class ThematicGroupingOutput(BaseModel):
    status: Literal["success", "partial", "failed"]
    themes: List[Theme]
    total_themes: int
    codes_grouped: int
    ungrouped_codes: List[str]
    cross_cutting_codes: List[str]
    errors: Optional[List[str]] = None
```

### 4.5 Implementation Details

**LLM Prompt Template**:
```
You are an expert qualitative researcher performing thematic analysis.

Research Domain: {research_domain}
Coded Units: {coded_units}
Code Dictionary: {code_dictionary}

Instructions:
1. Analyze the codes and identify relationships
2. Group related codes into themes (minimum 2 codes per theme)
3. Ensure themes are distinct and non-overlapping
4. Provide clear justifications for each theme
5. Identify cross-cutting ideas that span multiple themes
6. Select illustrative quotes for each theme

Output Format (JSON):
{
  "themes": [
    {
      "theme_id": "theme_001",
      "theme_name": "Theme Name",
      "description": "Theme description...",
      "codes_included": ["CODE1", "CODE2"],
      "justification": "These codes are grouped because...",
      "illustrative_quotes": [
        {
          "text": "Quote text...",
          "citation": "Author (Year)...",
          "code": "CODE1"
        }
      ],
      "cross_cutting_ideas": ["Idea 1", "Idea 2"],
      "theme_confidence": 0.88
    }
  ],
  "ungrouped_codes": ["CODE_X"],
  "cross_cutting_codes": ["CODE_Y"]
}
```

**Theme Validation**:
- Check theme distinctness using cosine similarity
- Ensure minimum codes per theme
- Validate theme coherence

### 4.6 Performance Targets
- Group 25 codes into themes: < 3 minutes
- Average processing time: < 7 seconds per theme

## 5. Validation & Refinement Agent

### 5.1 Purpose
Reviews and refines thematic outputs for coherence, completeness, and academic polish.

### 5.2 Responsibilities

1. **Coherence Review**:
   - Check theme logical consistency
   - Verify theme descriptions match codes
   - Identify contradictions

2. **Completeness Check**:
   - Ensure all critical themes included
   - Verify no important codes missed
   - Check coverage of research question

3. **Label Refinement**:
   - Improve unclear theme names
   - Refine section names
   - Enhance descriptions

4. **Academic Polish**:
   - Refine theme definitions
   - Define scope boundaries
   - Add theoretical frameworks
   - Identify key concepts

5. **Citation Enhancement**:
   - Add supporting academic quotes
   - Ensure proper citation format
   - Verify quote relevance

6. **Implications Analysis**:
   - Describe research implications
   - Identify future research directions
   - Highlight practical applications

### 5.3 Input Schema

```python
class ValidationRefinementInput(BaseModel):
    themes: List[Theme]
    coded_units: List[CodedUnit]
    research_question: str
    research_domain: str
    refinement_level: Literal["basic", "comprehensive"] = "comprehensive"
```

### 5.4 Output Schema

```python
class RefinedTheme(BaseModel):
    theme_id: str
    theme_name: str
    precise_definition: str
    scope: Dict[str, List[str]]  # {"included": [...], "excluded": [...]}
    supporting_quotes: List[Dict[str, Any]]
    key_concepts: List[str]
    theoretical_frameworks: List[str]
    research_implications: List[str]
    validation_status: Literal["approved", "refined", "rejected"]

class ValidationSummary(BaseModel):
    themes_reviewed: int
    themes_approved: int
    themes_refined: int
    themes_rejected: int
    overall_quality_score: float
    recommendations: List[str]

class ValidationRefinementOutput(BaseModel):
    status: Literal["success", "partial", "failed"]
    refined_themes: List[RefinedTheme]
    validation_summary: ValidationSummary
    errors: Optional[List[str]] = None
```

### 5.5 Implementation Details

**LLM Prompt Template**:
```
You are an expert academic reviewer validating and refining thematic analysis.

Research Question: {research_question}
Research Domain: {research_domain}
Themes to Review: {themes}
Coded Units: {coded_units}

Instructions:
1. Review each theme for coherence and completeness
2. Refine theme names, definitions, and scope
3. Add supporting academic quotes with proper citations
4. Identify key concepts and theoretical frameworks
5. Describe research implications
6. Provide quality scores and recommendations

Output Format (JSON):
{
  "refined_themes": [
    {
      "theme_id": "theme_001",
      "theme_name": "Refined Theme Name",
      "precise_definition": "Detailed definition...",
      "scope": {
        "included": ["Concept 1", "Concept 2"],
        "excluded": ["Concept 3"]
      },
      "supporting_quotes": [
        {
          "quote": "Quote text...",
          "citation": "Author (Year)...",
          "relevance": "high"
        }
      ],
      "key_concepts": ["Concept 1", "Concept 2"],
      "theoretical_frameworks": ["Framework 1"],
      "research_implications": ["Implication 1"],
      "validation_status": "approved"
    }
  ],
  "validation_summary": {
    "themes_reviewed": 8,
    "themes_approved": 7,
    "themes_refined": 1,
    "themes_rejected": 0,
    "overall_quality_score": 0.91,
    "recommendations": ["Recommendation 1"]
  }
}
```

**Quality Criteria**:
- Coherence: 0.3 weight
- Completeness: 0.3 weight
- Academic rigor: 0.2 weight
- Citation quality: 0.2 weight

### 5.6 Performance Targets
- Validate 8 themes: < 2 minutes
- Average processing time: < 15 seconds per theme

## 6. Report Generation Agent

### 6.1 Purpose
Assembles all agent outputs into a single **canonical JSON report payload** (JSON-first MVP).

### 6.2 Responsibilities

1. **Content Assembly**:
   - Combine literature review, coding, and themes
   - Structure content into academic paper format
   - Ensure logical flow and coherence

2. **Section Generation**:
   - **Title Page**: Research title, date, author info
   - **Abstract**: Summary of research and findings
   - **Introduction**: Research context and objectives
   - **Methodology**: Research approach and methods
   - **Findings**: Themes with supporting evidence
   - **Discussion**: Interpretation and implications
   - **Conclusion**: Summary and future directions
   - **References**: Harvard-style bibliography

3. **Citation Formatting**:
   - Format all citations in Harvard style
   - Create reference list
   - Ensure citation consistency

4. **JSON-first Output**:
   - Output strict JSON (no markdown fences) for downstream renderers
   - Include structured sections + themes + citations + metadata
   - Optionally include a markdown preview string for quick UI display (non-canonical)

### 6.3 Input Schema

```python
class ReportGenerationInput(BaseModel):
    literature_review: Dict[str, Any]
    coded_units: List[CodedUnit]
    themes: List[RefinedTheme]
    research_question: str
    research_domain: str
    output_format: Literal["json"] = "json"
    report_title: Optional[str] = None
```

### 6.4 Output Schema

```python
class ReportGenerationOutput(BaseModel):
    status: Literal["success", "failed"]
    report: Dict[str, Any]          # canonical structured report object
    rendered: Optional[Dict[str, Any]] = None  # e.g., {"markdown": "..."} for preview
    report_summary: Dict[str, Any]  # counts/metadata (themes_count, references_count, etc.)
    created_at: datetime
    errors: Optional[List[str]] = None
```

### 6.5 Implementation Details

The Report Generation Agent produces a canonical JSON payload that is stable across output formats.
Post-MVP, separate renderers will consume this JSON to produce PDF/PPTX/DOCX/HTML using templates.

### 6.6 Performance Targets
- Generate report content: < 1 minute
- JSON parse/validation: < 1 second
- Total report step: < 1 minute

## 7. Agent Orchestration

### 7.1 Pipeline Flow

```
1. Research & Ingestion Agent
   ↓
2. Retriever Logic Agent
   ↓
3. Initial Coding Agent
   ↓
4. Thematic Grouping Agent
   ↓
5. Validation & Refinement Agent
   ↓
6. Report Generation Agent
```

### 7.2 Error Handling

- **Agent Failure**: Retry up to 3 times
- **Partial Success**: Continue with available data
- **Critical Failure**: Stop pipeline, return error

### 7.3 State Management

- Store intermediate results after each agent
- Enable pipeline resumption from any step
- Log all agent executions

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15

