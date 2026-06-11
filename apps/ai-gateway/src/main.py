"""Enterprise AI Platform — AI Gateway Entry Point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Gateway",
    description="Internal AI Gateway — Model Routing, Policy, Cost",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-gateway"}
