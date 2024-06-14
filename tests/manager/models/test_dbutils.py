import asyncio

import aiotools
import pytest
import sqlalchemy as sa

from ai.backend.manager.models.utils import execute_with_retry, execute_with_txn_retry


@pytest.mark.asyncio
async def test_execute_with_retry():
    class DummyDBError(Exception):
        def __init__(self, pgcode):
            self.pgcode = pgcode

    async def txn_func_generic_failure():
        raise sa.exc.IntegrityError("DUMMY_SQL", params=None, orig=DummyDBError("999"))

    async def txn_func_generic_failure_2():
        raise ZeroDivisionError("oops")

    async def txn_func_permanent_serialization_failure():
        raise sa.exc.DBAPIError("DUMMY_SQL", params=None, orig=DummyDBError("40001"))

    _fail_count = 0

    async def txn_func_temporary_serialization_failure():
        nonlocal _fail_count
        _fail_count += 1
        if _fail_count == 10:
            return 1234
        raise sa.exc.DBAPIError("DUMMY_SQL", params=None, orig=DummyDBError("40001"))

    vclock = aiotools.VirtualClock()
    with vclock.patch_loop():
        with pytest.raises(sa.exc.IntegrityError):
            await execute_with_retry(txn_func_generic_failure)

        with pytest.raises(ZeroDivisionError):
            await execute_with_retry(txn_func_generic_failure_2)

        with pytest.raises(RuntimeError) as e:
            await execute_with_retry(txn_func_permanent_serialization_failure)
        assert "serialization failed" in e.value.args[0].lower()

        ret = await execute_with_retry(txn_func_temporary_serialization_failure)
        assert ret == 1234


@pytest.mark.asyncio
async def test_execute_with_trx_retry(database_engine):
    class DummyDBError(Exception):
        def __init__(self, pgcode):
            self.pgcode = pgcode

    async def txn_func_generic_failure(db_session):
        raise sa.exc.IntegrityError("DUMMY_SQL", params=None, orig=DummyDBError("999"))

    async def txn_func_generic_failure_2(db_session):
        raise ZeroDivisionError("oops")

    async def txn_func_permanent_serialization_failure(db_session):
        raise sa.exc.DBAPIError("DUMMY_SQL", params=None, orig=DummyDBError("40001"))

    _fail_count = 0

    async def txn_func_temporary_serialization_failure(db_session):
        nonlocal _fail_count
        _fail_count += 1
        if _fail_count == 5:
            return 1234
        raise sa.exc.DBAPIError("DUMMY_SQL", params=None, orig=DummyDBError("40001"))

    with pytest.raises(sa.exc.IntegrityError):
        async with database_engine.connect() as conn:
            await execute_with_txn_retry(
                txn_func_generic_failure, database_engine.begin_session, conn
            )

    with pytest.raises(ZeroDivisionError):
        async with database_engine.connect() as conn:
            await execute_with_txn_retry(
                txn_func_generic_failure_2, database_engine.begin_session, conn
            )

    with pytest.raises(asyncio.TimeoutError) as e:
        async with database_engine.connect() as conn:
            await execute_with_txn_retry(
                txn_func_permanent_serialization_failure, database_engine.begin_session, conn
            )
    assert "serialization failed" in e.value.args[0].lower()

    async with database_engine.connect() as conn:
        ret = await execute_with_txn_retry(
            txn_func_temporary_serialization_failure, database_engine.begin_session, conn
        )
    assert ret == 1234
