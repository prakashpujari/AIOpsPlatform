# ─────────────────────────────────────────────
# Multi-stage Dockerfile — Ingestion Service
# ─────────────────────────────────────────────

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev poppler-utils libmagic1 && \
    rm -rf /var/lib/apt/lists/*

FROM base AS deps
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry==1.8.3 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

FROM deps AS development
RUN poetry install --no-interaction --no-ansi
COPY . .
EXPOSE 8002
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

FROM deps AS production
COPY . .
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
