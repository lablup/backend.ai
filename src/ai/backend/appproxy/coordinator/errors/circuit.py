"""
Circuit-related exceptions for the coordinator.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class CircuitCreationError(BackendAIError):
    """Raised when circuit creation fails."""

    error_type = "https://api.backend.ai/probs/appproxy/circuit-creation-failed"
    error_title = "Failed to create circuit."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class InvalidCircuitConfigError(BackendAIError):
    """Raised when circuit configuration is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy/invalid-circuit-config"
    error_title = "Invalid circuit configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class SubdomainAllocationError(BackendAIError):
    """Raised when a unique subdomain could not be allocated after retries."""

    error_type = "https://api.backend.ai/probs/appproxy/subdomain-allocation-failed"
    error_title = "Failed to allocate a unique subdomain."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class InvalidCircuitStateError(BackendAIError):
    """Raised when circuit state is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy/invalid-circuit-state"
    error_title = "Invalid circuit state."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )
