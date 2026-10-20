from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa

from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.unified import DatabaseConfig
from ai.backend.manager.repositories.db.engine import connect_database
from ai.backend.testutils.bootstrap import POSTGRES_MAINTENANCE_DB, POSTGRES_PASSWORD, POSTGRES_USER

CONNECT_TIMEOUT = 0.5


@pytest.fixture
async def silent_member() -> AsyncIterator[HostPortPair]:
    """A member that accepts TCP connections and never answers the startup message."""
    accepted: list[asyncio.StreamWriter] = []

    async def _hold(_reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        accepted.append(writer)

    server = await asyncio.start_server(_hold, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    yield HostPortPair(host="127.0.0.1", port=port)
    for writer in accepted:
        writer.close()
    server.close()
    await server.wait_closed()


def _db_config(addrs: list[HostPortPair]) -> DatabaseConfig:
    return DatabaseConfig.model_validate({
        "addrs": addrs,
        "connect_timeout": CONNECT_TIMEOUT,
        "name": POSTGRES_MAINTENANCE_DB,
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
    })


class TestConnectDatabase:
    async def test_engine_connects_past_silent_member(
        self,
        postgres_container: tuple[str, HostPortPair],
        silent_member: HostPortPair,
    ) -> None:
        _, postgres_addr = postgres_container

        async with connect_database(_db_config([silent_member, postgres_addr])) as engine:
            async with engine.begin() as conn:
                result = await conn.execute(sa.text("SELECT pg_is_in_recovery()"))

        assert result.scalar() is False
