"""Enterprise AI Platform — FastAPI Application Entry Point."""

from __future__ import annotations

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Enterprise AI Platform API",
    description="Banking AI Support Copilot & AIOps Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened in Phase 12 Security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "aiops-api"}


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "aiops-api", "version": "1.0.0"}
