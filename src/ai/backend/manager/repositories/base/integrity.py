"""Integrity error parsing and matching utilities."""

from __future__ import annotations

from collections.abc import Sequence
from typing import NoReturn

import sqlalchemy as sa
from asyncpg.exceptions import PostgresError

from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    ExclusionViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    RepositoryIntegrityError,
    UniqueConstraintViolationError,
)

from .types import IntegrityErrorCheck

_SQLSTATE_TO_ERROR: dict[str, type[RepositoryIntegrityError]] = {
    "23505": UniqueConstraintViolationError,
    "23503": ForeignKeyViolationError,
    "23514": CheckConstraintViolationError,
    "23502": NotNullViolationError,
    "23P01": ExclusionViolationError,
}

_MESSAGE_KEYWORDS: list[tuple[str, type[RepositoryIntegrityError]]] = [
    ("unique constraint", UniqueConstraintViolationError),
    ("unique violation", UniqueConstraintViolationError),
    ("foreign key", ForeignKeyViolationError),
    ("not-null constraint", NotNullViolationError),
    ("null value in column", NotNullViolationError),
    ("check constraint", CheckConstraintViolationError),
    ("exclusion constraint", ExclusionViolationError),
]


def parse_integrity_error(e: sa.exc.IntegrityError) -> RepositoryIntegrityError:
    """Parse a SQLAlchemy IntegrityError into a structured RepositoryIntegrityError.

    Classification strategy:
    1. Primary: use SQLSTATE code from asyncpg's ``orig.sqlstate``
    2. Fallback: match keywords in the error message string

    Diagnostic attributes (constraint_name, table_name, column_name, detail)
    are extracted directly from asyncpg's ``PostgresError`` when available.
    """
    orig = e.orig
    pgcode: str | None = None
    constraint_name: str | None = None
    table_name: str | None = None
    column_name: str | None = None
    detail: str | None = None

    if isinstance(orig, PostgresError):
        pgcode = orig.sqlstate
        constraint_name = orig.constraint_name
        table_name = orig.table_name
        column_name = orig.column_name
        detail = orig.detail

    error_msg = str(e.orig) if e.orig is not None else str(e)
    kwargs = {
        "constraint_name": constraint_name,
        "table_name": table_name,
        "column_name": column_name,
        "detail": detail,
        "pgcode": pgcode,
    }

    # Primary classification: SQLSTATE code
    if pgcode is not None:
        error_cls = _SQLSTATE_TO_ERROR.get(pgcode)
        if error_cls is not None:
            return error_cls(extra_msg=error_msg, **kwargs)

    # Fallback classification: message-based keyword matching
    msg_lower = error_msg.lower()
    for keyword, error_cls in _MESSAGE_KEYWORDS:
        if keyword in msg_lower:
            return error_cls(extra_msg=error_msg, **kwargs)

    # Default fallback: generic integrity error
    return RepositoryIntegrityError(extra_msg=error_msg, **kwargs)


def _match_integrity_error(
    parsed: RepositoryIntegrityError,
    checks: Sequence[IntegrityErrorCheck],
) -> NoReturn:
    """Match a parsed integrity error against a sequence of checks and raise the appropriate error.

    Iterates through checks and raises the first matching domain error.
    If no check matches, raises the parsed ``RepositoryIntegrityError`` as fallback.
    """
    for check in checks:
        if not isinstance(parsed, check.violation_type):
            continue
        if check.constraint_name is not None and parsed.constraint_name != check.constraint_name:
            continue
        raise check.error from parsed
    raise parsed
