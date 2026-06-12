"""Pydantic schemas for evaluation results."""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

from pydantic import BaseModel, Field


class ModelEvalResult(BaseModel):
    model_id: str = Field(..., description="Model identifier used for the evaluation")
    query: str = Field(..., description="The input prompt/query")
    response: str = Field(..., description="Generated response content")
    latency_ms: float = Field(..., description="Round‑trip latency in milliseconds")
    prompt_tokens: int = Field(..., description="Number of prompt tokens used")
    completion_tokens: int = Field(..., description="Number of completion tokens generated")
    cost_usd: float = Field(..., description="Cost incurred for this request (USD)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BenchmarkReport(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    results: List[ModelEvalResult] = Field(..., description="List of evaluation results for each model/query pair")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Optional aggregate statistics (e.g., avg latency)" )
