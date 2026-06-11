"""Enterprise AI Platform — Ingestion Service Entry Point."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Ingestion Service",
    description="Document ingestion pipeline — parse, chunk, embed, store",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ingestion"}
