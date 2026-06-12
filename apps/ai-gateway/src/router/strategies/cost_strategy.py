"""Cost-optimized routing — picks the cheapest model that meets capability requirements."""

from __future__ import annotations

from ...registry.schemas import ModelCapability, ModelDefinition


def select_cheapest(
    candidates: list[ModelDefinition],
    required_capability: ModelCapability | None = None,
) -> tuple[ModelDefinition | None, str]:
    pool = candidates
    if required_capability:
        pool = [m for m in candidates if required_capability in m.capabilities]
    if not pool:
        pool = candidates

    if not pool:
        return None, "no_candidates"

    best = min(
        pool,
        key=lambda m: m.cost_per_1k_prompt_tokens + m.cost_per_1k_completion_tokens,
    )
    return best, f"cost_optimized(${best.cost_per_1k_prompt_tokens:.5f}/1k)"
