"""
Fair share domain exceptions.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class FairShareError(BackendAIError):
    """Base class for fair share domain errors."""

    error_type = "https://api.backend.ai/probs/fair-share-error"
    error_title = "Fair share operation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class FairShareNotFoundError(FairShareError):
    """Raised when a fair share entity is not found."""

    error_type = "https://api.backend.ai/probs/fair-share-not-found"
    error_title = "Fair share entity not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )
