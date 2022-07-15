import asyncio
import uuid
from datetime import datetime

import pytest
import sqlalchemy
from dateutil.tz import tzutc

from ai.backend.manager.api.utils import call_non_bursty, mask_sensitive_keys
from ai.backend.manager.models import (
    domains,
    groups,
    kernels,
    users,
    verify_dotfile_name,
    verify_vfolder_name,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, sql_json_merge


@pytest.mark.asyncio
async def test_call_non_bursty():
    key = 'x'
    execution_count = 0

    async def execute():
        nonlocal execution_count
        await asyncio.sleep(0)
        execution_count += 1

    # ensure reset
    await asyncio.sleep(0.11)

    # check run as coroutine
    execution_count = 0
    with pytest.raises(TypeError):
        await call_non_bursty(key, execute())

    # check run as coroutinefunction
    execution_count = 0
    await call_non_bursty(key, execute)
    assert execution_count == 1
    await asyncio.sleep(0.11)

    # check burstiness control
    execution_count = 0
    for _ in range(129):
        await call_non_bursty(key, execute)
    assert execution_count == 3
    await asyncio.sleep(0.01)
    await call_non_bursty(key, execute)
    assert execution_count == 3
    await asyncio.sleep(0.11)
    await call_non_bursty(key, execute)
    assert execution_count == 4
    for _ in range(64):
        await call_non_bursty(key, execute)
    assert execution_count == 5


def test_vfolder_name_validator():
    assert not verify_vfolder_name('.bashrc')
    assert not verify_vfolder_name('.terminfo')
    assert verify_vfolder_name('bashrc')
    assert verify_vfolder_name('.config')
    assert verify_vfolder_name('bin')
    assert verify_vfolder_name('boot')
    assert verify_vfolder_name('root')
    assert not verify_vfolder_name('/bin')
    assert not verify_vfolder_name('/boot')
    assert not verify_vfolder_name('/root')
    assert verify_vfolder_name('/home/work/bin')
    assert verify_vfolder_name('/home/work/boot')
    assert verify_vfolder_name('/home/work/root')
    assert verify_vfolder_name('home/work')


def test_dotfile_name_validator():
    assert not verify_dotfile_name('.terminfo')
    assert not verify_dotfile_name('.config')
    assert not verify_dotfile_name('.ssh/authorized_keys')
    assert verify_dotfile_name('.bashrc')
    assert verify_dotfile_name('.ssh/id_rsa')


def test_mask_sensitive_keys():
    a = {'a': 123, 'my-Secret': 'hello'}
    b = mask_sensitive_keys(a)
    # original is untouched
    assert a['a'] == 123
    assert a['my-Secret'] == 'hello'
    # cloned has masked fields
    assert b['a'] == 123
    assert b['my-Secret'] == '***'


@pytest.mark.asyncio
async def test_sql_json_merge(database_engine: ExtendedAsyncSAEngine):
    async def create_user_row(
        conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
    ) -> str:
        user_uuid = str(uuid.uuid4()).replace("-", "")
        postfix = str(uuid.uuid4()).split("-")[1]
        query = users.insert().values({
            "uuid": user_uuid,
            "username": f"TestCaseRunner-{postfix}",
            "email": f"tc.runner-{postfix}@lablup.com",
        })
        await conn.execute(query)
        return user_uuid

    async def create_domain_row(
        conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
    ) -> str:
        domain_name = "default"
        query = domains.insert().values({
            "name": domain_name,
            "total_resource_slots": {},
        })
        await conn.execute(query)
        return domain_name

    async def create_group_row(
        conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
        domain_name: str = "default",
    ) -> str:
        group_id = str(uuid.uuid4()).replace("-", "")
        group_name = str(uuid.uuid4()).split("-")[0]
        query = groups.insert().values({
            "id": group_id,
            "name": group_name,
            "domain_name": domain_name,
            "total_resource_slots": {},
        })
        await conn.execute(query)
        return group_id

    async with database_engine.begin() as conn:
        user_uuid = await create_user_row(conn)
        domain_name = await create_domain_row(conn)
        group_id = await create_group_row(conn, domain_name=domain_name)

    async def create_kernel_row(
        conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> str:
        session_id = str(uuid.uuid4()).replace('-', '')
        query = kernels.insert().values({
            "session_id": session_id,
            "domain_name": "default",
            "group_id": group_id,
            "user_uuid": user_uuid,
            "occupied_slots": {},
            "repl_in_port": 0,
            "repl_out_port": 0,
            "stdin_port": 0,
            "stdout_port": 0,
        })
        await conn.execute(query)
        return session_id

    async def select_kernel_row(
        conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
        session_id: uuid.UUID,
    ):
        query = kernels.select().select_from(kernels).where(kernels.c.session_id == session_id)
        return await conn.execute(query)

    async def delete_rows(
        conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
    ):
        await conn.execute(kernels.delete())
        await conn.execute(groups.delete())
        await conn.execute(domains.delete())
        await conn.execute(users.delete())

    timestamp = datetime.now(tzutc()).isoformat()

    # TEST 00
    expected = None
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 01
    expected = {
        "kernel": {
            "PENDING": timestamp,
            "PREPARING": timestamp,
        },
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel",),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 02
    expected = {
        "kernel": {
            "session": {
                "PENDING": timestamp,
                "PREPARING": timestamp,
            },
        },
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 03
    expected = {
        "PENDING": [
            {},
            timestamp,
        ],
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("PENDING",),
                timestamp,
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 04
    expected = {
        "kernel": {
            "session": {
                "more": {
                    "details": {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
                },
            },
        },
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session", "more", "details"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 05
    expected = {
        "more": {
            "details": {
                "PENDING": timestamp,
                "PREPARING": timestamp,
            },
        },
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session", "more", "details"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
                _depth=2,
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 06
    expected = {
        "details": {
            "PENDING": timestamp,
            "PREPARING": timestamp,
        },
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session", "more", "details"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
                _depth=3,
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 07 (Append)
    expected = {
        "kernel": {
            "session": {
                "PENDING": timestamp,
                "PREPARING": timestamp,
                "TERMINATED": timestamp,
                "TERMINATING": timestamp,
            },
        },
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session"),
                {
                    "TERMINATING": timestamp,
                    "TERMINATED": timestamp,
                },
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    # TEST 08
    expected = {
        "details": {
            "PENDING": timestamp,
            "PREPARING": timestamp,
            "TERMINATING": timestamp,
            "TERMINATED": timestamp,
        },
    }
    async with database_engine.begin() as conn:
        session_id = await create_kernel_row(conn, group_id, user_uuid)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session", "details"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        query = kernels.update().values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session", "details"),
                {
                    "TERMINATING": timestamp,
                    "TERMINATED": timestamp,
                },
                _depth=2,
            ),
        }).where(kernels.c.session_id == session_id)
        await conn.execute(query)
        kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected

    """
    # TEST 04
    expected = {
        "PENDING": timestamp,
        "PREPARING": timestamp,
    }
    async with connect_database(config) as db:
        async with database_engine.begin() as conn:
            session_id = await create_kernel_row(conn, group_id, user_uuid)
            query = kernels.update().values({
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    (),
                    {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
                ),
            }).where(kernels.c.session_id == session_id)
            await conn.execute(query)
            kernel, *_ = await select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected
    """

    # CLEAN UP
    async with database_engine.begin() as conn:
        await delete_rows(conn)
