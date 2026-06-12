"""Failover strategy — returns an ordered list of fallback models."""

from __future__ import annotations

from ...registry.model_registry import ModelRegistry, registry
from ...registry.schemas import ModelDefinition, ModelTier


def get_fallback_chain(
    primary: ModelDefinition,
    candidates: list[ModelDefinition],
    max_fallbacks: int = 3,
) -> list[ModelDefinition]:
    """
    Returns up to `max_fallbacks` fallback models, ordered by:
    1. Same tier first (comparable quality)
    2. Lower priority number (higher quality)
    3. Exclude the primary model
    """
    others = [m for m in candidates if m.id != primary.id]
    # prefer same tier, then any
    same_tier = sorted([m for m in others if m.tier == primary.tier], key=lambda m: m.priority)
    diff_tier = sorted([m for m in others if m.tier != primary.tier], key=lambda m: m.priority)
    chain = same_tier + diff_tier
    return chain[:max_fallbacks]
