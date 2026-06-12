"""AI Gateway exceptions."""

from __future__ import annotations


class GatewayError(Exception):
    status_code: int = 500
    error_code: str = "GATEWAY_ERROR"

    def __init__(self, message: str, details: object = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NoHealthyModelError(GatewayError):
    status_code = 503
    error_code = "NO_HEALTHY_MODEL"


class PolicyViolationError(GatewayError):
    status_code = 400
    error_code = "POLICY_VIOLATION"


class PIIDetectedError(PolicyViolationError):
    error_code = "PII_DETECTED"


class PromptInjectionError(PolicyViolationError):
    error_code = "PROMPT_INJECTION_DETECTED"


class ContentFilterError(PolicyViolationError):
    error_code = "CONTENT_FILTERED"


class BudgetExceededError(GatewayError):
    status_code = 402
    error_code = "BUDGET_EXCEEDED"


class ModelTimeoutError(GatewayError):
    status_code = 504
    error_code = "MODEL_TIMEOUT"


class CircuitOpenError(GatewayError):
    status_code = 503
    error_code = "CIRCUIT_OPEN"


class RoutingError(GatewayError):
    status_code = 502
    error_code = "ROUTING_ERROR"
