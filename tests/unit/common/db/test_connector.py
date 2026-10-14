from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import asyncpg
import pytest

from ai.backend.common.db.connector import PrimaryMemberConnector
from ai.backend.common.typed_validators import HostPortPair

# Matches the credentials of the `postgres_container` fixture.
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "develove"
POSTGRES_DB = "testing"

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


def _connector(members: list[HostPortPair]) -> PrimaryMemberConnector:
    return PrimaryMemberConnector(
        [(member.host, member.port) for member in members],
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        connect_timeout=CONNECT_TIMEOUT,
        connect_kwargs={},
    )


class TestPrimaryMemberConnector:
    async def test_silent_member_is_skipped_after_its_timeout(
        self,
        postgres_container: tuple[str, HostPortPair],
        silent_member: HostPortPair,
    ) -> None:
        _, postgres_addr = postgres_container
        connector = _connector([silent_member, postgres_addr])

        started = time.monotonic()
        conn = await connector.connect()
        elapsed = time.monotonic() - started
        try:
            assert await conn.fetchval("SELECT 1") == 1
        finally:
            await conn.close()

        assert CONNECT_TIMEOUT <= elapsed < CONNECT_TIMEOUT + 5

    async def test_next_connect_starts_from_last_primary(
        self,
        postgres_container: tuple[str, HostPortPair],
        silent_member: HostPortPair,
    ) -> None:
        _, postgres_addr = postgres_container
        connector = _connector([silent_member, postgres_addr])
        await (await connector.connect()).close()

        started = time.monotonic()
        conn = await connector.connect()
        elapsed = time.monotonic() - started
        await conn.close()

        assert elapsed < CONNECT_TIMEOUT

    async def test_standby_member_is_skipped_for_the_primary(
        self,
        postgres_container: tuple[str, HostPortPair],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, postgres_addr = postgres_container
        connector = _connector([postgres_addr, postgres_addr])
        in_hot_standby = AsyncMock(side_effect=[True, False, False])
        monkeypatch.setattr(connector, "_in_hot_standby", in_hot_standby)

        await (await connector.connect()).close()
        assert in_hot_standby.await_count == 2

        await (await connector.connect()).close()
        assert in_hot_standby.await_count == 3

    async def test_raises_when_every_member_is_standby(
        self,
        postgres_container: tuple[str, HostPortPair],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, postgres_addr = postgres_container
        connector = _connector([postgres_addr, postgres_addr])
        monkeypatch.setattr(connector, "_in_hot_standby", AsyncMock(return_value=True))

        with pytest.raises(asyncpg.TargetServerAttributeNotMatched):
            await connector.connect()

    async def test_raises_last_error_when_no_member_answers(
        self,
        silent_member: HostPortPair,
    ) -> None:
        connector = _connector([silent_member, silent_member])

        with pytest.raises(TimeoutError):
            await connector.connect()
