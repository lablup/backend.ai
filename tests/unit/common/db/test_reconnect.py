from __future__ import annotations

import asyncpg
import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from ai.backend.common.db.reconnect import PostgresReconnectErrorClassifier


def _wrap(orig: BaseException, *, invalidated: bool = False) -> DBAPIError:
    return DBAPIError("SELECT 1", {}, orig, connection_invalidated=invalidated)


class _PgcodeError(Exception):
    def __init__(self, pgcode: str) -> None:
        super().__init__(pgcode)
        self.pgcode = pgcode


def _cause(outer: BaseException, cause: BaseException) -> BaseException:
    outer.__cause__ = cause
    return outer


def _with_context(outer: BaseException, context: BaseException) -> BaseException:
    outer.__context__ = context
    return outer


RECONNECT_ERRORS: list[tuple[str, BaseException]] = [
    ("connection_invalidated", _wrap(ValueError("x"), invalidated=True)),
    ("sqlstate 08006", asyncpg.exceptions.ConnectionFailureError("x")),
    ("sqlstate 08001", asyncpg.exceptions.ClientCannotConnectError("x")),
    ("sqlstate 25006", asyncpg.exceptions.ReadOnlySQLTransactionError("x")),
    ("sqlstate 57P01", asyncpg.exceptions.AdminShutdownError("x")),
    ("sqlstate 57P02", asyncpg.exceptions.CrashShutdownError("x")),
    ("sqlstate 57P03", asyncpg.exceptions.CannotConnectNowError("x")),
    ("connection does not exist", asyncpg.exceptions.ConnectionDoesNotExistError("x")),
    ("target server attribute", asyncpg.TargetServerAttributeNotMatched("x")),
    ("connection refused", ConnectionRefusedError("x")),
    ("connection reset", ConnectionResetError("x")),
    ("os error", OSError("x")),
    ("timeout", TimeoutError("x")),
    ("wrapped sqlstate in orig", _wrap(asyncpg.exceptions.AdminShutdownError("x"))),
    ("wrapped pgcode in orig", _wrap(_PgcodeError("57P03"))),
    (
        "sqlstate in cause of orig",
        _wrap(_cause(RuntimeError("x"), asyncpg.exceptions.ReadOnlySQLTransactionError("x"))),
    ),
    ("wrapped os error", OperationalError("SELECT 1", {}, ConnectionResetError("x"))),
]

NON_RECONNECT_ERRORS: list[tuple[str, BaseException]] = [
    ("serialization failure", asyncpg.exceptions.SerializationError("x")),
    ("wrapped serialization failure", _wrap(asyncpg.exceptions.SerializationError("x"))),
    ("unique violation", asyncpg.exceptions.UniqueViolationError("x")),
    ("syntax error", asyncpg.exceptions.PostgresSyntaxError("x")),
    ("interface error", asyncpg.InterfaceError("x")),
    ("value error", ValueError("x")),
    ("wrapped value error", _wrap(ValueError("x"))),
    (
        "os error only in __context__",
        _with_context(IntegrityError("INSERT", {}, ValueError("x")), OSError("x")),
    ),
]


class TestPostgresReconnectErrorClassifier:
    @pytest.mark.parametrize(
        "error", [e for _, e in RECONNECT_ERRORS], ids=[n for n, _ in RECONNECT_ERRORS]
    )
    def test_reconnect_errors(self, error: BaseException) -> None:
        assert PostgresReconnectErrorClassifier().is_reconnect_error(error) is True

    @pytest.mark.parametrize(
        "error", [e for _, e in NON_RECONNECT_ERRORS], ids=[n for n, _ in NON_RECONNECT_ERRORS]
    )
    def test_non_reconnect_errors(self, error: BaseException) -> None:
        assert PostgresReconnectErrorClassifier().is_reconnect_error(error) is False
