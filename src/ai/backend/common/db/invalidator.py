from __future__ import annotations

import sqlalchemy as sa
from asyncpg.exceptions import NoActiveSQLTransactionError
from sqlalchemy.engine.base import ExceptionContextImpl


class FailedBeginInvalidator:
    """
    Invalidates a pooled connection whose transaction failed to start, as asyncpg then
    keeps the failed transaction and turns every later transaction into a SAVEPOINT.
    """

    def listen(self, engine: sa.engine.Engine) -> None:
        sa.event.listen(engine, "handle_error", self._on_error)

    def _on_error(self, context: ExceptionContextImpl) -> None:
        if context.is_disconnect:
            return
        if not (
            self._begin_failed(context)
            or isinstance(context.original_exception.__cause__, NoActiveSQLTransactionError)
        ):
            return
        context.is_disconnect = True
        context.invalidate_pool_on_disconnect = False

    def _begin_failed(self, context: ExceptionContextImpl) -> bool:
        conn = context.connection
        if conn is None or conn.invalidated:
            return False
        # The SQLAlchemy asyncpg adapter keeps the transaction it failed to start, unstarted.
        adapter = conn.connection.dbapi_connection
        return (
            getattr(adapter, "_transaction", None) is not None
            and getattr(adapter, "_started", True) is False
        )
