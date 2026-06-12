"""Gateway health and model info endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from ..cost.cost_engine import cost_engine
from ..health.health_monitor import health_monitor
from ..registry.model_registry import registry
from .schemas import HealthResponse, ModelInfo

router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.get("/health", response_model=HealthResponse)
async def gateway_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        models=health_monitor.all_health(),
        cost_summary=cost_engine.summary(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/routing")
async def routing_info() -> dict:
    """Expose current routing configuration and fallback chain for the default model."""
    # Gather fallback chain using the current healthy candidates
    from ..router.routing_engine import routing_engine
    from ..router.strategies.failover_strategy import get_fallback_chain

    candidates = routing_engine._get_healthy_candidates()
    default_model = registry.get(settings.default_model)
    fallbacks = []
    if default_model:
        fallbacks = [m.id for m in get_fallback_chain(default_model, candidates, max_fallbacks=settings.model_routing_max_fallbacks)]
    return {
        "default_model": settings.default_model,
        "strategy": settings.model_routing_strategy,
        "max_fallbacks": settings.model_routing_max_fallbacks,
        "fallback_models": fallbacks,
    }



@router.get("/models", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    all_health = health_monitor.all_health()
    models = []
    for m in registry.all_models():
        h = all_health.get(m.id, {})
        models.append(ModelInfo(
            id=m.id,
            name=m.name,
            provider=m.provider.value,
            tier=m.tier.value,
            capabilities=[c.value for c in m.capabilities],
            context_window=m.context_window,
            gpu_vram_gb=m.gpu_vram_gb,
            cost_per_1k_prompt=m.cost_per_1k_prompt_tokens,
            cost_per_1k_completion=m.cost_per_1k_completion_tokens,
            status=h.get("status", "unknown"),
            latency_ms=h.get("latency_ms", 0.0),
            circuit_state=h.get("circuit_state", "closed"),
        ))
    return models


@router.get("/costs")
async def cost_summary() -> dict:
    return cost_engine.summary()
