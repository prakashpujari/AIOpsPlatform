"""Unit tests — cost engine."""

from __future__ import annotations

import pytest

from src.cost.cost_engine import CostEngine, estimate_tokens
from src.registry.model_registry import registry


def test_estimate_tokens_non_zero() -> None:
    tokens = estimate_tokens("Hello, how are you doing today?")
    assert tokens > 0


def test_estimate_tokens_longer_text_more_tokens() -> None:
    short = estimate_tokens("Hello")
    long = estimate_tokens("Hello " * 100)
    assert long > short


def test_cost_engine_record() -> None:
    engine = CostEngine()
    model = registry.get("gemma2-9b")
    assert model is not None
    record = engine.record(model=model, prompt_tokens=100, completion_tokens=50, request_id="r1")
    assert record.cost_usd > 0
    assert record.model_id == "gemma2-9b"


def test_daily_spend_accumulates() -> None:
    engine = CostEngine()
    model = registry.get("gemma2-9b")
    assert model is not None
    engine.record(model=model, prompt_tokens=1000, completion_tokens=500)
    engine.record(model=model, prompt_tokens=1000, completion_tokens=500)
    assert engine.daily_spend() > 0


def test_budget_check_passes_under_limit() -> None:
    engine = CostEngine()
    engine.check_budget(0.001)  # should not raise


def test_budget_check_raises_when_exceeded() -> None:
    engine = CostEngine()
    from src.core.exceptions import BudgetExceededError
    with pytest.raises(BudgetExceededError):
        engine.check_budget(999_999.0)


def test_summary_structure() -> None:
    engine = CostEngine()
    model = registry.get("phi4-14b")
    assert model is not None
    engine.record(model=model, prompt_tokens=200, completion_tokens=100)
    summary = engine.summary()
    assert "daily_spend_usd" in summary
    assert "by_model" in summary
    assert "phi4-14b" in summary["by_model"]


def test_estimate_prompt_cost() -> None:
    engine = CostEngine()
    model = registry.get("gemma2-9b")
    assert model is not None
    messages = [{"role": "user", "content": "What is the incident status?"}]
    cost = engine.estimate_prompt_cost(messages, model)
    assert cost >= 0
