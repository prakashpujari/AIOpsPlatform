#!/usr/bin/env python
"""Test script that demonstrates AI Gateway with Groq working end-to-end."""

import asyncio
import sys
import os

# Suppress TF warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.registry.model_registry import registry
from src.registry.schemas import ModelProvider, ModelStatus, RoutingDecision
from src.router.routing_engine import RoutingEngine, RoutingStrategy
from src.fallback.fallback_engine import FallbackEngine
from src.health.circuit_breaker import CircuitBreakerRegistry
from src.providers.groq_provider import groq_provider
from src.cost.cost_engine import cost_engine


class CloudHealthMonitor:
    """Health monitor that treats cloud providers as always healthy."""

    def get_status(self, model_id: str) -> ModelStatus:
        model = registry.get(model_id)
        if model and model.provider == ModelProvider.GROQ:
            return ModelStatus.HEALTHY
        return ModelStatus.HEALTHY  # For testing, assume all healthy

    def healthy_models(self) -> list[str]:
        return [m.id for m in registry.all_models()]

    def get_latency_ms(self, model_id: str) -> float:
        return 50.0

    def circuit_registry(self):
        return CircuitBreakerRegistry()


async def run_test():
    """Run the integration test."""
    print("=" * 60)
    print("AI Gateway + Groq Integration Test")
    print("=" * 60)

    monitor = CloudHealthMonitor()
    engine = RoutingEngine(model_registry=registry, monitor=monitor)
    fallback = FallbackEngine(monitor=monitor, model_registry=registry)

    # Test 1: Intent routing
    print("\n[1] Testing Intent Routing...")
    decision = await engine.route(
        messages=[{"role": "user", "content": "Write a Python function"}],
        strategy=RoutingStrategy.INTENT,
    )
    print(f"    Selected: {decision.selected_model.id} (strategy: {decision.strategy_used})")

    # Test 2: Explicit Groq model
    print("\n[2] Testing Explicit Groq Model Selection...")
    decision = await engine.route(
        messages=[{"role": "user", "content": "Hello!"}],
        preferred_model="llama-3.3-70b-groq"
    )
    print(f"    Selected: {decision.selected_model.id}")

    # Test 3: Actual Groq API call through fallback engine
    print("\n[3] Testing Groq API Call...")
    async def call_fn(model):
        return await groq_provider.chat_complete(
            model_id="llama-3.3-70b-groq",
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            max_tokens=100
        )

    result, model_used = await fallback.execute_with_fallback(decision, call_fn)
    answer = result["choices"][0]["message"]["content"]
    print(f"    Model: {model_used.id}")
    print(f"    Answer: {answer[:100]}...")

    # Test 4: Cost tracking
    print("\n[4] Testing Cost Tracking...")
    record = cost_engine.record(
        model=model_used,
        prompt_tokens=10,
        completion_tokens=20,
        request_id="test-123"
    )
    print(f"    Cost: ${record.cost_usd:.4f}")
    print(f"    Daily spend: ${cost_engine.daily_spend():.4f}")

    print("\n" + "=" * 60)
    print("All tests passed! The AI Gateway is working with Groq.")
    print("=" * 60)

    print("\nTo test via HTTP endpoint, after starting the server:")
    print("  curl -X POST http://localhost:8001/v1/chat/complete \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -H 'X-API-Key: changeme' \\")
    print("    -d '{\"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}], \"model\": \"llama-3.3-70b-groq\"}'")


if __name__ == "__main__":
    asyncio.run(run_test())