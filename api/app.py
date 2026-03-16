"""
Main FastAPI application for the Research Pipeline API.
Contains the main app instance, middleware, and route registration.
"""

import sys
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

# Add parent directory to path if running from api/ folder
# This allows the app to work both from repo root and api/ directories
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# NOTE: Use package-absolute imports (e.g., `from api...`) instead of
# manually mutating sys.path. This makes the app runnable from the repo
# root with `uvicorn api.main:app` and from the `api/` directory with
# `uvicorn main:app`.

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from api.models.responses import ErrorResponse
from api.routes import (
    pipeline_routes,
    agent_routes,
    data_routes,
    report_routes,
)


# Global variables for application state
app_state = {
    "startup_time": None,
    "total_requests": 0,
    "active_pipelines": 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    app_state["startup_time"] = datetime.now(timezone.utc)
    print(f"🚀 Research Pipeline API starting up at {app_state['startup_time']}")
    
    # Initialize services here if needed
    try:
        # Any startup initialization can go here
        print("✅ Services initialized successfully")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    shutdown_time = datetime.now(timezone.utc)
    uptime = shutdown_time - app_state["startup_time"]
    print(f"🛑 Research Pipeline API shutting down after {uptime}")
    print(f"📊 Total requests processed: {app_state['total_requests']}")

# Create FastAPI application
app = FastAPI(
    title="Research Pipeline API",
    description="""
    A comprehensive REST API for automated academic research pipeline execution.
    
    This API provides endpoints for:
    - **Pipeline Management**: Start, monitor, and manage research pipelines
    - **Agent Operations**: Execute individual research agents (literature review, coding, etc.)
    - **Quality Control**: Supervisor agent integration and quality assessment
    - **Data Management**: Document retrieval and vector database operations
    - **Report Generation**: Academic report creation and management
    
    ## Features
    - Multi-agent research pipeline orchestration
    - Real-time progress tracking
    - Quality control with supervisor agent
    - Academic report generation
    - Vector database integration
    - Comprehensive error handling and logging
    """,
    version="1.0.0",
    contact={
        "name": "Research Pipeline Team",
        "email": "support@researchpipeline.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    app_state["total_requests"] += 1
    
    error_response = ErrorResponse(
        success=False,
        error=str(exc.detail),
        error_code=f"HTTP_{exc.status_code}",
        details={"path": request.url.path, "method": request.method},
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    app_state["total_requests"] += 1
    
    error_response = ErrorResponse(
        success=False,
        error="Request validation failed",
        error_code="VALIDATION_ERROR",
        details={
            "path": request.url.path,
            "method": request.method,
            "validation_errors": exc.errors()
        },
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    app_state["total_requests"] += 1
    
    error_response = ErrorResponse(
        success=False,
        error="Internal server error",
        error_code="INTERNAL_ERROR",
        details={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__
        },
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )

# Request middleware for logging
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Middleware for request logging and statistics."""
    start_time = datetime.now(timezone.utc)
    
    # Process request
    response = await call_next(request)
    
    # Update statistics
    app_state["total_requests"] += 1
    
    # Log request (in production, use proper logging)
    process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
    print(f"📊 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": str(datetime.now(timezone.utc) - app_state["startup_time"]) if app_state["startup_time"] else "unknown",
        "total_requests": app_state["total_requests"],
        "active_pipelines": app_state["active_pipelines"]
    }

# Include route modules
app.include_router(
    pipeline_routes.router,
    prefix="/api/v1/pipelines",
    tags=["Pipelines"]
)

app.include_router(
    agent_routes.router,
    prefix="/api/v1/agents",
    tags=["Agents"]
)

# app.include_router(
#     quality_routes.router,
#     prefix="/api/v1/quality",
#     tags=["Quality Control"]
# )

app.include_router(
    data_routes.router,
    prefix="/api/v1/data",
    tags=["Data Management"]
)

app.include_router(
    report_routes.router,
    prefix="/api/v1/reports",
    tags=["Reports"]
)

# Serve static files (frontend) if SERVE_CLIENT is enabled
# This is used in Docker/production deployments
if os.getenv("SERVE_CLIENT", "false").lower() == "true":
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        # Mount static assets directory (Vite outputs to /assets)
        assets_dir = os.path.join(static_dir, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
        # Serve index.html for root path
        @app.get("/")
        async def serve_index():
            """Serve the React app index.html for root path."""
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            else:
                raise HTTPException(status_code=404, detail="Frontend not built")
        
        # Catch-all route for SPA routing (must be last)
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve the React app for all non-API routes (SPA routing)."""
            # Skip API routes, docs, and static assets
            if (full_path.startswith("api/") or 
                full_path == "docs" or full_path.startswith("docs/") or
                full_path == "redoc" or full_path.startswith("redoc/") or
                full_path == "openapi.json" or
                full_path.startswith("assets/") or
                full_path.startswith("static/")):
                raise HTTPException(status_code=404, detail="Not found")
            
            # Serve index.html for all other routes (React Router handles client-side routing)
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            else:
                raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )