"""Unit tests for the RoutingEngine (Phase 5)."""

import pytest
import asyncio
from typing import List

from src.router.routing_engine import RoutingEngine, RoutingStrategy
from src.registry.schemas import ModelDefinition, ModelCapability, ModelStatus, ModelTier, ModelProvider
from src.core.config import settings

# Helper to create a minimal ModelDefinition
def make_model(id: str, priority: int, capabilities: List[ModelCapability]) -> ModelDefinition:
    return ModelDefinition(
        id=id,
        name=id,
        provider=ModelProvider.VLLM,
        tier=ModelTier.BALANCED,
        capabilities=capabilities,
        context_window=8192,
        max_output_tokens=2048,
        gpu_vram_gb=8.0,
        cost_per_1k_prompt_tokens=0.001,
        cost_per_1k_completion_tokens=0.0015,
        avg_tokens_per_second=30.0,
        priority=priority,
    )

class DummyRegistry:
    def __init__(self, models: List[ModelDefinition]):
        self._models = {m.id: m for m in models}
    def get(self, model_id: str):
        return self._models.get(model_id)
    def all_models(self) -> List[ModelDefinition]:
        return list(self._models.values())

class DummyMonitor:
    def __init__(self, healthy_ids: List[str]):
        self._healthy = set(healthy_ids)
    def get_status(self, model_id: str):
        return ModelStatus.HEALTHY if model_id in self._healthy else ModelStatus.UNHEALTHY
    def healthy_models(self):
        return list(self._healthy)
    def get_latency_ms(self, model_id: str):
        return 100.0
    def circuit_registry(self):
        from src.health.circuit_breaker import CircuitBreakerRegistry
        return CircuitBreakerRegistry()

@pytest.fixture
def engine() -> RoutingEngine:
    # Create three models with different capabilities and priorities
    m1 = make_model("model-code", priority=1, capabilities=[ModelCapability.CODE])
    m2 = make_model("model-chat", priority=2, capabilities=[ModelCapability.CHAT])
    m3 = make_model("model-reason", priority=3, capabilities=[ModelCapability.REASONING])
    registry = DummyRegistry([m1, m2, m3])
    monitor = DummyMonitor(["model-code", "model-chat", "model-reason"])  # all healthy
    return RoutingEngine(model_registry=registry, monitor=monitor)

@pytest.mark.asyncio
async def test_intent_strategy_selects_code_model(engine: RoutingEngine):
    messages = [{"role": "user", "content": "Can you write a Python function?"}]
    decision = await engine.route(messages, strategy=RoutingStrategy.INTENT)
    assert decision.selected_model.id == "model-code"
    # Verify fallback chain respects max_fallbacks from settings (default 3)
    assert len(decision.fallback_models) <= settings.model_routing_max_fallbacks

@pytest.mark.asyncio
async def test_cost_strategy_chooses_cheapest(engine: RoutingEngine):
    # Adjust costs to make model-chat cheapest
    for m in engine._registry.all_models():
        if m.id == "model-chat":
            m.cost_per_1k_prompt_tokens = 0.0005
            m.cost_per_1k_completion_tokens = 0.0005
        else:
            m.cost_per_1k_prompt_tokens = 0.01
            m.cost_per_1k_completion_tokens = 0.01
    decision = await engine.route([], strategy=RoutingStrategy.COST)
    assert decision.selected_model.id == "model-chat"

@pytest.mark.asyncio
async def test_latency_strategy_picks_fastest(engine: RoutingEngine):
    # Change avg_tokens_per_second to make model-reason fastest
    for m in engine._registry.all_models():
        if m.id == "model-reason":
            m.avg_tokens_per_second = 100.0
        else:
            m.avg_tokens_per_second = 10.0
    decision = await engine.route([], strategy=RoutingStrategy.LATENCY)
    assert decision.selected_model.id == "model-reason"
