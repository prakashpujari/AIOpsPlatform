"""Integration tests for the AI Gateway chat routing (Phase 5)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

import sys, os
# Add the src directory to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from main import app
from apps.ai-gateway.src.core.config import settings
from apps.ai-gateway.src.registry.schemas import ModelDefinition, ModelCapability, ModelProvider, ModelTier
from apps.ai-gateway.src.router.routing_engine import RoutingDecision

client = TestClient(app)

# Helper to build a minimal ModelDefinition for the default model
def dummy_model() -> ModelDefinition:
    return ModelDefinition(
        id=settings.default_model,
        name="Dummy Model",
        provider=ModelProvider.VLLM,
        tier=ModelTier.BALANCED,
        capabilities=[ModelCapability.CHAT],
        context_window=8192,
        max_output_tokens=2048,
        gpu_vram_gb=8.0,
        cost_per_1k_prompt_tokens=0.001,
        cost_per_1k_completion_tokens=0.0015,
        avg_tokens_per_second=30.0,
        priority=1,
    )

@pytest.fixture
def dummy_decision() -> RoutingDecision:
    return RoutingDecision(
        selected_model=dummy_model(),
        strategy_used="intent",
        fallback_models=[],
        routing_reason="test",
        estimated_cost_usd=0.0,
        estimated_latency_ms=0.0,
    )

@pytest.mark.asyncio
async def test_chat_complete_uses_routing(dummy_decision: RoutingDecision):
    request_json = {
        "messages": [{"role": "user", "content": "Hello"}],
        "strategy": "intent",
        "model": None,
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False,
    }

    # Patch the routing_engine.route to return our dummy decision
    with patch("apps.ai-gateway.src.router.routing_engine.routing_engine.route", AsyncMock(return_value=dummy_decision)):
        # Patch the fallback_engine.execute_with_fallback to return a deterministic response
        fake_resp = {"choices": [{"message": {"content": "Hello back!"}}], "usage": {"prompt_tokens": 5, "completion_tokens": 5}}
        with patch("apps.ai-gateway.src.fallback.fallback_engine.execute_with_fallback", AsyncMock(return_value=(fake_resp, dummy_decision.selected_model))):
            response = client.post("/v1/chat/complete", json=request_json)
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "Hello back!"
            assert data["model_used"] == settings.default_model
            assert data["strategy_used"] == "intent"
            # Verify that routing info appears in the response
            assert "routing_reason" in data
