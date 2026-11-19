from __future__ import annotations

import asyncio
import io
import time
from collections.abc import AsyncIterator, Awaitable

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ai.backend.common.db.connector import PrimaryMemberConnector
from ai.backend.common.db.pre_ping import PrePingTimeout
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.testutils.bootstrap import POSTGRES_MAINTENANCE_DB, POSTGRES_PASSWORD, POSTGRES_USER

PRE_PING_TIMEOUT = 0.5
STEP_LIMIT = 10


async def _bounded[T](step: Awaitable[T], name: str) -> T:
    """Fails with the stacks of all tasks when the step does not finish."""
    try:
        async with asyncio.timeout(STEP_LIMIT):
            return await step
    except TimeoutError:
        out = io.StringIO()
        for task in asyncio.all_tasks():
            task.print_stack(file=out)
        raise AssertionError(f"{name} did not finish in {STEP_LIMIT}s\n{out.getvalue()}") from None


class _Relay:
    """
    A TCP relay in front of a server. `freeze()` stops forwarding on the open connections
    and keeps their sockets open, as a stopped server process does. New connections are served.
    """

    _target: HostPortPair
    _server: asyncio.Server | None
    _frozen: asyncio.Event
    _writers: list[asyncio.StreamWriter]
    _tasks: list[asyncio.Task[None]]
    port: int

    def __init__(self, target: HostPortPair) -> None:
        self._target = target
        self._server = None
        self._frozen = asyncio.Event()
        self._writers = []
        self._tasks = []
        self.port = 0

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        for writer in self._writers:
            writer.close()
        assert self._server is not None
        self._server.close()
        await self._server.wait_closed()

    def freeze(self) -> None:
        self._frozen.set()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        up_reader, up_writer = await asyncio.open_connection(self._target.host, self._target.port)
        self._writers += [writer, up_writer]
        frozen_here = asyncio.Event() if self._frozen.is_set() else self._frozen
        for src, dst in ((reader, up_writer), (up_reader, writer)):
            self._tasks.append(asyncio.create_task(self._pipe(src, dst, frozen_here)))

    async def _pipe(
        self,
        src: asyncio.StreamReader,
        dst: asyncio.StreamWriter,
        frozen: asyncio.Event,
    ) -> None:
        # A connection opened after freeze() gets its own, unset event and is never frozen.
        while data := await src.read(65536):
            if frozen.is_set():
                await asyncio.Event().wait()
            dst.write(data)
            await dst.drain()


@pytest.fixture
async def relay(postgres_container: tuple[str, HostPortPair]) -> AsyncIterator[_Relay]:
    _, addr = postgres_container
    relay = _Relay(addr)
    await relay.start()
    yield relay
    await _bounded(relay.close(), "relay close")


@pytest.fixture
async def engine(relay: _Relay) -> AsyncIterator[AsyncEngine]:
    connector = PrimaryMemberConnector(
        [("127.0.0.1", relay.port)],
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_MAINTENANCE_DB,
        connect_timeout=5,
        connect_kwargs={},
    )
    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=connector.connect,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True,
    )
    PrePingTimeout(PRE_PING_TIMEOUT).listen(engine.sync_engine)
    yield engine
    await _bounded(engine.dispose(), "engine dispose")


class TestPrePingTimeout:
    # pytest-timeout ends a hung test with a stack dump, whatever the event loop is doing.
    @pytest.mark.timeout(60)
    async def test_responding_connection_is_reused(self, engine: AsyncEngine) -> None:
        async with engine.connect() as conn:
            first = (await conn.get_raw_connection()).driver_connection
            await conn.execute(sa.text("SELECT 1"))
        async with engine.connect() as conn:
            second = (await conn.get_raw_connection()).driver_connection
            assert (await conn.execute(sa.text("SELECT 1"))).scalar() == 1
        assert first is second

    @pytest.mark.timeout(60)
    async def test_unresponsive_connection_is_terminated_and_replaced(
        self,
        engine: AsyncEngine,
        relay: _Relay,
    ) -> None:
        async with engine.connect() as conn:
            stale = (await conn.get_raw_connection()).driver_connection
            await conn.execute(sa.text("SELECT 1"))
        assert stale is not None
        stale_connection = stale._connection
        relay.freeze()

        started = time.monotonic()

        async def checkout() -> object:
            async with engine.connect() as conn:
                fresh = (await conn.get_raw_connection()).driver_connection
                assert (await conn.execute(sa.text("SELECT 1"))).scalar() == 1
                return fresh

        fresh = await _bounded(checkout(), "checkout")
        elapsed = time.monotonic() - started

        assert PRE_PING_TIMEOUT <= elapsed < PRE_PING_TIMEOUT + 4
        assert stale_connection.is_closed()
        assert fresh is not stale
