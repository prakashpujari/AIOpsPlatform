"""PII masker using Microsoft Presidio — detects and anonymizes banking-relevant entities."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MaskResult:
    masked_text: str
    detected_entities: list[str]
    was_masked: bool


# Banking-specific regex patterns used as fallback when Presidio is unavailable
_REGEX_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("CREDIT_CARD", "CREDIT_CARD", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")),
    ("IBAN", "IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")),
    ("SSN", "SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("PHONE", "PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("EMAIL", "EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    ("ACCOUNT_NUMBER", "ACCOUNT_NUMBER", re.compile(r"\b\d{8,17}\b")),
    ("IP_ADDRESS", "IP_ADDRESS", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


class PIIMasker:
    """Masks PII using Presidio with regex fallback."""

    def __init__(self) -> None:
        self._analyzer = None
        self._anonymizer = None
        self._presidio_available = False
        self._try_load_presidio()

    def _try_load_presidio(self) -> None:
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
            self._presidio_available = True
            logger.info("Presidio PII engine loaded")
        except Exception:  # noqa: BLE001 — covers ImportError, spaCy/numpy load failures
            logger.warning("Presidio unavailable (import or model load failed) — falling back to regex masking")

    def mask(self, text: str, language: str = "en") -> MaskResult:
        if self._presidio_available:
            return self._mask_combined(text, language)
        return self._mask_regex(text)

    def _mask_combined(self, text: str, language: str) -> MaskResult:
        """Run both Presidio and regex, combine results."""
        presidio_result = self._mask_presidio(text, language)
        regex_result = self._mask_regex(text)

        # Combine detected entities
        all_entities = list(set(presidio_result.detected_entities + regex_result.detected_entities))

        # Use Presidio's masked text as base, then apply regex masking for any missed entities
        masked_text = presidio_result.masked_text
        was_masked = presidio_result.was_masked or regex_result.was_masked

        # If regex found additional entities, apply regex masking on top
        if regex_result.was_masked:
            # Re-run regex on the already masked text to catch any missed entities
            for name, placeholder, pattern in _REGEX_PATTERNS:
                if name in regex_result.detected_entities and name not in presidio_result.detected_entities:
                    masked_text, _ = pattern.subn(f"[{placeholder}]", masked_text)

        return MaskResult(
            masked_text=masked_text,
            detected_entities=all_entities,
            was_masked=was_masked,
        )

    def _mask_presidio(self, text: str, language: str) -> MaskResult:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        results = self._analyzer.analyze(text=text, language=language)
        if not results:
            return MaskResult(masked_text=text, detected_entities=[], was_masked=False)

        anonymized = self._anonymizer.anonymize(text=text, analyzer_results=results)
        entities = list({r.entity_type for r in results})
        logger.info("PII detected: %s", entities)
        return MaskResult(
            masked_text=anonymized.text,
            detected_entities=entities,
            was_masked=True,
        )

    def _mask_regex(self, text: str) -> MaskResult:
        result = text
        detected: list[str] = []
        for name, placeholder, pattern in _REGEX_PATTERNS:
            new_text, count = pattern.subn(f"[{placeholder}]", result)
            if count > 0:
                detected.append(name)
                result = new_text
        return MaskResult(
            masked_text=result,
            detected_entities=detected,
            was_masked=bool(detected),
        )

    def contains_pii(self, text: str, language: str = "en") -> bool:
        result = self.mask(text, language)
        return result.was_masked


# Singleton
pii_masker = PIIMasker()
