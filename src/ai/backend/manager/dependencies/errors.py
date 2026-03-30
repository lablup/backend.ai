"""
Exceptions related to dependency management.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidManagerKeypairError(BackendAIError):
    """Raised when manager secret key is missing from the keypair file."""

    error_type = "https://api.backend.ai/probs/dependency/invalid-manager-keypair"
    error_title = "Invalid manager keypair configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class DependencyInitializationError(BackendAIError):
    """Raised when a required dependency fails to initialize during Composer startup."""

    error_type = "https://api.backend.ai/probs/dependency/initialization-failure"
    error_title = "Dependency initialization failure."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
