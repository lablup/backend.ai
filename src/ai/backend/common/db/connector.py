from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

import asyncpg

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PrimaryMemberConnector:
    """
    Connects to the first member of a PostgreSQL cluster that is not in hot standby,
    starting from the member that answered as the primary last time.
    """

    _members: list[tuple[str, int]]
    _connect_timeout: float
    _connect_kwargs: dict[str, Any]
    _start: int

    def __init__(
        self,
        members: Sequence[tuple[str, int]],
        *,
        user: str,
        password: str | None,
        database: str,
        connect_timeout: float,
        connect_kwargs: Mapping[str, Any],
    ) -> None:
        self._members = list(members)
        self._connect_timeout = connect_timeout
        self._connect_kwargs = {
            **connect_kwargs,
            "user": user,
            "password": password,
            "database": database,
        }
        self._start = 0

    async def connect(self) -> asyncpg.Connection:
        last_error: Exception | None = None
        count = len(self._members)
        for index in [(self._start + offset) % count for offset in range(count)]:
            host, port = self._members[index]
            addr = f"{host}:{port}"
            try:
                conn = await asyncpg.connect(
                    host=host,
                    port=port,
                    timeout=self._connect_timeout,
                    **self._connect_kwargs,
                )
            except (OSError, asyncpg.PostgresError) as e:
                log.warning("database member connection failed (addr: {}, reason: {!r})", addr, e)
                last_error = e
                continue
            try:
                in_hot_standby = await self._in_hot_standby(conn)
            except (OSError, asyncpg.PostgresError) as e:
                conn.terminate()
                log.warning("database member connection failed (addr: {}, reason: {!r})", addr, e)
                last_error = e
                continue
            except BaseException:
                conn.terminate()
                raise
            if not in_hot_standby:
                self._start = index
                return conn
            conn.terminate()
            log.warning("database member is in hot standby (addr: {})", addr)
        if last_error is not None:
            raise last_error
        raise asyncpg.TargetServerAttributeNotMatched("None of the cluster members is a primary")

    async def _in_hot_standby(self, conn: asyncpg.Connection) -> bool:
        # PostgreSQL 14+ reports in_hot_standby at startup.
        reported: str | None = getattr(conn.get_settings(), "in_hot_standby", None)
        if reported is not None:
            return reported == "on"
        return bool(
            await conn.fetchval(
                "SELECT pg_catalog.pg_is_in_recovery()", timeout=self._connect_timeout
            )
        )
