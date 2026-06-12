"""Unit tests — model registry."""

from __future__ import annotations

import pytest

from src.registry.model_registry import ModelRegistry, registry
from src.registry.schemas import ModelCapability, ModelProvider, ModelTier


def test_registry_has_all_six_models() -> None:
    models = registry.all_models()
    assert len(models) == 6


def test_all_required_models_present() -> None:
    ids = {m.id for m in registry.all_models()}
    expected = {"llama3.3-70b", "deepseek-r1", "deepseek-coder", "qwen3-72b", "phi4-14b", "gemma2-9b"}
    assert expected == ids


def test_get_existing_model() -> None:
    m = registry.get("llama3.3-70b")
    assert m is not None
    assert m.name == "Llama 3.3 70B Instruct"


def test_get_missing_model_returns_none() -> None:
    assert registry.get("nonexistent") is None


def test_get_or_raise_raises_for_missing() -> None:
    with pytest.raises(KeyError, match="not found"):
        registry.get_or_raise("nonexistent")


def test_by_capability_code() -> None:
    code_models = registry.by_capability(ModelCapability.CODE)
    ids = {m.id for m in code_models}
    assert "deepseek-coder" in ids


def test_by_tier_fast() -> None:
    fast = registry.by_tier(ModelTier.FAST)
    assert all(m.tier == ModelTier.FAST for m in fast)


def test_by_provider_ollama() -> None:
    ollama = registry.by_provider(ModelProvider.OLLAMA)
    ids = {m.id for m in ollama}
    assert {"phi4-14b", "gemma2-9b"} == ids


def test_sorted_by_priority() -> None:
    models = registry.sorted_by_priority()
    priorities = [m.priority for m in models]
    assert priorities == sorted(priorities)


def test_sorted_by_cost() -> None:
    models = registry.sorted_by_cost()
    costs = [m.cost_per_1k_prompt_tokens for m in models]
    assert costs == sorted(costs)


def test_sorted_by_speed() -> None:
    models = registry.sorted_by_speed()
    speeds = [m.avg_tokens_per_second for m in models]
    assert speeds == sorted(speeds, reverse=True)


def test_all_models_have_positive_costs() -> None:
    for m in registry.all_models():
        assert m.cost_per_1k_prompt_tokens > 0
        assert m.cost_per_1k_completion_tokens > 0


def test_all_models_have_context_window() -> None:
    for m in registry.all_models():
        assert m.context_window >= 4096


def test_within_vram_filters_correctly() -> None:
    small = registry.within_vram(10.0)
    for m in small:
        assert m.gpu_vram_gb <= 10.0
