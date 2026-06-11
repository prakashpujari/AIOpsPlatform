# ─────────────────────────────────────────────
# Multi-stage Dockerfile — API Service
# ─────────────────────────────────────────────

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies ──────────────────────────────
FROM base AS deps
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry==1.8.3 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# ── Development ───────────────────────────────
FROM deps AS development
RUN poetry install --no-interaction --no-ansi
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production ────────────────────────────────
FROM deps AS production
COPY . .
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--no-access-log"]
