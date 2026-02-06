#
# Railway single-service deployment for monorepo:
# - Build React/Vite frontend
# - Run FastAPI backend (and serve built frontend assets)
#

### Stage 1: build frontend
FROM node:20.19-alpine AS web
WORKDIR /app/client

COPY client/package.json client/package-lock.json ./
RUN npm ci --prefer-offline --no-audit

# Build-time API base URL (same-origin by default)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY client/ ./
RUN npm run build && \
    rm -rf node_modules

### Stage 2: run backend
FROM python:3.12-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api \
    SERVE_CLIENT=true

WORKDIR /app/api

# No system dependencies needed - saves ~200MB
# OCR (tesseract-ocr, poppler-utils) is optional and handled gracefully by the code
# PDF extraction will use PyMuPDF and pdfplumber only

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip

COPY api/ ./

# Copy built frontend into FastAPI container
COPY --from=web /app/client/dist ./static

# Remove unnecessary files to reduce image size
RUN find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete && \
    find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true && \
    rm -rf tests/ test/ .pytest_cache/ .coverage htmlcov/ notebook/ *.ipynb || true

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]

