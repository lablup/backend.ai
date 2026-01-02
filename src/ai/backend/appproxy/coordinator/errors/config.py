"""
Configuration-related exceptions for the coordinator.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class MissingTraefikConfigError(BackendAIError):
    """Raised when Traefik configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-traefik-config"
    error_title = "Traefik configuration is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingDatabaseURLError(BackendAIError):
    """Raised when database URL is missing from configuration."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-database-url"
    error_title = "Database URL is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingConfigFileError(BackendAIError):
    """Raised when configuration file is missing."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-config-file"
    error_title = "Configuration file is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingFrontendConfigError(BackendAIError):
    """Raised when frontend configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-frontend-config"
    error_title = "Frontend configuration is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidURLError(BackendAIError):
    """Raised when URL is invalid or missing required components."""

    error_type = "https://api.backend.ai/probs/appproxy/invalid-url"
    error_title = "Invalid URL."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidSessionParameterError(BackendAIError):
    """Raised when session parameter is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy/invalid-session-parameter"
    error_title = "Invalid session parameter."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidEnumTypeError(BackendAIError):
    """Raised when enum type is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy/invalid-enum-type"
    error_title = "Invalid enum type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class TransactionResultError(BackendAIError):
    """Raised when transaction did not produce a result."""

    error_type = "https://api.backend.ai/probs/appproxy/transaction-result-error"
    error_title = "Transaction did not produce a result."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class LockContextNotInitializedError(BackendAIError):
    """Raised when lock context is not initialized."""

    error_type = "https://api.backend.ai/probs/appproxy/lock-context-not-initialized"
    error_title = "Lock context is not initialized."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )


class CleanupContextNotInitializedError(BackendAIError):
    """Raised when cleanup context is not initialized."""

    error_type = "https://api.backend.ai/probs/appproxy/cleanup-context-not-initialized"
    error_title = "Cleanup context is not initialized."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )


class MissingProfilingConfigError(BackendAIError):
    """Raised when profiling configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-profiling-config"
    error_title = "Profiling configuration is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingRouteInfoError(BackendAIError):
    """Raised when route connection info is missing from Redis."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-route-info"
    error_title = "Route connection info is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingHealthCheckInfoError(BackendAIError):
    """Raised when health check info is missing from Redis."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-health-check-info"
    error_title = "Health check info is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
