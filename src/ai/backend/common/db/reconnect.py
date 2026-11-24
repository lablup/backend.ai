from __future__ import annotations

from typing import Final, override

import asyncpg
from sqlalchemy.exc import DBAPIError

from ai.backend.common.resilience.policies.retry import ReconnectErrorClassifier

_RECONNECT_SQLSTATES: Final = frozenset({
    "25006",  # read_only_sql_transaction: connected to a demoted leader
    "57P01",  # admin_shutdown
    "57P02",  # crash_shutdown
    "57P03",  # cannot_connect_now
})
_RECONNECT_SQLSTATE_CLASS: Final = "08"  # connection exception


class PostgresReconnectErrorClassifier(ReconnectErrorClassifier):
    """Judges connection loss and leader change errors of PostgreSQL."""

    @override
    def is_reconnect_error(self, error: BaseException) -> bool:
        for exc in self._iter_chain(error):
            if isinstance(exc, DBAPIError) and exc.connection_invalidated:
                return True
            if isinstance(
                exc,
                (
                    asyncpg.exceptions.ConnectionDoesNotExistError,
                    asyncpg.TargetServerAttributeNotMatched,
                    OSError,
                    TimeoutError,
                ),
            ):
                return True
            sqlstate = getattr(exc, "sqlstate", None) or getattr(exc, "pgcode", None)
            if isinstance(sqlstate, str) and (
                sqlstate.startswith(_RECONNECT_SQLSTATE_CLASS) or sqlstate in _RECONNECT_SQLSTATES
            ):
                return True
        return False

    def _iter_chain(self, error: BaseException) -> list[BaseException]:
        chain: list[BaseException] = []
        seen: set[int] = set()
        pending: list[BaseException | None] = [error]
        while pending:
            exc = pending.pop()
            if exc is None or id(exc) in seen:
                continue
            seen.add(id(exc))
            chain.append(exc)
            pending.append(getattr(exc, "orig", None))
            pending.append(exc.__cause__)
        return chain
