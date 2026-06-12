"""API request/response schemas for the AI Gateway."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str = Field(..., min_length=1, max_length=32000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    model: str | None = None                # override model selection
    strategy: str = "intent"               # intent | cost | latency | quality
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=16000)
    stream: bool = True
    session_id: str | None = None
    request_id: str | None = None


class ChatResponse(BaseModel):
    content: str
    model_used: str
    strategy_used: str
    routing_reason: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    pii_detected: bool
    request_id: str


class StreamChunk(BaseModel):
    type: Literal["content", "metadata", "error", "done"]
    content: str | None = None
    metadata: dict | None = None
    error: str | None = None


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    tier: str
    capabilities: list[str]
    context_window: int
    gpu_vram_gb: float
    cost_per_1k_prompt: float
    cost_per_1k_completion: float
    status: str
    latency_ms: float
    circuit_state: str


class HealthResponse(BaseModel):
    status: str
    models: dict[str, dict]
    cost_summary: dict
    timestamp: str
