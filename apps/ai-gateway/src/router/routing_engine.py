"""Main routing engine — selects the optimal model for each request."""

from __future__ import annotations

import logging
import time
from enum import Enum

from ..core.config import settings
from ..core.exceptions import CircuitOpenError, NoHealthyModelError
from ..health.health_monitor import ModelHealthMonitor, health_monitor
from ..registry.model_registry import ModelRegistry, registry
from ..registry.schemas import ModelDefinition, ModelStatus, RoutingDecision
from .strategies.cost_strategy import select_cheapest
from .strategies.failover_strategy import get_fallback_chain
from .strategies.intent_strategy import select_by_intent
from .strategies.latency_strategy import select_fastest

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    INTENT = "intent"
    COST = "cost"
    LATENCY = "latency"
    QUALITY = "quality"


from prometheus_client import Counter, Histogram

# Metrics for routing decisions and model usage
MODEL_REQUEST_COUNT = Counter(
    "gateway_model_requests_total",
    "Total number of requests routed to each model",
    ["model"]
)
MODEL_LATENCY = Histogram(
    "gateway_model_latency_seconds",
    "Latency of request handling per model",
    ["model"]
)

class RoutingEngine:
    """Selects the optimal model given routing strategy, health state, and circuit breakers."""

    def __init__(
        self,
        model_registry: ModelRegistry | None = None,
        monitor: ModelHealthMonitor | None = None,
    ) -> None:
        self._registry = model_registry or registry
        self._monitor = monitor or health_monitor

    async def route(
        self,
        messages: list[dict],
        strategy: RoutingStrategy = RoutingStrategy.INTENT,
        preferred_model: str | None = None,
        required_capability: str | None = None,
    ) -> RoutingDecision:
        """Select a model and compute routing decision.

        Records the start time to calculate latency metrics and handles
        fallback chain creation. """
        start_time = time.time()
        """Return a RoutingDecision containing the selected model and fallback chain."""

        # ── Build healthy candidate pool ─────────────────────────────────────
        candidates = self._get_healthy_candidates()
        if not candidates:
            raise NoHealthyModelError("No healthy models available")

        # ── Honour explicit model preference ────────────────────────────────
        if preferred_model:
            explicit = self._registry.get(preferred_model)
            if explicit and explicit.id in {m.id for m in candidates}:
                fallbacks = get_fallback_chain(explicit, candidates)
                return RoutingDecision(
                    selected_model=explicit,
                    strategy_used="explicit",
                    fallback_models=[m.id for m in fallbacks],
                    routing_reason=f"caller_preferred_model={preferred_model}",
                    estimated_cost_usd=self._estimate_cost(messages, explicit),
                    estimated_latency_ms=self._estimate_latency(explicit),
                )

        # ── Apply strategy ────────────────────────────────────────────────────
        selected, reason = self._apply_strategy(strategy, messages, candidates)
        if selected is None:
            raise NoHealthyModelError("Strategy returned no model")

        fallbacks = get_fallback_chain(selected, candidates, max_fallbacks=settings.model_routing_max_fallbacks)
        # Increment routing decision metric
        from ..main import ROUTING_DECISIONS
        ROUTING_DECISIONS.labels(strategy=strategy.value, model=selected.id).inc()
        # Record request latency metric (seconds)
        elapsed = time.time() - start_time
        MODEL_LATENCY.labels(model=selected.id).observe(elapsed)
        return RoutingDecision(
            selected_model=selected,
            strategy_used=strategy.value,
            fallback_models=[m.id for m in fallbacks],
            routing_reason=reason,
            estimated_cost_usd=self._estimate_cost(messages, selected),
            estimated_latency_ms=self._estimate_latency(selected),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_healthy_candidates(self) -> list[ModelDefinition]:
        all_models = self._registry.all_models()
        healthy: list[ModelDefinition] = []

        for model in all_models:
            status = self._monitor.get_status(model.id)
            if status in (ModelStatus.HEALTHY, ModelStatus.DEGRADED):
                healthy.append(model)

        # Sort by priority as the stable base order
        return sorted(healthy, key=lambda m: m.priority)

    def _apply_strategy(
        self,
        strategy: RoutingStrategy,
        messages: list[dict],
        candidates: list[ModelDefinition],
    ) -> tuple[ModelDefinition | None, str]:
        if strategy == RoutingStrategy.COST:
            return select_cheapest(candidates)
        if strategy == RoutingStrategy.LATENCY:
            return select_fastest(candidates, self._monitor)
        if strategy == RoutingStrategy.QUALITY:
            # Quality = highest priority model (lowest priority number)
            best = min(candidates, key=lambda m: m.priority)
            return best, "quality=highest_priority"
        # Default: INTENT
        return select_by_intent(messages, candidates, self._registry)

    @staticmethod
    def _estimate_cost(messages: list[dict], model: ModelDefinition) -> float:
        total_chars = sum(len(m.get("content", "")) for m in messages)
        estimated_tokens = max(1, total_chars // 4)
        return (estimated_tokens / 1000) * model.cost_per_1k_prompt_tokens

    @staticmethod
    def _estimate_latency(model: ModelDefinition) -> float:
        # Rough TTFT estimate: 512 output tokens / throughput
        return (512 / model.avg_tokens_per_second) * 1000


# Singleton
routing_engine = RoutingEngine()
