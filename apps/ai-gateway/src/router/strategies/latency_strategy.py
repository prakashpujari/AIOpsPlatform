"""Latency-optimized routing — picks the fastest model (highest tokens/sec)."""

from __future__ import annotations

from ...registry.schemas import ModelDefinition
from ...health.health_monitor import ModelHealthMonitor


def select_fastest(
    candidates: list[ModelDefinition],
    monitor: ModelHealthMonitor | None = None,
) -> tuple[ModelDefinition | None, str]:
    if not candidates:
        return None, "no_candidates"

    # Filter by known healthy models if monitor is available
    if monitor:
        healthy_ids = set(monitor.healthy_models())
        healthy = [m for m in candidates if m.id in healthy_ids]
        pool = healthy if healthy else candidates
    else:
        pool = candidates

    best = max(pool, key=lambda m: m.avg_tokens_per_second)
    return best, f"latency_optimized({best.avg_tokens_per_second:.0f}tok/s)"
