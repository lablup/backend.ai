import asyncio

import pytest

from ai.backend.manager.defs import LockID
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@pytest.mark.asyncio
async def test_lock(database_engine: ExtendedAsyncSAEngine) -> None:
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
                critical_section(database_engine),
                name=f"critical-section-{idx}",
            ),
        )
    await asyncio.sleep(0.5)

    async with database_engine.connect() as conn:
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
    async with database_engine.connect() as conn:
        result = await conn.exec_driver_sql(
            "SELECT objid, granted, pid FROM pg_locks "
            "WHERE locktype = 'advisory' AND objid = 42 AND granted = 't';",
        )
        rows = result.fetchall()
        print(rows)
        assert len(rows) == 0


@pytest.mark.asyncio
async def test_lock_timeout(database_engine: ExtendedAsyncSAEngine) -> None:
    lock_connection_timeout = 0.5
    sleep = 1

    with pytest.raises(asyncio.TimeoutError):
        database_engine.lock_conn_timeout = lock_connection_timeout
        async with database_engine.advisory_lock(LockID.LOCKID_TEST):
            await asyncio.sleep(sleep)
