"""Domain and application exceptions."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"


class ValidationError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class AuthenticationError(AppError):
    status_code = 401
    error_code = "UNAUTHENTICATED"


class AuthorizationError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"


class RateLimitError(AppError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class ExternalServiceError(AppError):
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"


class AIGatewayError(AppError):
    status_code = 502
    error_code = "AI_GATEWAY_ERROR"


class DatabaseError(AppError):
    status_code = 503
    error_code = "DATABASE_ERROR"
