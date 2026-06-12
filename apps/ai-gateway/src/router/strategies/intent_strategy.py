"""Intent-based routing — maps detected intent to best-fit model capability."""

from __future__ import annotations

import re

from ...registry.model_registry import ModelRegistry, registry
from ...registry.schemas import ModelCapability, ModelDefinition


# Keyword → capability mapping (ordered by specificity)
_INTENT_MAP: list[tuple[re.Pattern, ModelCapability]] = [
    (re.compile(r"\b(code|script|function|debug|sql|query|python|javascript)\b", re.I), ModelCapability.CODE),
    (re.compile(r"\b(reason|analyze|why|root\s+cause|explain|rca|investigate)\b", re.I), ModelCapability.REASONING),
    (re.compile(r"\b(summarize|summary|brief|overview|tldr)\b", re.I), ModelCapability.SUMMARIZATION),
    (re.compile(r"\b(classify|categorize|label|detect|is\s+this)\b", re.I), ModelCapability.CLASSIFICATION),
    (re.compile(r"\b(search|find|retrieve|lookup|what\s+is)\b", re.I), ModelCapability.CHAT),
]


def detect_intent(messages: list[dict]) -> ModelCapability:
    """Return the dominant capability needed based on the last user message."""
    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    for pattern, capability in _INTENT_MAP:
        if pattern.search(last_user):
            return capability
    return ModelCapability.CHAT


def select_by_intent(
    messages: list[dict],
    candidates: list[ModelDefinition],
    reg: ModelRegistry | None = None,
) -> tuple[ModelDefinition | None, str]:
    """Pick the highest-priority candidate that supports the detected intent."""
    reg = reg or registry
    intent = detect_intent(messages)
    capable = [m for m in candidates if intent in m.capabilities]
    if not capable:
        capable = candidates  # fall back to all candidates
        reason = f"intent={intent.value} (no capable model, using fallback)"
    else:
        reason = f"intent={intent.value}"

    if not capable:
        return None, reason

    best = min(capable, key=lambda m: m.priority)
    return best, reason
