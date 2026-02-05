# Implementation Plan

## Overview

This document outlines the implementation plan for the B2B AI Research Automation Platform. The plan is organized into phases, with clear dependencies, priorities, and acceptance criteria.

## Implementation Phases

### Phase 1: Foundation & Infrastructure (Week 1-2)

#### 1.1 Environment Setup
**Priority**: Critical  
**Dependencies**: None  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Set up development environment
- [ ] Configure environment variables (.env)
- [ ] Set up Weaviate connection (cloud or local)
- [ ] Configure OpenAI API access
- [ ] Install and configure all dependencies

**Acceptance Criteria**:
- All services (Weaviate, OpenAI) are accessible
- Environment variables are properly configured
- Dependencies are installed and tested

**Files to Create/Modify**:
- `.env.example`
- `requirements.txt` (update if needed)
- `config/settings.py`

#### 1.2 Output Contract (JSON-first)
**Priority**: Critical  
**Dependencies**: 1.1  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Define canonical JSON schema for final report output (sections, themes, citations, metadata)
- [ ] Update Report Generator prompt to emit strict JSON only
- [ ] Implement robust JSON parsing/validation in Report Generator agent
- [ ] Add unit tests to validate each agent output shape without real LLM calls

**Acceptance Criteria**:
- Pipeline produces a canonical JSON report payload at the final step
- Unit tests validate each agent produces the expected keys/shape
- No Google Drive/OAuth dependency is required for MVP

**Files to Create/Modify**:
- `api/agents/report_generator_agent.py`
- `specs/SPEC.md`
- `specs/API_CONTRACTS.md`
- `api/tests/test_agents_json.py`

#### 1.3 Enhanced Vector Store Manager
**Priority**: Critical  
**Dependencies**: 1.1  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Review existing `VectorStoreManager`
- [ ] Enhance with collection management
- [ ] Add document filtering capabilities
- [ ] Implement batch operations
- [ ] Add error handling and retries

**Acceptance Criteria**:
- Can create/delete collections
- Can store documents with metadata
- Can retrieve documents with filters
- Proper error handling

**Files to Modify**:
- `api/utils/vector_store_manager.py`
- `api/utils/weaviate_client.py`

### Phase 2: Core Agents Implementation (Week 3-4)

#### 2.1 Research & Ingestion Agent Enhancement
**Priority**: Critical  
**Dependencies**: 1.1, 1.3  
**Estimated Time**: 3 days

**Tasks**:
- [ ] Review existing `MultiSourceDataExtractorAgent`
- [ ] Enhance with additional sources (if needed)
- [ ] Implement document chunking with overlap
- [ ] Integrate embedding generation
- [ ] Connect to Weaviate storage
- [ ] Add comprehensive error handling

**Acceptance Criteria**:
- Can fetch from all specified sources
- Documents are properly chunked
- Embeddings are generated and stored
- All documents stored in Weaviate
- Error handling for failed sources

**Files to Modify**:
- `api/agents/multi_source_data_extractor_agent.py`
- `api/services/data_service.py`

#### 2.2 Retriever Logic Agent
**Priority**: Critical  
**Dependencies**: 1.3  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Review existing `RetrieverAgent`
- [ ] Implement semantic search with Weaviate
- [ ] Add optional reranking with cross-encoder
- [ ] Implement filtering (year, authors, source)
- [ ] Add provenance verification
- [ ] Optimize query performance

**Acceptance Criteria**:
- Can perform semantic search
- Results are ranked by relevance
- Filters work correctly
- Provenance is verified
- Query time < 1 second

**Files to Modify**:
- `api/agents/retriever_agent.py`
- `api/services/data_service.py`

#### 2.3 Initial Coding Agent Enhancement
**Priority**: Critical  
**Dependencies**: 2.2  
**Estimated Time**: 4 days

**Tasks**:
- [ ] Review existing `InitialCodingAgent`
- [ ] Enhance code assignment logic
- [ ] Implement code dictionary management
- [ ] Add Harvard-style citation generation
- [ ] Implement confidence scoring
- [ ] Add supervisor feedback integration

