from __future__ import annotations

from collections.abc import AsyncIterator

import asyncpg
import pytest
import sqlalchemy as sa
from asyncpg.transaction import Transaction
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ai.backend.common.db.invalidator import FailedBeginInvalidator
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.testutils.bootstrap import POSTGRES_MAINTENANCE_DB, POSTGRES_PASSWORD, POSTGRES_USER


@pytest.fixture
async def engine(postgres_container: tuple[str, HostPortPair]) -> AsyncIterator[AsyncEngine]:
    _, addr = postgres_container
    url = sa.engine.URL.create(
        "postgresql+asyncpg",
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=addr.host,
        port=addr.port,
        database=POSTGRES_MAINTENANCE_DB,
    )
    engine = create_async_engine(url, pool_size=1, max_overflow=0, isolation_level="SERIALIZABLE")
    FailedBeginInvalidator().listen(engine.sync_engine)
    yield engine
    await engine.dispose()


async def _select_one(engine: AsyncEngine) -> int | None:
    async with engine.begin() as conn:
        return (await conn.execute(sa.text("SELECT 1"))).scalar()


class TestFailedBeginInvalidator:
    async def test_connection_with_failed_begin_is_replaced(
        self,
        engine: AsyncEngine,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        original_start = Transaction.start
        failures = [
            asyncpg.exceptions.FeatureNotSupportedError(
                "cannot use serializable mode in a hot standby"
            )
        ]

        async def _start(self: Transaction) -> None:
            if failures:
                # asyncpg keeps the transaction as the connection's top one when BEGIN fails.
                self._connection._top_xact = self
                raise failures.pop()
            await original_start(self)

        monkeypatch.setattr(Transaction, "start", _start)

        with pytest.raises(DBAPIError):
            await _select_one(engine)

        assert await _select_one(engine) == 1

    async def test_connection_left_in_savepoint_mode_is_replaced(
        self,
        engine: AsyncEngine,
    ) -> None:
        async with engine.connect() as conn:
            raw = await conn.get_raw_connection()
            driver_conn = raw.driver_connection
            assert driver_conn is not None
            driver_conn._top_xact = driver_conn.transaction(isolation="serializable")

        with pytest.raises(DBAPIError) as exc_info:
            await _select_one(engine)
        assert exc_info.value.orig is not None
        assert isinstance(exc_info.value.orig.__cause__, asyncpg.NoActiveSQLTransactionError)

        assert await _select_one(engine) == 1
