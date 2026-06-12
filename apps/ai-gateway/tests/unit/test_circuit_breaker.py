"""Unit tests — circuit breaker state machine."""

from __future__ import annotations

import asyncio

import pytest

from src.health.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitState


@pytest.fixture
def breaker() -> CircuitBreaker:
    return CircuitBreaker(model_id="test-model", failure_threshold=3, recovery_timeout_seconds=1)


@pytest.mark.asyncio
async def test_starts_closed(breaker: CircuitBreaker) -> None:
    assert breaker.state == CircuitState.CLOSED
    assert not await breaker.is_open()


@pytest.mark.asyncio
async def test_opens_after_threshold(breaker: CircuitBreaker) -> None:
    for _ in range(3):
        await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert await breaker.is_open()


@pytest.mark.asyncio
async def test_transitions_to_half_open_after_timeout(breaker: CircuitBreaker) -> None:
    for _ in range(3):
        await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    await asyncio.sleep(1.1)  # wait for recovery timeout
    is_open = await breaker.is_open()
    assert not is_open
    assert breaker.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_closes_after_successes_in_half_open(breaker: CircuitBreaker) -> None:
    for _ in range(3):
        await breaker.record_failure()
    await asyncio.sleep(1.1)
    await breaker.is_open()  # triggers half-open
    # need success_threshold=2 successes
    await breaker.record_success()
    await breaker.record_success()
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_success_in_closed_resets_failures(breaker: CircuitBreaker) -> None:
    await breaker.record_failure()
    await breaker.record_failure()
    await breaker.record_success()
    assert breaker.failure_count == 0


def test_registry_creates_breaker_per_model() -> None:
    reg = CircuitBreakerRegistry(failure_threshold=5, recovery_timeout_seconds=60)
    b1 = reg.get("model-a")
    b2 = reg.get("model-b")
    b3 = reg.get("model-a")
    assert b1 is b3
    assert b1 is not b2


def test_registry_all_states() -> None:
    reg = CircuitBreakerRegistry()
    reg.get("m1")
    reg.get("m2")
    states = reg.all_states()
    assert "m1" in states
    assert "m2" in states
