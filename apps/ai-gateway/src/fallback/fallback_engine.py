"""Fallback engine — retries a request through the fallback chain on failure."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from ..core.config import settings
from ..core.exceptions import GatewayError, NoHealthyModelError
from ..health.health_monitor import ModelHealthMonitor, health_monitor
from ..registry.model_registry import ModelRegistry, registry
from ..registry.schemas import ModelDefinition, RoutingDecision

logger = logging.getLogger(__name__)


class FallbackEngine:
    """Executes the model call and retries through the fallback chain on failure."""

    def __init__(
        self,
        model_registry: ModelRegistry | None = None,
        monitor: ModelHealthMonitor | None = None,
    ) -> None:
        self._registry = model_registry or registry
        self._monitor = monitor or health_monitor

    async def execute_with_fallback(
        self,
        decision: RoutingDecision,
        call_fn,  # async callable(model: ModelDefinition) -> Any
        max_retries: int | None = None,
    ) -> tuple[Any, ModelDefinition]:
        """
        Try `decision.selected_model`, then each model in `decision.fallback_models`.
        Returns (result, model_used).
        """
        max_retries = max_retries or settings.max_routing_retries
        models_to_try: list[ModelDefinition] = [decision.selected_model]

        for fid in decision.fallback_models[:max_retries]:
            m = self._registry.get(fid)
            if m:
                models_to_try.append(m)

        last_error: Exception | None = None
        for model in models_to_try:
            # Skip any model whose circuit breaker is currently open
            breaker = self._monitor.circuit_registry().get(model.id)
            if await breaker.is_open():
                logger.debug("Skipping model %s due to open circuit", model.id)
                continue
            try:
                result = await asyncio.wait_for(
                    call_fn(model),
                    timeout=settings.routing_timeout_seconds,
                )
                await breaker.record_success()
                if model.id != decision.selected_model.id:
                    logger.info("Fallback succeeded on model %s", model.id)
                return result, model

            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.warning("Model %s timed out, trying next", model.id)
                await breaker.record_failure()

            except GatewayError:
                raise  # policy/budget errors propagate immediately

            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Model %s failed: %s, trying next", model.id, exc)
                await breaker.record_failure()

        raise NoHealthyModelError(
            f"All {len(models_to_try)} model(s) failed. Last error: {last_error}"
        )

    async def stream_with_fallback(
        self,
        decision: RoutingDecision,
        stream_fn,  # async callable(model) -> AsyncIterator[str]
    ) -> tuple[AsyncIterator[str], ModelDefinition]:
        """For streaming calls — return (async_generator, model_used)."""
        max_retries = settings.max_routing_retries
        models_to_try: list[ModelDefinition] = [decision.selected_model]
        for fid in decision.fallback_models[:max_retries]:
            m = self._registry.get(fid)
            if m:
                models_to_try.append(m)

        last_error: Exception | None = None
        for model in models_to_try:
            # Skip any model whose circuit breaker is currently open
            breaker = self._monitor.circuit_registry().get(model.id)
            if await breaker.is_open():
                logger.debug("Skipping streaming model %s due to open circuit", model.id)
                continue
            try:
                stream = await stream_fn(model)
                await breaker.record_success()
                if model.id != decision.selected_model.id:
                    logger.info("Streaming fallback succeeded on model %s", model.id)
                return stream, model
            except GatewayError:
                await breaker.record_failure()
                raise
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Streaming model %s failed: %s", model.id, exc)
                await breaker.record_failure()

        raise NoHealthyModelError(
            f"All streaming models failed. Last error: {last_error}"
        )


# Singleton
fallback_engine = FallbackEngine()
