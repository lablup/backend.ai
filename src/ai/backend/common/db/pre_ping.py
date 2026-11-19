from __future__ import annotations

import asyncio
from typing import Any

import sqlalchemy as sa


class PrePingTimeout:
    """
    Bounds the pool pre-ping of an async engine by a timeout.

    SQLAlchemy pings through `Dialect.do_ping` when a connection is checked out; when the ping
    reports a disconnect, the pool invalidates the connection and connects again.
    `listen()` replaces `do_ping` of the engine's dialect, so the pre-ping runs once.
    On timeout the connection is terminated instead of cancelling the ping, as asyncpg
    cancels a command through a new connection that has no timeout.
    """

    _timeout: float

    def __init__(self, timeout: float) -> None:
        self._timeout = timeout

    def listen(self, engine: sa.engine.Engine) -> None:
        dialect = engine.dialect

        def do_ping(dbapi_connection: Any) -> bool:
            try:
                dbapi_connection.await_(self._ping(dbapi_connection))
            except TimeoutError as e:
                raise dialect.loaded_dbapi.InterfaceError(
                    "connection is closed: pre-ping timed out"
                ) from e
            except Exception as e:
                dbapi_connection._handle_exception(e)
            return True

        vars(dialect)["do_ping"] = do_ping

    async def _ping(self, dbapi_connection: Any) -> None:
        task = asyncio.ensure_future(dbapi_connection._async_ping())
        try:
            done, _ = await asyncio.wait({task}, timeout=self._timeout)
        except BaseException:
            dbapi_connection._connection.terminate()
            await asyncio.gather(task, return_exceptions=True)
            raise
        if task in done:
            task.result()
            return
        dbapi_connection._connection.terminate()
        await asyncio.gather(task, return_exceptions=True)
        raise TimeoutError
