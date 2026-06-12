"""Model registry — single source of truth for all supported LLMs."""

from __future__ import annotations

import logging
from typing import Sequence

from .schemas import (
    ModelCapability,
    ModelDefinition,
    ModelProvider,
    ModelTier,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Catalogue of all supported models
# ---------------------------------------------------------------------------

_MODELS: list[ModelDefinition] = [
    # ── Llama 3.3 70B ──────────────────────────────────────────────────────
    ModelDefinition(
        id="llama3.3-70b",
        name="Llama 3.3 70B Instruct",
        provider=ModelProvider.VLLM,
        tier=ModelTier.POWERFUL,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.SUMMARIZATION,
            ModelCapability.CLASSIFICATION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.LONG_CONTEXT,
            ModelCapability.MULTILINGUAL,
        ],
        context_window=128_000,
        max_output_tokens=8_192,
        gpu_vram_gb=40.0,
        cost_per_1k_prompt_tokens=0.0009,
        cost_per_1k_completion_tokens=0.0009,
        avg_tokens_per_second=35.0,
        quantization="fp8",
        priority=1,
        tags=["general", "banking", "flagship"],
    ),
    # ── DeepSeek R1 ────────────────────────────────────────────────────────
    ModelDefinition(
        id="deepseek-r1",
        name="DeepSeek R1 (Chain-of-Thought)",
        provider=ModelProvider.VLLM,
        tier=ModelTier.POWERFUL,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.SUMMARIZATION,
            ModelCapability.CLASSIFICATION,
        ],
        context_window=64_000,
        max_output_tokens=8_192,
        gpu_vram_gb=48.0,
        cost_per_1k_prompt_tokens=0.0014,
        cost_per_1k_completion_tokens=0.0028,
        avg_tokens_per_second=20.0,
        quantization=None,
        priority=2,
        tags=["reasoning", "rca", "analysis"],
    ),
    # ── DeepSeek Coder ─────────────────────────────────────────────────────
    ModelDefinition(
        id="deepseek-coder",
        name="DeepSeek Coder V2",
        provider=ModelProvider.VLLM,
        tier=ModelTier.BALANCED,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.CODE,
            ModelCapability.REASONING,
            ModelCapability.FUNCTION_CALLING,
        ],
        context_window=128_000,
        max_output_tokens=8_192,
        gpu_vram_gb=20.0,
        cost_per_1k_prompt_tokens=0.0002,
        cost_per_1k_completion_tokens=0.0006,
        avg_tokens_per_second=45.0,
        quantization="awq",
        priority=3,
        tags=["code", "scripting", "runbook"],
    ),
    # ── Qwen 3 ─────────────────────────────────────────────────────────────
    ModelDefinition(
        id="qwen3-72b",
        name="Qwen 3 72B Instruct",
        provider=ModelProvider.VLLM,
        tier=ModelTier.POWERFUL,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.SUMMARIZATION,
            ModelCapability.MULTILINGUAL,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.LONG_CONTEXT,
        ],
        context_window=128_000,
        max_output_tokens=8_192,
        gpu_vram_gb=40.0,
        cost_per_1k_prompt_tokens=0.0009,
        cost_per_1k_completion_tokens=0.0009,
        avg_tokens_per_second=32.0,
        quantization="fp8",
        priority=2,
        tags=["multilingual", "global-banking"],
    ),
    # ── Phi-4 ──────────────────────────────────────────────────────────────
    ModelDefinition(
        id="phi4-14b",
        name="Microsoft Phi-4 14B",
        provider=ModelProvider.OLLAMA,
        tier=ModelTier.BALANCED,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.REASONING,
            ModelCapability.SUMMARIZATION,
            ModelCapability.CLASSIFICATION,
        ],
        context_window=16_000,
        max_output_tokens=4_096,
        gpu_vram_gb=10.0,
        cost_per_1k_prompt_tokens=0.0001,
        cost_per_1k_completion_tokens=0.0002,
        avg_tokens_per_second=60.0,
        quantization="q4_k_m",
        priority=4,
        tags=["fast", "low-cost", "classification"],
        endpoint_path="/api/chat",
    ),
    # ── Gemma ──────────────────────────────────────────────────────────────
    ModelDefinition(
        id="gemma2-9b",
        name="Google Gemma 2 9B Instruct",
        provider=ModelProvider.OLLAMA,
        tier=ModelTier.FAST,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.SUMMARIZATION,
            ModelCapability.CLASSIFICATION,
        ],
        context_window=8_192,
        max_output_tokens=2_048,
        gpu_vram_gb=6.0,
        cost_per_1k_prompt_tokens=0.00005,
        cost_per_1k_completion_tokens=0.0001,
        avg_tokens_per_second=80.0,
        quantization="q4_k_m",
        priority=5,
        tags=["fast", "cheap", "triage", "fallback"],
        endpoint_path="/api/chat",
    ),
]

_MODEL_MAP: dict[str, ModelDefinition] = {m.id: m for m in _MODELS}


class ModelRegistry:
    """Immutable catalogue with capability and tier queries."""

    def __init__(self, models: list[ModelDefinition] | None = None) -> None:
        self._models = {m.id: m for m in (models or _MODELS)}

    # ── Lookups ─────────────────────────────────────────────────────────────

    def get(self, model_id: str) -> ModelDefinition | None:
        return self._models.get(model_id)

    def get_or_raise(self, model_id: str) -> ModelDefinition:
        model = self._models.get(model_id)
        if model is None:
            raise KeyError(f"Model '{model_id}' not found in registry")
        return model

    def all_models(self) -> list[ModelDefinition]:
        return list(self._models.values())

    # ── Filters ─────────────────────────────────────────────────────────────

    def by_capability(self, capability: ModelCapability) -> list[ModelDefinition]:
        return [m for m in self._models.values() if capability in m.capabilities]

    def by_tier(self, tier: ModelTier) -> list[ModelDefinition]:
        return [m for m in self._models.values() if m.tier == tier]

    def by_provider(self, provider: ModelProvider) -> list[ModelDefinition]:
        return [m for m in self._models.values() if m.provider == provider]

    def by_capabilities(
        self, capabilities: Sequence[ModelCapability], require_all: bool = False
    ) -> list[ModelDefinition]:
        if require_all:
            return [
                m for m in self._models.values()
                if all(c in m.capabilities for c in capabilities)
            ]
        return [
            m for m in self._models.values()
            if any(c in m.capabilities for c in capabilities)
        ]

    def within_vram(self, available_vram_gb: float) -> list[ModelDefinition]:
        return [m for m in self._models.values() if m.gpu_vram_gb <= available_vram_gb]

    def sorted_by_priority(self, models: list[ModelDefinition] | None = None) -> list[ModelDefinition]:
        src = models if models is not None else list(self._models.values())
        return sorted(src, key=lambda m: m.priority)

    def sorted_by_cost(self, models: list[ModelDefinition] | None = None) -> list[ModelDefinition]:
        src = models if models is not None else list(self._models.values())
        return sorted(src, key=lambda m: m.cost_per_1k_prompt_tokens + m.cost_per_1k_completion_tokens)

    def sorted_by_speed(self, models: list[ModelDefinition] | None = None) -> list[ModelDefinition]:
        src = models if models is not None else list(self._models.values())
        return sorted(src, key=lambda m: m.avg_tokens_per_second, reverse=True)


# Singleton registry instance
registry = ModelRegistry()
