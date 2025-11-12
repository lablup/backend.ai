from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class HealthCheckError(BackendAIError):
    """
    Base exception for all health check failures.

    Subclasses should inherit this along with appropriate web.HTTPxxx classes
    and implement the error_code() method.

    Example:
        class DatabaseHealthCheckError(HealthCheckError, web.HTTPServiceUnavailable):
            error_type = "https://api.backend.ai/probs/database-health-check-failed"
            error_title = "Database health check failed"

            def error_code(self) -> ErrorCode:
                return ErrorCode(
                    domain=ErrorDomain.BACKENDAI,
                    operation=ErrorOperation.GENERIC,
                    error_detail=ErrorDetail.UNAVAILABLE,
                )
    """

    pass


class HealthCheckerAlreadyRegistered(BackendAIError, web.HTTPConflict):
    """
    Raised when attempting to register a health checker that is already registered.
    """

    error_type = "https://api.backend.ai/probs/health-checker-already-registered"
    error_title = "Health checker already registered."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class HealthCheckerNotFound(BackendAIError, web.HTTPNotFound):
    """
    Raised when attempting to access a health checker that is not registered.
    """

    error_type = "https://api.backend.ai/probs/health-checker-not-found"
    error_title = "Health checker not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
