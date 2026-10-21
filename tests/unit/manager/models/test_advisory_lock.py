import asyncio
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa

from ai.backend.manager.defs import LockID
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.db.engine import create_async_engine


async def test_lock(database_connection: ExtendedAsyncSAEngine) -> None:
    enter_count = 0
    done_count = 0

    async def critical_section(db: ExtendedAsyncSAEngine) -> None:
        nonlocal enter_count
        async with db.advisory_lock(LockID.LOCKID_TEST):
            enter_count += 1
            await asyncio.sleep(1.0)

    tasks = []
    for idx in range(5):
        tasks.append(
            asyncio.create_task(
                critical_section(database_connection),
                name=f"critical-section-{idx}",
            ),
        )
    await asyncio.sleep(0.5)

    async with database_connection.connect() as conn:
        result = await conn.exec_driver_sql(
            "SELECT objid, granted, pid FROM pg_locks WHERE locktype = 'advisory' AND objid = 42;",
        )
        rows = result.fetchall()
        print(rows)
        result = await conn.exec_driver_sql(
            "SELECT objid, granted FROM pg_locks "
            "WHERE locktype = 'advisory' AND objid = 42 AND granted = 't';",
        )
        rows = result.fetchall()
        assert len(rows) == 1

    await asyncio.sleep(2.5)
    for t in tasks:
        if t.done():
            done_count += 1
        else:
            try:
                t.cancel()
                await t
            except asyncio.CancelledError:
                pass
    await asyncio.sleep(0.1)

    assert 2 <= done_count <= 3
    assert enter_count >= done_count

    # Check all tasks have unlocked.
    async with database_connection.connect() as conn:
        result = await conn.exec_driver_sql(
            "SELECT objid, granted, pid FROM pg_locks "
            "WHERE locktype = 'advisory' AND objid = 42 AND granted = 't';",
        )
        rows = result.fetchall()
        print(rows)
        assert len(rows) == 0


async def test_lock_timeout(database_connection: ExtendedAsyncSAEngine) -> None:
    lock_connection_timeout = 0.5
    sleep = 1

    with pytest.raises(asyncio.TimeoutError):
        database_connection.lock_conn_timeout = lock_connection_timeout
        async with database_connection.advisory_lock(LockID.LOCKID_TEST):
            await asyncio.sleep(sleep)


@pytest.fixture
async def short_idle_engine(test_database_url: str) -> AsyncIterator[ExtendedAsyncSAEngine]:
    engine = create_async_engine(
        test_database_url,
        connect_args={"server_settings": {"idle_in_transaction_session_timeout": "1000"}},
        isolation_level="SERIALIZABLE",
    )
    yield engine
    await engine.dispose()


async def test_lock_survives_idle_in_transaction_timeout(
    short_idle_engine: ExtendedAsyncSAEngine,
) -> None:
    async with short_idle_engine.advisory_lock(LockID.LOCKID_TEST):
        await asyncio.sleep(2.0)
        async with short_idle_engine.connect() as other:
            # The xact variant leaves no lock behind on the pooled probe connection.
            acquired = await other.scalar(
                sa.text(f"SELECT pg_try_advisory_xact_lock({LockID.LOCKID_TEST:d})")
            )
        assert acquired is False


async def test_lock_connection_isolation_level_is_restored(
    short_idle_engine: ExtendedAsyncSAEngine,
) -> None:
    async with short_idle_engine.advisory_lock(LockID.LOCKID_TEST):
        pass
    async with short_idle_engine.connect() as conn:
        assert await conn.get_isolation_level() == "SERIALIZABLE"
