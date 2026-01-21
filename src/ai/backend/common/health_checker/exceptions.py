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
    """

    pass


class HttpHealthCheckError(HealthCheckError, web.HTTPServiceUnavailable):
    """Raised when HTTP endpoint health check fails."""

    error_type = "https://api.backend.ai/probs/http-health-check-failed"
    error_title = "HTTP health check failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ValkeyHealthCheckError(HealthCheckError, web.HTTPServiceUnavailable):
    """Raised when Valkey/Redis health check fails."""

    error_type = "https://api.backend.ai/probs/valkey-health-check-failed"
    error_title = "Valkey health check failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class EtcdHealthCheckError(HealthCheckError, web.HTTPServiceUnavailable):
    """Raised when etcd health check fails."""

    error_type = "https://api.backend.ai/probs/etcd-health-check-failed"
    error_title = "Etcd health check failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class DatabaseHealthCheckError(HealthCheckError, web.HTTPServiceUnavailable):
    """Raised when database health check fails."""

    error_type = "https://api.backend.ai/probs/database-health-check-failed"
    error_title = "Database health check failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class DockerHealthCheckError(HealthCheckError, web.HTTPServiceUnavailable):
    """Raised when Docker health check fails."""

    error_type = "https://api.backend.ai/probs/docker-health-check-failed"
    error_title = "Docker health check failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


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
