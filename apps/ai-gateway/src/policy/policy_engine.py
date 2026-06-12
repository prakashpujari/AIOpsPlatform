"""Policy engine — orchestrates PII masking and injection detection before routing."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..core.config import settings
from ..core.exceptions import PIIDetectedError, PromptInjectionError
from .pii_masker import PIIMasker, pii_masker
from .prompt_injection_detector import PromptInjectionDetector, injection_detector

logger = logging.getLogger(__name__)


@dataclass
class PolicyResult:
    sanitized_messages: list[dict]
    pii_detected: bool
    injection_detected: bool
    detected_pii_entities: list[str]


class PolicyEngine:
    """Applies all safety policies to the incoming prompt before model routing."""

    def __init__(
        self,
        masker: PIIMasker | None = None,
        detector: PromptInjectionDetector | None = None,
    ) -> None:
        self._masker = masker or pii_masker
        self._detector = detector or injection_detector

    async def apply(self, messages: list[dict]) -> PolicyResult:
        """
        Process a messages array (OpenAI-compatible format).
        Raises PolicyViolationError if a policy blocks the request.
        """
        sanitized: list[dict] = []
        pii_entities_total: list[str] = []
        any_pii = False
        any_injection = False

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if not isinstance(content, str):
                sanitized.append(msg)
                continue

            # ── Prompt injection check (fail-closed) ───────────────────────
            if settings.prompt_injection_detection_enabled and role == "user":
                inj = self._detector.detect(content)
                if inj.is_injection:
                    any_injection = True
                    raise PromptInjectionError(
                        "Prompt injection attempt detected",
                        details={"matched_patterns": inj.matched_patterns[:5]},
                    )

            # ── PII masking ────────────────────────────────────────────────
            if settings.pii_masking_enabled:
                mask_result = self._masker.mask(content)
                if mask_result.was_masked:
                    any_pii = True
                    pii_entities_total.extend(mask_result.detected_entities)
                    content = mask_result.masked_text
                    logger.info(
                        "PII masked in %s message: %s",
                        role, mask_result.detected_entities
                    )

            # ── Max prompt length ──────────────────────────────────────────
            if len(content) > settings.max_prompt_length:
                logger.warning("Prompt truncated from %d to %d chars", len(content), settings.max_prompt_length)
                content = content[: settings.max_prompt_length]

            sanitized.append({**msg, "content": content})

        return PolicyResult(
            sanitized_messages=sanitized,
            pii_detected=any_pii,
            injection_detected=any_injection,
            detected_pii_entities=list(set(pii_entities_total)),
        )


# Singleton
policy_engine = PolicyEngine()
