"""Model registry schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    VLLM = "vllm"
    OLLAMA = "ollama"
    TGI = "tgi"
    OPENAI_COMPAT = "openai_compat"
    GROQ = "groq"


class ModelCapability(str, Enum):
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    EMBEDDINGS = "embeddings"
    FUNCTION_CALLING = "function_calling"
    LONG_CONTEXT = "long_context"
    MULTILINGUAL = "multilingual"


class ModelTier(str, Enum):
    FAST = "fast"        # < 200ms TTFT, small models
    BALANCED = "balanced" # 200-500ms TTFT, mid models
    POWERFUL = "powerful" # > 500ms TTFT, large models


class ModelStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"
    UNKNOWN = "unknown"


class ModelDefinition(BaseModel):
    id: str
    name: str
    provider: ModelProvider
    tier: ModelTier
    capabilities: list[ModelCapability]
    context_window: int
    max_output_tokens: int
    gpu_vram_gb: float
    cost_per_1k_prompt_tokens: float    # USD
    cost_per_1k_completion_tokens: float # USD
    avg_tokens_per_second: float
    supports_streaming: bool = True
    supports_system_prompt: bool = True
    quantization: str | None = None     # "awq", "gptq", "fp8", None
    priority: int = 5                   # 1 (highest) to 10 (lowest)
    tags: list[str] = []
    endpoint_path: str = "/v1/chat/completions"


class ModelHealthState(BaseModel):
    model_id: str
    status: ModelStatus = ModelStatus.UNKNOWN
    failure_count: int = 0
    last_failure: str | None = None
    last_success: str | None = None
    avg_latency_ms: float = 0.0
    circuit_open_until: str | None = None


class RoutingDecision(BaseModel):
    selected_model: ModelDefinition
    strategy_used: str
    fallback_models: list[str] = []
    routing_reason: str
    estimated_cost_usd: float
    estimated_latency_ms: float
