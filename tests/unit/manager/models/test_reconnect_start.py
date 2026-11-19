from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable

import asyncpg
import pytest
import sqlalchemy as sa
from sqlalchemy.pool import QueuePool

from ai.backend.common.db.connector import PrimaryMemberConnector
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.unified import DatabaseConfig
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.db.engine import create_async_engine
from ai.backend.testutils.bootstrap import POSTGRES_MAINTENANCE_DB, POSTGRES_PASSWORD, POSTGRES_USER

RECONNECT_TIMEOUT = 10.0
SHORT_TIMEOUT = 0.5


class _FlakyCreator:
    """Raises `errors` one per call and then connects to the real database."""

    _errors: list[BaseException]
    _connector: PrimaryMemberConnector
    calls: int

    def __init__(self, errors: list[BaseException], connector: PrimaryMemberConnector) -> None:
        self._errors = list(errors)
        self._connector = connector
        self.calls = 0

    async def __call__(self) -> asyncpg.Connection:
        self.calls += 1
        if self._errors:
            raise self._errors.pop(0)
        return await self._connector.connect()


class _AlwaysFailingCreator:
    calls: int

    def __init__(self, error: Callable[[], BaseException]) -> None:
        self._error = error
        self.calls = 0

    async def __call__(self) -> asyncpg.Connection:
        self.calls += 1
        raise self._error()


class _Relay:
    """A TCP relay that can be closed and opened again on the same port."""

    _target: HostPortPair
    _server: asyncio.Server | None
    _writers: list[asyncio.StreamWriter]
    _tasks: list[asyncio.Task[None]]
    port: int

    def __init__(self, target: HostPortPair) -> None:
        self._target = target
        self._server = None
        self._writers = []
        self._tasks = []
        self.port = 0

    async def open(self) -> None:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", self.port)
        self.port = self._server.sockets[0].getsockname()[1]

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        for writer in self._writers:
            writer.close()
        self._tasks.clear()
        self._writers.clear()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        up_reader, up_writer = await asyncio.open_connection(self._target.host, self._target.port)
        self._writers += [writer, up_writer]
        for src, dst in ((reader, up_writer), (up_reader, writer)):
            self._tasks.append(asyncio.create_task(self._pipe(src, dst)))

    async def _pipe(self, src: asyncio.StreamReader, dst: asyncio.StreamWriter) -> None:
        while data := await src.read(65536):
            dst.write(data)
            await dst.drain()
        dst.close()


@pytest.fixture
def connector(postgres_container: tuple[str, HostPortPair]) -> PrimaryMemberConnector:
    _, addr = postgres_container
    return PrimaryMemberConnector(
        [(addr.host, addr.port)],
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_MAINTENANCE_DB,
        connect_timeout=2,
        connect_kwargs={},
    )


def _engine(
    creator: Callable[[], Awaitable[asyncpg.Connection]],
    reconnect_timeout: float | None,
) -> ExtendedAsyncSAEngine:
    return create_async_engine(
        "postgresql+asyncpg://",
        async_creator=creator,
        pool_size=1,
        max_overflow=0,
        _reconnect_timeout=reconnect_timeout,
    )


class TestReconnectOnStart:
    @pytest.mark.parametrize("method", ["begin", "connect"])
    async def test_start_retries_reconnect_errors_and_succeeds(
        self,
        connector: PrimaryMemberConnector,
        method: str,
    ) -> None:
        creator = _FlakyCreator(
            [ConnectionRefusedError("refused"), OSError("unreachable")], connector
        )
        engine = _engine(creator, RECONNECT_TIMEOUT)
        try:
            async with getattr(engine, method)() as conn:
                assert (await conn.execute(sa.text("SELECT 1"))).scalar() == 1
        finally:
            await engine.dispose()
        assert creator.calls == 3

    async def test_raises_last_error_after_the_time_limit(self) -> None:
        creator = _AlwaysFailingCreator(lambda: ConnectionRefusedError("refused"))
        engine = _engine(creator, SHORT_TIMEOUT)
        started = time.monotonic()
        try:
            with pytest.raises(ConnectionRefusedError):
                async with engine.begin():
                    pytest.fail("the body must not run")
        finally:
            await engine.dispose()
        assert time.monotonic() - started >= SHORT_TIMEOUT
        assert creator.calls > 1

    async def test_error_that_is_not_a_reconnect_error_is_raised_at_once(self) -> None:
        creator = _AlwaysFailingCreator(lambda: asyncpg.InvalidPasswordError("bad password"))
        engine = _engine(creator, RECONNECT_TIMEOUT)
        try:
            with pytest.raises(Exception, match="bad password"):
                async with engine.begin():
                    pytest.fail("the body must not run")
        finally:
            await engine.dispose()
        assert creator.calls == 1

    async def test_error_raised_in_the_body_is_not_retried(
        self,
        connector: PrimaryMemberConnector,
    ) -> None:
        creator = _FlakyCreator([], connector)
        engine = _engine(creator, RECONNECT_TIMEOUT)
        runs = 0
        try:
            with pytest.raises(ConnectionRefusedError):
                async with engine.begin():
                    runs += 1
                    raise ConnectionRefusedError("lost in the body")
        finally:
            await engine.dispose()
        assert runs == 1

    async def test_failed_start_leaves_no_checked_out_connection(self) -> None:
        creator = _AlwaysFailingCreator(lambda: ConnectionRefusedError("refused"))
        engine = _engine(creator, SHORT_TIMEOUT)
        try:
            with pytest.raises(ConnectionRefusedError):
                async with engine.connect():
                    pytest.fail("the body must not run")
            assert isinstance(engine.pool, QueuePool)
            assert engine.pool.checkedout() == 0
        finally:
            await engine.dispose()


@pytest.fixture
async def relay(postgres_container: tuple[str, HostPortPair]) -> AsyncIterator[_Relay]:
    _, addr = postgres_container
    relay = _Relay(addr)
    await relay.open()
    yield relay
    await relay.close()


class TestReconnectWhileDatabaseIsUnreachable:
    @pytest.mark.timeout(60)
    async def test_begin_waits_for_the_database_to_come_back(self, relay: _Relay) -> None:
        connector = PrimaryMemberConnector(
            [("127.0.0.1", relay.port)],
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_MAINTENANCE_DB,
            connect_timeout=2,
            connect_kwargs={},
        )
        await relay.close()
        engine = _engine(connector.connect, RECONNECT_TIMEOUT)

        async def reopen() -> None:
            await asyncio.sleep(1.5)
            await relay.open()

        reopening = asyncio.create_task(reopen())
        try:
            async with engine.begin() as conn:
                assert (await conn.execute(sa.text("SELECT 1"))).scalar() == 1
            await reopening
        finally:
            reopening.cancel()
            await engine.dispose()


class TestReconnectConfigDefaults:
    _base: dict[str, str] = {"name": "testdb", "user": "testuser", "password": "testpass"}

    def test_reconnect_timeout_and_pool_pre_ping_defaults(self) -> None:
        config = DatabaseConfig.model_validate(self._base)
        assert config.reconnect_timeout == 60.0
        assert config.pool_pre_ping is True

    def test_reconnect_timeout_must_be_positive(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            DatabaseConfig.model_validate({**self._base, "reconnect-timeout": 0})
