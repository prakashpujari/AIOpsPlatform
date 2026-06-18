"""Background health monitor — polls all model endpoints every N seconds."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx

from ..core.config import settings
from ..registry.model_registry import registry
from ..registry.schemas import ModelProvider, ModelStatus
from .circuit_breaker import CircuitBreakerRegistry

logger = logging.getLogger(__name__)


from prometheus_client import Gauge

# Metrics for model health and latency
MODEL_HEALTH = Gauge(
    "gateway_model_health", "Health status of each model (0=unknown,1=healthy,2=degraded,3=unhealthy,4=circuit_open)", ["model"]
)
MODEL_LATENCY_MS = Gauge(
    "gateway_model_latency_ms", "Observed latency in milliseconds for each model", ["model"]
)
# CIRCUIT_STATE is defined in circuit_breaker.py to avoid duplication
from .circuit_breaker import CIRCUIT_STATE

class ModelHealthMonitor:
    """Polls model endpoints and maintains a health state map."""

    def __init__(
        self,
        circuit_registry: CircuitBreakerRegistry | None = None,
        poll_interval: int | None = None,
    ) -> None:
        self._circuit_registry = circuit_registry or CircuitBreakerRegistry(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout_seconds=settings.circuit_breaker_recovery_timeout,
        )
        self._poll_interval = poll_interval or settings.health_check_interval_seconds
        self._health: dict[str, ModelStatus] = {}
        self._latency: dict[str, float] = {}
        self._task: asyncio.Task | None = None  # type: ignore[type-arg]
        # Initialize cloud providers as healthy immediately
        for model in registry.all_models():
            if model.provider == ModelProvider.GROQ:
                self._health[model.id] = ModelStatus.HEALTHY
                MODEL_HEALTH.labels(model=model.id).set(1)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._task = asyncio.create_task(self._poll_loop(), name="health-monitor")
        logger.info("Health monitor started (interval=%ds)", self._poll_interval)

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")

    # ── Public API ───────────────────────────────────────────────────────────

    def get_status(self, model_id: str) -> ModelStatus:
        return self._health.get(model_id, ModelStatus.UNKNOWN)

    def get_latency_ms(self, model_id: str) -> float:
        return self._latency.get(model_id, 0.0)

    def healthy_models(self) -> list[str]:
        return [
            mid for mid, status in self._health.items()
            if status in (ModelStatus.HEALTHY, ModelStatus.DEGRADED)
        ]

    def all_health(self) -> dict[str, dict]:
        result = {}
        for model in registry.all_models():
            breaker = self._circuit_registry.get(model.id)
            result[model.id] = {
                "status": self._health.get(model.id, ModelStatus.UNKNOWN).value,
                "latency_ms": self._latency.get(model.id, 0.0),
                "circuit_state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "circuit_open_until": (
                    breaker.open_until.isoformat() if breaker.open_until else None
                ),
            }
        return result

    def circuit_registry(self) -> CircuitBreakerRegistry:
        return self._circuit_registry

    # ── Internal ─────────────────────────────────────────────────────────────

    async def _poll_loop(self) -> None:
        # First pass: ensure cloud providers are healthy immediately
        for model in registry.all_models():
            if model.provider == ModelProvider.GROQ:
                self._health[model.id] = ModelStatus.HEALTHY
                MODEL_HEALTH.labels(model=model.id).set(1)
        while True:
            await self._check_all()
            await asyncio.sleep(self._poll_interval)

    async def _check_all(self) -> None:
        tasks = [self._check_model(m) for m in registry.all_models()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_model(self, model) -> None:  # type: ignore[no-untyped-def]
        url = self._health_url(model)
        if url is None:
            # For cloud providers like Groq, assume healthy (no local health check)
            self._health[model.id] = ModelStatus.HEALTHY
            return

        t0 = time.monotonic()
        new_status = ModelStatus.UNKNOWN
        elapsed_ms = 0.0
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
            elapsed_ms = (time.monotonic() - t0) * 1000
            self._latency[model.id] = elapsed_ms

            if resp.status_code == 200:
                await self._circuit_registry.get(model.id).record_success()
                new_status = ModelStatus.DEGRADED if elapsed_ms > 2000 else ModelStatus.HEALTHY
            else:
                await self._handle_failure(model.id)
                new_status = self._health.get(model.id, ModelStatus.UNHEALTHY)

        except Exception as exc:  # noqa: BLE001
            logger.debug("Health check failed for %s: %s", model.id, exc)
            await self._handle_failure(model.id)
            new_status = self._health.get(model.id, ModelStatus.UNHEALTHY)

        # Update Prometheus gauges AFTER determining status
        MODEL_LATENCY_MS.labels(model=model.id).set(elapsed_ms)
        # Health status gauge: 1=healthy,2=degraded,3=unhealthy,4=circuit_open,0=unknown
        health_value = {
            ModelStatus.HEALTHY: 1,
            ModelStatus.DEGRADED: 2,
            ModelStatus.UNHEALTHY: 3,
            ModelStatus.CIRCUIT_OPEN: 4,
            ModelStatus.UNKNOWN: 0,
        }.get(new_status, 0)
        MODEL_HEALTH.labels(model=model.id).set(health_value)
        self._health[model.id] = new_status

    async def _handle_failure(self, model_id: str) -> None:
        breaker = self._circuit_registry.get(model_id)
        await breaker.record_failure()
        if await breaker.is_open():
            self._health[model_id] = ModelStatus.CIRCUIT_OPEN
        else:
            self._health[model_id] = ModelStatus.UNHEALTHY

    def _health_url(self, model) -> str | None:  # type: ignore[no-untyped-def]
        if model.provider == ModelProvider.VLLM:
            return f"{settings.vllm_base_url}/health"
        if model.provider == ModelProvider.OLLAMA:
            return f"{settings.ollama_base_url}/api/tags"
        if model.provider == ModelProvider.TGI:
            return f"{settings.tgi_base_url}/health"
        return None


# Singleton
health_monitor = ModelHealthMonitor()