**Acceptance Criteria**:
- Codes are assigned consistently
- Code dictionary is maintained
- Citations are in Harvard format
- Confidence scores are accurate
- Can handle supervisor feedback

**Files to Modify**:
- `api/agents/initial_coding_agent.py`
- `api/utils/citation_formatter.py` (new)

#### 2.4 Thematic Grouping Agent
**Priority**: Critical  
**Dependencies**: 2.3  
**Estimated Time**: 3 days

**Tasks**:
- [ ] Review existing thematic grouping logic (if any)
- [ ] Implement code relationship analysis
- [ ] Create theme formation algorithm
- [ ] Add theme distinctness validation
- [ ] Implement cross-cutting identification
- [ ] Add illustrative quote selection

**Acceptance Criteria**:
- Themes are logically grouped
- Themes are distinct (similarity < 0.7)
- Cross-cutting ideas are identified
- Illustrative quotes are selected
- All codes are accounted for

**Files to Create/Modify**:
- `api/agents/thematic_grouping_agent.py`
- `api/utils/theme_validator.py` (new)

#### 2.5 Validation & Refinement Agent
**Priority**: High  
**Dependencies**: 2.4  
**Estimated Time**: 3 days

**Tasks**:
- [ ] Implement coherence review logic
- [ ] Add completeness checking
- [ ] Create label refinement system
- [ ] Implement academic polish features
- [ ] Add citation enhancement
- [ ] Create implications analysis

**Acceptance Criteria**:
- Themes are validated for coherence
- Completeness is checked
- Labels are refined
- Academic polish is applied
- Citations are enhanced
- Implications are identified

**Files to Create**:
- `api/agents/validation_refinement_agent.py`
- `api/utils/quality_scorer.py` (new)

#### 2.6 Report Generation Agent
**Priority**: Critical  
**Dependencies**: 1.2, 2.5  
**Estimated Time**: 5 days

**Tasks**:
- [ ] Implement content assembly logic
- [ ] Create section templates (Docs and Slides)
- [ ] Implement Harvard citation formatting
- [ ] Integrate Google Docs API
- [ ] Integrate Google Slides API
- [ ] Add file permission management
- [ ] Implement error handling

**Acceptance Criteria**:
- Can generate Google Docs reports
- Can generate Google Slides reports
- All sections are properly formatted
- Citations are in Harvard style
- Files are saved to user's Drive
- Proper error handling

**Files to Create**:
- `api/agents/report_generator_agent.py`
- `api/utils/report_templates.py` (new)
- `api/utils/citation_formatter.py` (enhance)

### Phase 3: Pipeline Orchestration (Week 5)

#### 3.1 Pipeline Service Enhancement
**Priority**: Critical  
**Dependencies**: All Phase 2 agents  
**Estimated Time**: 4 days

**Tasks**:
- [ ] Review existing `PipelineService`
- [ ] Integrate all 6 agents in sequence
- [ ] Implement state management
- [ ] Add progress tracking
- [ ] Implement error handling and retries
- [ ] Add pipeline persistence

**Acceptance Criteria**:
- All agents execute in correct order
- State is properly managed
- Progress is tracked accurately
- Errors are handled gracefully
- Pipeline can be resumed

**Files to Modify**:
- `api/services/pipeline_service.py`
- `api/models/pipeline_models.py`

#### 3.2 API Endpoints
**Priority**: Critical  
**Dependencies**: 3.1  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Review existing pipeline routes
- [ ] Add new endpoints if needed
- [ ] Implement request validation
- [ ] Add response formatting
- [ ] Implement error responses
- [ ] Add API documentation

**Acceptance Criteria**:
- All endpoints are functional
- Request validation works
- Responses are properly formatted
- Error handling is consistent
- API docs are up to date

**Files to Modify**:
- `api/routes/pipeline_routes.py`
- `api/routes/report_routes.py`
- `api/models/responses.py`

### Phase 4: Testing & Quality Assurance (Week 6)

#### 4.1 Unit Tests
**Priority**: High  
**Dependencies**: All previous phases  
**Estimated Time**: 3 days

**Tasks**:
- [ ] Write unit tests for each agent
- [ ] Test vector store operations
- [ ] Test citation formatting
- [ ] Test error handling

**Acceptance Criteria**:
- All agents have unit tests
- Test coverage > 80%
- All tests pass

**Files to Create**:
- `tests/test_research_ingestion_agent.py`
- `tests/test_retriever_agent.py`
- `tests/test_initial_coding_agent.py`
- `tests/test_thematic_grouping_agent.py`
- `tests/test_validation_refinement_agent.py`
- `tests/test_report_generator_agent.py`
- `tests/test_google_drive_service.py`
- `tests/test_pipeline_service.py`

#### 4.2 Integration Tests
**Priority**: High  
**Dependencies**: 4.1  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Test full pipeline end-to-end
- [ ] Test agent interactions
- [ ] Test final JSON report payload generation (structure + required fields)
- [ ] Test error recovery
- [ ] Test concurrent pipelines

**Acceptance Criteria**:
- Full pipeline completes successfully
- All agents work together
- Final report JSON payload is generated
- Error recovery works
- Concurrent pipelines work

**Files to Create**:
- `tests/test_full_pipeline.py`
- `tests/test_concurrent_pipelines.py`

#### 4.3 Performance Testing
**Priority**: Medium  
**Dependencies**: 4.2  
**Estimated Time**: 1 day

**Tasks**:
- [ ] Test pipeline performance
- [ ] Measure agent execution times
- [ ] Test with large document sets
- [ ] Optimize slow operations

**Acceptance Criteria**:
- Pipeline completes in < 15 minutes
- All agents meet performance targets
- System handles 30+ documents

### Phase 5: Documentation & Deployment (Week 7)

#### 5.1 Documentation
**Priority**: High  
**Dependencies**: All phases  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Update API documentation
- [ ] Create user guide
- [ ] Document agent configurations
- [ ] Create deployment guide
- [ ] Add code comments

**Acceptance Criteria**:
- All documentation is complete
- API docs are accurate
- User guide is clear

**Files to Create/Modify**:
- `README.md`
- `docs/API.md`
- `docs/USER_GUIDE.md`
- `docs/DEPLOYMENT.md`

#### 5.2 Deployment Preparation
**Priority**: High  
**Dependencies**: 4.3  
**Estimated Time**: 2 days

**Tasks**:
- [ ] Set up production environment
- [ ] Configure production Weaviate
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Set up error tracking

**Acceptance Criteria**:
- Production environment is ready
- Monitoring is configured
- Logging is comprehensive

## Implementation Details

### Technology Stack Confirmation

**Backend**:
- FastAPI (Python 3.10+)
- LangChain & LangChain OpenAI
- Weaviate Client (v4.0+)
- OpenAI API (GPT-4, Embeddings)
- aiohttp (async HTTP client)

**Vector Database**:
- Weaviate (cloud or self-hosted)
- OpenAI embeddings (text-embedding-3-small)

**External APIs**:
- CORE API
- OpenAlex API
- Europe PMC API
- arXiv API
- Google Custom Search API (optional)

### Key Dependencies

```
Phase 1 (Foundation)
  ├── Environment Setup
  ├── Output Contract (JSON-first)
  └── Vector Store Manager

Phase 2 (Agents)
  ├── Research & Ingestion (depends on: Vector Store)
  ├── Retriever Logic (depends on: Vector Store)
  ├── Initial Coding (depends on: Retriever)
  ├── Thematic Grouping (depends on: Initial Coding)
  ├── Validation & Refinement (depends on: Thematic Grouping)
  └── Report Generation (depends on: Validation, JSON contract)

Phase 3 (Orchestration)
  └── Pipeline Service (depends on: All Agents)

Phase 4 (Testing)
  └── All Tests (depends on: All Previous)

Phase 5 (Deployment)
  └── Documentation & Deployment (depends on: All Previous)
```

### File Structure

