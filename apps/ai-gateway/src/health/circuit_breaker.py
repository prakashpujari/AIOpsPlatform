"""Per-model circuit breaker (closed → open → half-open)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing — reject all calls
    HALF_OPEN = "half_open"  # Probe request allowed


@dataclass
class CircuitBreaker:
    model_id: str
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    success_threshold: int = 2          # successes needed in half-open to close

    # runtime state
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    opened_at: datetime | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def record_success(self) -> None:
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._close()
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    async def record_failure(self) -> None:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                return
            self.failure_count += 1
            self.success_count = 0
            if self.failure_count >= self.failure_threshold:
                self._open()

    async def is_open(self) -> bool:
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return False
            if self.state == CircuitState.OPEN and self._recovery_elapsed():
                self._half_open()
                return False          # allow the probe request
            return self.state == CircuitState.OPEN

    def _open(self) -> None:
        # Update Prometheus gauge for circuit state (1 = open)
        from prometheus_client import Gauge
        CIRCUIT_STATE.labels(model=self.model_id).set(1)
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now(timezone.utc)
        logger.warning("Circuit OPEN for model %s after %d failures", self.model_id, self.failure_count)

    def _half_open(self) -> None:
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info("Circuit HALF-OPEN for model %s — probing", self.model_id)

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        logger.info("Circuit CLOSED for model %s", self.model_id)

    def _recovery_elapsed(self) -> bool:
        if self.opened_at is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout_seconds

    @property
    def open_until(self) -> datetime | None:
        if self.state == CircuitState.OPEN and self.opened_at:
            from datetime import timedelta
            return self.opened_at + timedelta(seconds=self.recovery_timeout_seconds)
        return None


from prometheus_client import Gauge

# Gauge for circuit breaker state per model (0=closed,1=open,2=half-open)
CIRCUIT_STATE = Gauge(
    "gateway_circuit_state", "Circuit breaker state for each model (0=closed,1=open,2=half-open)", ["model"]
)

class CircuitBreakerRegistry:
    """Manages one circuit breaker per model."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
    ) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds

    def get(self, model_id: str) -> CircuitBreaker:
        if model_id not in self._breakers:
            self._breakers[model_id] = CircuitBreaker(
                model_id=model_id,
                failure_threshold=self._failure_threshold,
                recovery_timeout_seconds=self._recovery_timeout,
            )
        return self._breakers[model_id]

    def all_states(self) -> dict[str, str]:
        return {mid: cb.state.value for mid, cb in self._breakers.items()}
