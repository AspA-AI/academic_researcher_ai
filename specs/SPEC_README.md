# B2B AI Research Automation Platform - Specification Documents

## Overview

This directory contains the complete specification for the B2B AI Research Automation Platform. The specification is organized into multiple documents covering different aspects of the system.

## Specification Documents

### 1. [SPEC.md](./SPEC.md) - Main Specification
**Purpose**: Comprehensive overview of the platform

**Contents**:
- System overview and purpose
- Key features and MVP scope
- High-level architecture
- Technology stack
- User inputs and requirements
- Agent overview (6 agents)
- Data models
- API endpoints summary
- Output contract (JSON-first)
- Error handling
- Performance requirements
- Security considerations

**Use this for**: Understanding the overall system, requirements, and architecture

---

### 2. [API_CONTRACTS.md](./API_CONTRACTS.md) - API Contracts
**Purpose**: Detailed API endpoint specifications

**Contents**:
- Complete request/response schemas
- All API endpoints with examples
- Error response formats
- Authentication requirements
- Rate limiting (future)
- Health check endpoints

**Use this for**: API integration, frontend development, testing

---

### 3. [AGENT_SPECIFICATIONS.md](./AGENT_SPECIFICATIONS.md) - Agent Specifications
**Purpose**: Detailed specifications for each agent

**Contents**:
- Purpose and responsibilities for each agent
- Input/output schemas
- Implementation details
- LLM prompt templates
- Performance targets
- Error handling strategies

**Agents Covered**:
1. Research & Ingestion Agent
2. Retriever Logic Agent
3. Initial Coding Agent
4. Thematic Grouping Agent
5. Validation & Refinement Agent
6. Report Generation Agent

**Use this for**: Agent implementation, understanding agent behavior, debugging

---

### 4. [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Implementation Plan
**Purpose**: Step-by-step implementation guide

**Contents**:
- Implementation phases (5 phases)
- Task breakdown with priorities
- Dependencies between tasks
- Estimated timelines
- File structure
- Risk mitigation
- Success criteria
- Testing strategy

**Use this for**: Project planning, task assignment, progress tracking

---

## Quick Start Guide

### For Project Managers
1. Read [SPEC.md](./SPEC.md) for system overview
2. Review [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for timeline and phases
3. Use the plan to assign tasks and track progress

### For Developers
1. Start with [SPEC.md](./SPEC.md) for context
2. Read [AGENT_SPECIFICATIONS.md](./AGENT_SPECIFICATIONS.md) for agent details
3. Follow [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for implementation order
4. Reference [API_CONTRACTS.md](./API_CONTRACTS.md) when building endpoints

### For Frontend Developers
1. Read [SPEC.md](./SPEC.md) for user inputs and requirements
2. Use [API_CONTRACTS.md](./API_CONTRACTS.md) for all API integration
3. Reference data models in [SPEC.md](./SPEC.md) section 5

### For QA/Testers
1. Review [API_CONTRACTS.md](./API_CONTRACTS.md) for endpoint testing
2. Use [AGENT_SPECIFICATIONS.md](./AGENT_SPECIFICATIONS.md) for agent behavior validation
3. Reference [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for test requirements

## System Architecture Summary

```
User Input (Topic, Date Range, Sources, etc.)
    ↓
Pipeline Orchestrator
    ↓
┌─────────────────────────────────────────┐
│ 1. Research & Ingestion Agent          │ → Weaviate Vector Store
│ 2. Retriever Logic Agent               │
│ 3. Initial Coding Agent                │
│ 4. Thematic Grouping Agent             │
│ 5. Validation & Refinement Agent       │
│ 6. Report Generation Agent             │ → Canonical JSON output
└─────────────────────────────────────────┘
    ↓
Structured JSON report payload (optionally with markdown preview)
```

## Key Features

✅ **Multi-Source Content Ingestion**
- CoreAPI, arXiv, OpenAlex, Europe PMC, Google

✅ **Intelligent Document Processing**
- Chunking, embedding, vector storage (Weaviate)

✅ **Multi-Agent Analysis Pipeline**
- 6 specialized AI agents for complete research workflow

✅ **Academic Report Generation**
- JSON-first canonical report payload
- Harvard-style citations
- Professional academic structure

✅ **Template Rendering (Post-MVP)**
- PDF/PPTX/DOCX/HTML renderers consume canonical JSON

## Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **AI/ML**: LangChain, OpenAI (GPT-4, Embeddings)
- **Vector DB**: Weaviate
- **External APIs**: CoreAPI, OpenAlex, Europe PMC, arXiv

## Implementation Timeline

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1 | Week 1-2 | Foundation & Infrastructure |
| Phase 2 | Week 3-4 | Core Agents Implementation |
| Phase 3 | Week 5 | Pipeline Orchestration |
| Phase 4 | Week 6 | Testing & QA |
| Phase 5 | Week 7 | Documentation & Deployment |

**Total**: 7 weeks

## Success Criteria

- ✅ Pipeline completes in < 15 minutes
- ✅ All 6 agents execute successfully
- ✅ Canonical JSON report output generated
- ✅ Harvard-style citations
- ✅ Error handling and recovery
- ✅ Test coverage > 80%

## Next Steps

1. **Review Specifications**: Ensure all requirements are understood
2. **Set Up Environment**: Follow Phase 1.1 in Implementation Plan
3. **Begin Development**: Start with JSON output contract + tests (Phase 1.2)
4. **Iterate**: Follow the phased approach in Implementation Plan

## Document Status

| Document | Version | Status | Last Updated |
|----------|---------|--------|--------------|
| SPEC.md | 1.0 | ✅ Complete | 2024-01-15 |
| API_CONTRACTS.md | 1.0 | ✅ Complete | 2024-01-15 |
| AGENT_SPECIFICATIONS.md | 1.0 | ✅ Complete | 2024-01-15 |
| IMPLEMENTATION_PLAN.md | 1.0 | ✅ Complete | 2024-01-15 |

## Questions or Updates?

If you need to update or clarify any part of the specification:

1. Update the relevant document
2. Increment the version number
3. Update the "Last Updated" date
4. Document changes in the document's changelog section

---

**Specification Version**: 1.0  
**Created**: 2024-01-15  
**Status**: Ready for Implementation

