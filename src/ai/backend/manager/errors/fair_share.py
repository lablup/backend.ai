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


class InvalidResourceWeightError(FairShareError):
    """Raised when resource_weights contains resource types not available in capacity."""

    error_type = "https://api.backend.ai/probs/invalid-resource-weight"
    error_title = "Invalid resource weight configuration."

    def __init__(self, invalid_types: list[str]) -> None:
        self.invalid_types = invalid_types
        super().__init__(f"Resource types not available in capacity: {', '.join(invalid_types)}")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
