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


class MissingFrontendConfigError(BackendAIError):
    """Raised when frontend configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-frontend-config"
    error_title = "Frontend configuration is missing."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )
