"""Unit tests — routing engine and strategies."""

from __future__ import annotations

import pytest

from src.registry.model_registry import ModelRegistry, registry
from src.registry.schemas import ModelCapability, ModelStatus
from src.router.routing_engine import RoutingEngine, RoutingStrategy
from src.router.strategies.cost_strategy import select_cheapest
from src.router.strategies.intent_strategy import detect_intent, select_by_intent
from src.router.strategies.failover_strategy import get_fallback_chain


# ── Intent Detection ──────────────────────────────────────────────────────────

def test_detect_intent_code() -> None:
    messages = [{"role": "user", "content": "Write a Python function to parse JSON"}]
    intent = detect_intent(messages)
    assert intent == ModelCapability.CODE


def test_detect_intent_reasoning() -> None:
    messages = [{"role": "user", "content": "Analyze the root cause of this incident"}]
    intent = detect_intent(messages)
    assert intent == ModelCapability.REASONING


def test_detect_intent_summarization() -> None:
    messages = [{"role": "user", "content": "Summarize the last 24 hours of alerts"}]
    intent = detect_intent(messages)
    assert intent == ModelCapability.SUMMARIZATION


def test_detect_intent_default_chat() -> None:
    messages = [{"role": "user", "content": "Hello, I need help"}]
    intent = detect_intent(messages)
    assert intent == ModelCapability.CHAT


# ── Strategy: Cost ────────────────────────────────────────────────────────────

def test_select_cheapest_returns_lowest_cost() -> None:
    models = registry.all_models()
    best, reason = select_cheapest(models)
    assert best is not None
    all_costs = [m.cost_per_1k_prompt_tokens for m in models]
    assert best.cost_per_1k_prompt_tokens == min(all_costs)


def test_select_cheapest_empty_returns_none() -> None:
    best, reason = select_cheapest([])
    assert best is None


# ── Failover Chain ────────────────────────────────────────────────────────────

def test_failover_chain_excludes_primary() -> None:
    primary = registry.get("llama3.3-70b")
    assert primary is not None
    chain = get_fallback_chain(primary, registry.all_models())
    assert primary not in chain


def test_failover_chain_max_length() -> None:
    primary = registry.get("llama3.3-70b")
    assert primary is not None
    chain = get_fallback_chain(primary, registry.all_models(), max_fallbacks=2)
    assert len(chain) <= 2


# ── Routing Engine ────────────────────────────────────────────────────────────

class MockHealthMonitor:
    def get_status(self, model_id: str) -> ModelStatus:
        return ModelStatus.HEALTHY

    def healthy_models(self) -> list[str]:
        return [m.id for m in registry.all_models()]

    def get_latency_ms(self, model_id: str) -> float:
        return 100.0

    def circuit_registry(self):
        from src.health.circuit_breaker import CircuitBreakerRegistry
        return CircuitBreakerRegistry()


@pytest.mark.asyncio
async def test_routing_engine_returns_decision() -> None:
    engine = RoutingEngine(model_registry=registry, monitor=MockHealthMonitor())
    messages = [{"role": "user", "content": "What is the current incident status?"}]
    decision = await engine.route(messages=messages)
    assert decision.selected_model is not None
    assert decision.strategy_used is not None
    assert decision.routing_reason != ""


@pytest.mark.asyncio
async def test_routing_engine_cost_strategy() -> None:
    engine = RoutingEngine(model_registry=registry, monitor=MockHealthMonitor())
    messages = [{"role": "user", "content": "Classify this alert"}]
    decision = await engine.route(messages=messages, strategy=RoutingStrategy.COST)
    assert decision.strategy_used == "cost"
    # Cost strategy picks cheapest — should be gemma or phi
    assert decision.selected_model.id in {"gemma2-9b", "phi4-14b"}


@pytest.mark.asyncio
async def test_routing_engine_preferred_model_honoured() -> None:
    engine = RoutingEngine(model_registry=registry, monitor=MockHealthMonitor())
    messages = [{"role": "user", "content": "Write some code"}]
    decision = await engine.route(messages=messages, preferred_model="deepseek-coder")
    assert decision.selected_model.id == "deepseek-coder"
    assert decision.strategy_used == "explicit"


@pytest.mark.asyncio
async def test_routing_engine_no_healthy_models_raises() -> None:
    class NoHealthyMonitor:
        def get_status(self, model_id: str) -> ModelStatus:
            return ModelStatus.UNHEALTHY
        def healthy_models(self) -> list[str]:
            return []
        def get_latency_ms(self, model_id: str) -> float:
            return 0.0
        def circuit_registry(self):
            from src.health.circuit_breaker import CircuitBreakerRegistry
            return CircuitBreakerRegistry()

    engine = RoutingEngine(model_registry=registry, monitor=NoHealthyMonitor())
    from src.core.exceptions import NoHealthyModelError
    with pytest.raises(NoHealthyModelError):
        await engine.route(messages=[{"role": "user", "content": "test"}])
