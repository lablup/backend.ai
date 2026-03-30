"""
Repository layer exceptions.
"""

from __future__ import annotations

from typing import Any

from aiohttp import web

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


class RepositoryIntegrityError(RepositoryError, web.HTTPConflict):
    """Base class for integrity constraint violation errors.

    Carries structured attributes extracted from asyncpg diagnostics.
    """

    error_type = "https://api.backend.ai/probs/integrity-error"
    error_title = "Integrity constraint violated."

    constraint_name: str | None
    table_name: str | None
    column_name: str | None
    detail: str | None
    pgcode: str | None

    def __init__(
        self,
        extra_msg: str | None = None,
        extra_data: Any | None = None,
        *,
        constraint_name: str | None = None,
        table_name: str | None = None,
        column_name: str | None = None,
        detail: str | None = None,
        pgcode: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(extra_msg=extra_msg, extra_data=extra_data, **kwargs)
        self.constraint_name = constraint_name
        self.table_name = table_name
        self.column_name = column_name
        self.detail = detail
        self.pgcode = pgcode

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.CONFLICT,
        )


class UniqueConstraintViolationError(RepositoryIntegrityError):
    """Raised when a unique constraint is violated (SQLSTATE 23505)."""

    error_type = "https://api.backend.ai/probs/unique-constraint-violation"
    error_title = "Unique constraint violated."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ForeignKeyViolationError(RepositoryIntegrityError):
    """Raised when a foreign key constraint is violated (SQLSTATE 23503)."""

    error_type = "https://api.backend.ai/probs/foreign-key-violation"
    error_title = "Foreign key constraint violated."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class CheckConstraintViolationError(RepositoryIntegrityError):
    """Raised when a check constraint is violated (SQLSTATE 23514)."""

    error_type = "https://api.backend.ai/probs/check-constraint-violation"
    error_title = "Check constraint violated."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.CONFLICT,
        )


class NotNullViolationError(RepositoryIntegrityError):
    """Raised when a not-null constraint is violated (SQLSTATE 23502).

    Uses HTTP 400 Bad Request instead of the default 409 Conflict.
    """

    error_type = "https://api.backend.ai/probs/not-null-violation"
    error_title = "Not-null constraint violated."
    status_code = 400

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ExclusionViolationError(RepositoryIntegrityError):
    """Raised when an exclusion constraint is violated (SQLSTATE 23P01)."""

    error_type = "https://api.backend.ai/probs/exclusion-violation"
    error_title = "Exclusion constraint violated."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.CONFLICT,
        )