```
waga-academy-ai-assistant/
├── ragbackend/
│   ├── api/
│   │   ├── agents/
│   │   │   ├── multi_source_data_extractor_agent.py (enhance)
│   │   │   ├── retriever_agent.py (enhance)
│   │   │   ├── initial_coding_agent.py (enhance)
│   │   │   ├── thematic_grouping_agent.py (create/enhance)
│   │   │   ├── validation_refinement_agent.py (create)
│   │   │   └── report_generator_agent.py (create)
│   │   ├── services/
│   │   │   ├── pipeline_service.py (enhance)
│   │   │   ├── data_service.py (enhance)
│   │   │   ├── google_drive_service.py (create)
│   │   │   └── agent_service.py (enhance)
│   │   ├── routes/
│   │   │   ├── pipeline_routes.py (enhance)
│   │   │   └── report_routes.py (enhance)
│   │   ├── models/
│   │   │   ├── pipeline_models.py (enhance)
│   │   │   ├── google_drive_models.py (create)
│   │   │   └── responses.py (enhance)
│   │   └── utils/
│   │       ├── vector_store_manager.py (enhance)
│   │       ├── citation_formatter.py (create)
│   │       ├── theme_validator.py (create)
│   │       ├── quality_scorer.py (create)
│   │       ├── report_templates.py (create)
│   │       └── oauth_validator.py (create)
│   └── tests/
│       ├── test_research_ingestion_agent.py
│       ├── test_retriever_agent.py
│       ├── test_initial_coding_agent.py
│       ├── test_thematic_grouping_agent.py
│       ├── test_validation_refinement_agent.py
│       ├── test_report_generator_agent.py
│       ├── test_google_drive_service.py
│       ├── test_pipeline_service.py
│       ├── test_full_pipeline.py
│       └── test_concurrent_pipelines.py
├── SPEC.md
├── API_CONTRACTS.md
├── AGENT_SPECIFICATIONS.md
└── IMPLEMENTATION_PLAN.md (this file)
```

## Risk Mitigation

### High-Risk Areas

1. **LLM JSON reliability**
   - Risk: The model returns non-JSON or drifts from the expected schema
   - Mitigation: strict prompting, robust parsing, schema validation, supervisor checks, unit tests

2. **Agent Orchestration**
   - Risk: Complex state management, error propagation
   - Mitigation: Incremental development, comprehensive testing

3. **Performance**
   - Risk: Slow pipeline execution
   - Mitigation: Performance testing, optimization, caching

4. **External API Dependencies**
   - Risk: API failures, rate limits
   - Mitigation: Retry logic, fallback mechanisms, error handling

### Contingency Plans

1. **If report JSON generation fails**: Fall back to markdown-only output and mark pipeline as partial
2. **If Weaviate fails**: Implement in-memory storage for MVP
3. **If external APIs fail**: Continue with available sources, log errors

## Success Criteria

### MVP Success Criteria

1. ✅ Can accept research parameters via API
2. ✅ Can fetch documents from multiple sources
3. ✅ Can store documents in Weaviate
4. ✅ Can retrieve relevant documents
5. ✅ Can perform coding and thematic analysis
6. ✅ Can generate academic reports
7. ✅ Can generate canonical JSON report payload
8. ✅ Pipeline completes in < 15 minutes
9. ✅ All agents execute successfully
10. ✅ Error handling works correctly

### Quality Metrics

- **Test Coverage**: > 80%
- **API Response Time**: < 2 seconds (for initiation)
- **Pipeline Success Rate**: > 95%
- **Error Recovery**: Automatic retry for transient errors
- **Documentation**: Complete and up-to-date

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|-----------------|
| Phase 1: Foundation | Week 1-2 | Environment, OAuth, Vector Store |
| Phase 2: Agents | Week 3-4 | All 6 agents implemented |
| Phase 3: Orchestration | Week 5 | Full pipeline working |
| Phase 4: Testing | Week 6 | Tests, QA, Performance |
| Phase 5: Deployment | Week 7 | Documentation, Deployment |

**Total Estimated Time**: 7 weeks

## Next Steps

1. Review and approve this implementation plan
2. Set up development environment (Phase 1.1)
3. Define JSON output contract + tests (Phase 1.2)
4. Start agent implementation (Phase 2)

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Status**: Ready for Review

