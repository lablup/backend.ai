"""
Repository layer exceptions.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class RepositoryError(BackendAIError):
    """Base class for repository layer errors."""

    error_type = "https://api.backend.ai/probs/repository-error"
    error_title = "Repository operation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UpsertEmptyResultError(RepositoryError):
    """Raised when upsert operation returns no rows."""

    error_type = "https://api.backend.ai/probs/upsert-empty-result"
    error_title = "Upsert operation did not return any row."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UnsupportedCompositePrimaryKeyError(RepositoryError):
    """Raised when an operation requires a single-column primary key but the table has a composite key."""

    error_type = "https://api.backend.ai/probs/unsupported-composite-pk"
    error_title = "Unsupported composite primary key."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
