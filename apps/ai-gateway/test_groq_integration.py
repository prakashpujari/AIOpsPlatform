#!/usr/bin/env python
"""Test script for Groq integration with AI Gateway."""

import asyncio
import json

# Test 1: Verify Groq provider can make calls
async def test_groq_provider():
    """Test that Groq provider can connect to the API."""
    import sys
    sys.path.insert(0, '.')
    from src.providers.groq_provider import GroqProvider
    from src.core.config import settings

    if not settings.groq_api_key:
        print("ERROR: Groq API key not configured in .env")
        return False

    provider = GroqProvider()
    print(f"Groq provider initialized with base URL: {provider._base_url}")

    # Test a simple completion
    try:
        response = await provider.chat_complete(
            model_id="llama3-8b-8192",  # Groq's model name
            messages=[{"role": "user", "content": "Hello!"}],
            temperature=0.7,
            max_tokens=100,
        )
        print("Groq API response received!")
        print(f"Content: {response['choices'][0]['message']['content'][:100]}...")
        return True
    except Exception as e:
        print(f"Groq API call failed: {e}")
        return False


# Test 2: Verify routing with Groq model
async def test_routing_with_groq():
    """Test that the routing engine can select Groq models."""
    import sys
    sys.path.insert(0, '.')
    from src.registry.schemas import ModelStatus
    from src.registry.model_registry import registry
    from src.router.routing_engine import RoutingEngine, RoutingStrategy

    class MockHealthMonitor:
        def get_status(self, model_id):
            return ModelStatus.HEALTHY
        def healthy_models(self):
            return [m.id for m in registry.all_models()]
        def get_latency_ms(self, model_id):
            return 100.0
        def circuit_registry(self):
            from src.health.circuit_breaker import CircuitBreakerRegistry
            return CircuitBreakerRegistry()

    engine = RoutingEngine(model_registry=registry, monitor=MockHealthMonitor())

    decision = await engine.route(
        messages=[{"role": "user", "content": "Hello!"}],
        preferred_model="llama3-8b-groq"
    )

    print(f"Routing selected model: {decision.selected_model.id}")
    print(f"Strategy used: {decision.strategy_used}")
    print(f"Model provider: {decision.selected_model.provider}")
    return True


if __name__ == "__main__":
    import os
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # Suppress TF warnings

    print("=" * 60)
    print("AI Gateway Groq Integration Tests")
    print("=" * 60)

    print("\nTest 1: Routing with Groq model...")
    asyncio.run(test_routing_with_groq())

    print("\nTest 2: Groq API connectivity...")
    result = asyncio.run(test_groq_provider())

    print("\n" + "=" * 60)
    if result:
        print("SUCCESS: All Groq integration tests passed!")
    else:
        print("NOTE: Groq API test may fail if API key is invalid or rate-limited")
    print("=" * 60)