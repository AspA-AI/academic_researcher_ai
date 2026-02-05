#
# Dockerfile for AI Researcher
# Multi-stage build: Build React/Vite frontend, then run FastAPI backend
# The backend serves the built frontend assets as static files
#

### Stage 1: Build Frontend
FROM node:20.19-alpine AS frontend-builder

WORKDIR /app/client

# Copy package files
COPY client/package.json client/package-lock.json ./

# Install dependencies
RUN npm ci

# Build-time API base URL (defaults to /api/v1 for same-origin)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copy frontend source code
COPY client/ ./

# Build the frontend
RUN npm run build

### Stage 2: Run Backend
FROM python:3.12-slim AS backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api \
    SERVE_CLIENT=true

WORKDIR /app/api

# Install system dependencies (for PDF processing)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY api/ ./

# Copy built frontend from Stage 1 into FastAPI static directory
COPY --from=frontend-builder /app/client/dist ./static

# Expose port (Railway/Heroku will set PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the FastAPI application
# Use PORT env var if set (for Railway/Heroku), otherwise default to 8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]

