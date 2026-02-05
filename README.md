# AI Researcher

A comprehensive academic research pipeline system that automates literature review, thematic analysis, and report generation using multi-agent AI orchestration.

## 🏗️ Architecture

This project consists of two main components:

- **Backend (`api/`)**: FastAPI-based REST API with multi-agent research pipeline
- **Frontend (`client/`)**: React + TypeScript + Vite web application

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Usage](#usage)

## ✨ Features

### Backend Features
- **Multi-Agent Pipeline**: Orchestrates multiple AI agents for research tasks
  - Document Retrieval Agent
  - Literature Review Agent
  - Initial Coding Agent
  - Thematic Grouping Agent
  - Theme Refinement Agent
  - Report Generator Agent
  - Supervisor Agent (quality control)
- **Smart Retrieval System**: Advanced RAG (Retrieval-Augmented Generation)
  - Cross-encoder reranking for accuracy
  - Adaptive threshold filtering
  - Paper-level diversification
  - Quality metrics (quantity, certainty, recency)
- **Format Transformation**: LLM-powered report format conversion
  - PPTX (PowerPoint) with customizable themes
  - HTML, PDF, DOCX, Markdown, Text, JSON
- **Vector Database Integration**: Weaviate/Chroma for document storage
- **Multi-Source Data Extraction**: Supports arXiv, CORE, Europe PMC, and more

### Frontend Features
- **Interactive Pipeline Interface**: Start and monitor research pipelines
- **Report Preview & Export**: Real-time preview with multiple format options
- **Template System**: Multiple report templates (Academic, Executive Summary, Slide Deck)
- **Theme Customization**: 8+ PowerPoint themes for presentations
- **Tabbed Interface**: Organized view of Preview, JSON Output, and Export options
- **Responsive Design**: Modern, dark-themed UI

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.128.0
- **Python**: 3.12+
- **AI/ML**:
  - OpenAI GPT (via LangChain)
  - Sentence Transformers (cross-encoder reranking)
  - LangChain Core
- **Vector Database**: Weaviate Client 4.19.0
- **PDF Processing**: PyMuPDF, pdfplumber, pdf2image
- **Server**: Uvicorn with ASGI

### Frontend
- **Framework**: React 18.3.1
- **Language**: TypeScript 5.4.0
- **Build Tool**: Vite 5.0.0
- **Export Libraries**:
  - jsPDF (PDF generation)
  - docx (Word documents)
  - pptxgenjs (PowerPoint presentations)
- **Routing**: React Router DOM 6.30.3

## 📁 Project Structure

```
ai_researcher/
├── api/                          # Backend FastAPI application
│   ├── agents/                   # AI agent implementations
│   │   ├── data_extractor_agent.py
│   │   ├── literature_review_agent.py
│   │   ├── initial_coding_agent.py
│   │   ├── thematic_grouping_agent.py
│   │   ├── theme_refiner_agent.py
│   │   ├── report_generator_agent.py
│   │   ├── format_transformation_agent.py
│   │   └── supervisor_agent.py
│   ├── routes/                   # API route handlers
│   │   ├── pipeline_routes.py   # Pipeline management
│   │   ├── agent_routes.py       # Individual agent execution
│   │   ├── data_routes.py        # Data management
│   │   └── report_routes.py      # Report generation & export
│   ├── services/                # Business logic services
│   │   ├── pipeline_service.py
│   │   ├── smart_retrieval_service.py
│   │   ├── retrieval_quality.py
│   │   └── report_service.py
│   ├── models/                   # Pydantic models
│   │   ├── requests.py
│   │   ├── responses.py
│   │   └── format_models.py
│   ├── utils/                    # Utility modules
│   │   ├── llm_backends.py
│   │   ├── vector_store_manager.py
│   │   └── reranking.py
│   ├── app.py                    # FastAPI application entry point
│   └── requirements.txt          # Python dependencies
│
├── client/                        # Frontend React application
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── PipelineForm.tsx
│   │   │   ├── ResponsePanel.tsx
│   │   │   ├── ReportExportPanel.tsx
│   │   │   └── ...
│   │   ├── api/                 # API client
│   │   │   └── client.ts
│   │   ├── utils/               # Utility functions
│   │   │   ├── report.ts
│   │   │   └── reportExporters.ts
│   │   ├── config/              # Configuration
│   │   │   ├── reportTemplates.ts
│   │   │   └── pptxThemes.ts
│   │   ├── App.tsx              # Main app component
│   │   └── main.tsx            # Entry point
│   ├── package.json
│   └── vite.config.ts
│
├── doc/                          # Documentation
│   └── BACKEND_DOCUMENTATION.md
│
├── Dockerfile                    # Docker build configuration
└── README.md                    # This file
```

## 📦 Prerequisites

### For Local Development
- **Python**: 3.12 or higher
- **Node.js**: 20.x or higher
- **npm**: Comes with Node.js
- **Vector Database**: Weaviate instance (local or cloud)
- **OpenAI API Key**: For LLM operations

### For Docker Deployment
- **Docker**: 20.10+
- **Docker Compose**: (optional, for multi-container setups)

## 🚀 Local Development

### Backend Setup

1. **Navigate to the API directory**:
   ```bash
   cd ai_researcher/api
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the `api/` directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   WEAVIATE_URL=http://localhost:8080
   WEAVIATE_API_KEY=your_weaviate_key_if_needed
   ```

5. **Run the backend server**:
   ```bash
   # From api/ directory
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   
   # Or from project root
   uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

1. **Navigate to the client directory**:
   ```bash
   cd ai_researcher/client
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

   The Vite dev server is configured to proxy `/api` requests to `http://localhost:8000`

### Running Both Together

In separate terminals:

**Terminal 1 - Backend**:
```bash
cd ai_researcher/api
source venv/bin/activate
uvicorn app:app --reload --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd ai_researcher/client
npm run dev
```

## 🐳 Docker Deployment

### Building the Docker Image

From the `ai_researcher/` directory:

```bash
docker build -t ai-researcher:latest .
```

### Running the Container

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e WEAVIATE_URL=http://your-weaviate:8080 \
  -e VITE_API_BASE_URL=/api/v1 \
  ai-researcher:latest
```

The application will be available at `http://localhost:8000`

### Docker Compose (Optional)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ai-researcher:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEAVIATE_URL=${WEAVIATE_URL}
      - VITE_API_BASE_URL=/api/v1
    volumes:
      - ./reports:/app/api/reports
```

Run with:
```bash
docker-compose up -d
```

## 📚 API Documentation

### Main Endpoints

#### Pipeline Management
- `POST /api/v1/pipelines/full` - Start full thematic pipeline
- `POST /api/v1/pipelines/lite` - Start lite pipeline (faster)
- `GET /api/v1/pipelines/{pipeline_id}` - Get pipeline results
- `DELETE /api/v1/pipelines/{pipeline_id}` - Delete pipeline

#### Report Generation
- `POST /api/v1/reports/transform` - Transform report to different format
- `GET /api/v1/reports/{report_id}` - Get report details
- `GET /api/v1/reports/{report_id}/download` - Download report

#### Data Management
- `POST /api/v1/data/retrieve` - Retrieve documents from vector store
- `POST /api/v1/data/store` - Store documents in vector store

#### Health Check
- `GET /health` - Health check endpoint

### Interactive API Documentation

When running the backend, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## ⚙️ Configuration

### Backend Configuration

Key configuration files:
- `api/app.py` - Main FastAPI application
- `api/services/pipeline_service.py` - Pipeline orchestration
- `api/services/smart_retrieval_service.py` - RAG retrieval logic

### Frontend Configuration

- `client/vite.config.ts` - Vite build configuration
- `client/src/api/client.ts` - API client configuration
- `client/src/config/reportTemplates.ts` - Report template definitions
- `client/src/config/pptxThemes.ts` - PowerPoint theme definitions

## 🔐 Environment Variables

### Backend Required Variables

```env
# OpenAI API
OPENAI_API_KEY=sk-...

# Vector Database
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=optional_api_key

# Optional: Custom API base URL for frontend
VITE_API_BASE_URL=/api/v1
```

### Frontend Build Variables

Set during Docker build or in `.env`:
```env
VITE_API_BASE_URL=/api/v1
```

## 💡 Usage

### Starting a Research Pipeline

1. **Via Frontend UI**:
   - Navigate to `http://localhost:5173`
   - Fill in the research query and domain
   - Choose between Lite or Full pipeline
   - Click "Start Pipeline"
   - Monitor progress and view results

2. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/pipelines/lite" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "blockchain technology applications",
       "research_domain": "blockchain",
       "max_results": 20,
       "sources": ["arxiv", "core"]
     }'
   ```

### Exporting Reports

1. **Via Frontend**:
   - After pipeline completes, navigate to Export tab
   - Choose template and format (PDF, PPTX, HTML, DOCX, etc.)
   - Select PowerPoint theme if exporting PPTX
   - Click "Export" to download

2. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/reports/transform" \
     -H "Content-Type: application/json" \
     -d '{
       "report": {...},
       "targetFormat": "pptx"
     }'
   ```

## 🔍 Pipeline Modes

### Lite Pipeline
- **Steps**: Document Retrieval → Literature Review → Report Generation
- **Use Case**: Quick research summaries
- **Duration**: ~30-60 seconds

### Full Pipeline
- **Steps**: Document Retrieval → Literature Review → Initial Coding → Thematic Grouping → Theme Refinement → Report Generation
- **Use Case**: In-depth thematic analysis
- **Duration**: ~2-5 minutes

## 🧪 Testing

### Backend Tests
```bash
cd ai_researcher/api
pytest tests/
```

### Frontend Tests
```bash
cd ai_researcher/client
npm test
```

## 📝 Documentation

- **Backend Documentation**: See `doc/BACKEND_DOCUMENTATION.md` for detailed API and RAG implementation docs
- **API Specifications**: See `specs/` directory for detailed specifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- Check the documentation in `doc/` directory
- Review API docs at `/docs` endpoint
- Open an issue on GitHub

## 🎯 Roadmap

- [ ] Enhanced report templates
- [ ] Additional export formats
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Multi-language support

---

**Built with ❤️ for academic researchers**

