"""Prompt injection detector — heuristic + pattern-based."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Patterns that signal prompt injection attempts
_INJECTION_PATTERNS: list[re.Pattern] = [
    # Classic jailbreaks
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    # System prompt extraction
    re.compile(r"(print|repeat|output|reveal|show)\s+(your\s+)?(system\s+prompt|instructions)", re.IGNORECASE),
    re.compile(r"what\s+(are\s+)?your\s+(system\s+)?instructions", re.IGNORECASE),
    # Role manipulation
    re.compile(r"you\s+are\s+now\s+(an?\s+)?(different|new|unrestricted|jailbroken)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+)?(?:unrestricted|uncensored|unfiltered|evil|DAN)", re.IGNORECASE),
    re.compile(r"\[SYSTEM\]|\[INST\]|\[\/INST\]", re.IGNORECASE),
    # Data exfiltration markers
    re.compile(r"<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>"),
    # Direct instruction injection
    re.compile(r"###\s*New\s+Instructions?:", re.IGNORECASE),
    re.compile(r"ASSISTANT:\s*Sure,\s*I\s+will", re.IGNORECASE),
]

# Suspicious token sequences (adversarial suffixes)
_ADVERSARIAL_TOKENS = [
    "SuffixAttack",
    "! ! ! ! !",
    "} } } } }",
    "\\n\\nHuman:",
    "\\nHuman:",
]


@dataclass
class InjectionResult:
    is_injection: bool
    matched_patterns: list[str]
    confidence: float  # 0.0 – 1.0


class PromptInjectionDetector:
    """Heuristic detector for prompt injection attacks."""

    def detect(self, text: str) -> InjectionResult:
        matched: list[str] = []

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                matched.append(pattern.pattern)

        for token in _ADVERSARIAL_TOKENS:
            if token in text:
                matched.append(f"adversarial_token:{token!r}")

        # Score: each match raises confidence, capped at 1.0
        confidence = min(1.0, len(matched) * 0.35)
        is_injection = confidence >= 0.35  # any single match triggers

        if is_injection:
            logger.warning("Prompt injection detected: %d patterns matched", len(matched))

        return InjectionResult(
            is_injection=is_injection,
            matched_patterns=matched,
            confidence=confidence,
        )


# Singleton
injection_detector = PromptInjectionDetector()
