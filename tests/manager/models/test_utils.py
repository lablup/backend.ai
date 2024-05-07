from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models import KernelRow, SessionRow, kernels, metadata
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    agg_to_array,
    agg_to_str,
    sql_json_merge,
)


@pytest.fixture
async def dummy_kernels(database_engine: ExtendedAsyncSAEngine):
    # dummy_kernels, designed solely for testing sql_json_merge, only includes the status_history column, unlike legacy kernels table.
    dummy_kernels = sa.Table(
        "dummy_kernels",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True, default=1),
        sa.Column(
            "status_history", pgsql.JSONB(), nullable=True, default=sa.null()
        ),  # JSONB column for testing
        extend_existing=True,
    )

    async with database_engine.begin() as db_sess:
        await db_sess.run_sync(metadata.create_all)
        await db_sess.execute(dummy_kernels.insert())  # insert fixture data for testing
        await db_sess.commit()

        yield dummy_kernels

    async with database_engine.begin() as db_sess:
        await db_sess.run_sync(dummy_kernels.drop)
        await db_sess.commit()


@pytest.mark.asyncio
async def test_sql_json_merge__deeper_object(
    dummy_kernels: sa.Table, database_engine: ExtendedAsyncSAEngine
):
    async with database_engine.begin() as db_sess:
        timestamp = datetime.now(tzutc()).isoformat()
        expected = {
            "kernel": {
                "session": {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            },
        }
        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    ("kernel", "session"),
                    {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)
        result = (await db_sess.execute(sa.select(dummy_kernels.c.status_history))).scalar()
        assert result == expected


@pytest.mark.asyncio
async def test_sql_json_merge__append_values(
    dummy_kernels: sa.Table, database_engine: ExtendedAsyncSAEngine
):
    async with database_engine.begin() as db_sess:
        timestamp = datetime.now(tzutc()).isoformat()
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
        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    ("kernel", "session"),
                    {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)
        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    ("kernel", "session"),
                    {
                        "TERMINATING": timestamp,
                        "TERMINATED": timestamp,
                    },
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)

        result = (await db_sess.execute(sa.select(dummy_kernels.c.status_history))).scalar()
        assert result == expected


@pytest.mark.asyncio
async def test_sql_json_merge__kernel_status_history(
    dummy_kernels: sa.Table, database_engine: ExtendedAsyncSAEngine
):
    async with database_engine.begin() as db_sess:
        timestamp = datetime.now(tzutc()).isoformat()
        expected = {
            "PENDING": timestamp,
            "PREPARING": timestamp,
            "TERMINATING": timestamp,
            "TERMINATED": timestamp,
        }
        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    (),
                    {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)
        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    (),
                    {
                        "TERMINATING": timestamp,
                        "TERMINATED": timestamp,
                    },
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)

        result = (await db_sess.execute(sa.select(dummy_kernels.c.status_history))).scalar()
        assert result == expected


@pytest.mark.asyncio
async def test_sql_json_merge__mixed_formats(
    dummy_kernels: sa.Table, database_engine: ExtendedAsyncSAEngine
):
    async with database_engine.begin() as db_sess:
        timestamp = datetime.now(tzutc()).isoformat()
        expected = {
            "PENDING": timestamp,
            "kernel": {
                "PREPARING": timestamp,
            },
        }
        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    (),
                    {
                        "PENDING": timestamp,
                    },
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)

        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    ("kernel",),
                    {
                        "PREPARING": timestamp,
                    },
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)

        result = (await db_sess.execute(sa.select(dummy_kernels.c.status_history))).scalar()
        assert result == expected


@pytest.mark.asyncio
async def test_sql_json_merge__json_serializable_types(
    dummy_kernels: sa.Table, database_engine: ExtendedAsyncSAEngine
):
    async with database_engine.begin() as db_sess:
        expected = {
            "boolean": True,
            "integer": 10101010,
            "float": 1010.1010,
            "string": "10101010",
            # "bytes": b"10101010",
            "list": [
                10101010,
                "10101010",
            ],
            "dict": {
                "10101010": 10101010,
            },
        }
        query = (
            dummy_kernels.update()
            .values({
                "status_history": sql_json_merge(
                    dummy_kernels.c.status_history,
                    (),
                    expected,
                ),
            })
            .where(dummy_kernels.c.id == 1)
        )
        await db_sess.execute(query)
        result = (await db_sess.execute(sa.select(dummy_kernels.c.status_history))).scalar()
        assert result == expected


@pytest.mark.asyncio
async def test_agg_to_str(session_info):
    session_id, conn = session_info
    test_data1, test_data2 = "hello", "world"
    expected = "hello,world"

    # Insert more kernel data
    result = await conn.execute(sa.select(kernels).where(kernels.c.session_id == session_id))
    orig_kernel = result.first()
    kernel_data = {
        "session_id": session_id,
        "domain_name": orig_kernel["domain_name"],
        "group_id": orig_kernel["group_id"],
        "user_uuid": orig_kernel["user_uuid"],
        "cluster_role": "sub",
        "occupied_slots": {},
        "repl_in_port": 0,
        "repl_out_port": 0,
        "stdin_port": 0,
        "stdout_port": 0,
        "vfolder_mounts": {},
    }
    await conn.execute(
        sa.insert(
            kernels,
            {
                "tag": test_data1,
                **kernel_data,
            },
        )
    )
    await conn.execute(
        sa.insert(
            kernels,
            {
                "tag": test_data2,
                **kernel_data,
            },
        )
    )

    # Fetch Session's kernel and check `kernels_tag` field
    query = (
        sa.select(SessionRow, agg_to_str(KernelRow.tag).label("kernels_tag"))
        .select_from(sa.join(SessionRow, KernelRow))
        .where(SessionRow.id == session_id)
        .group_by(SessionRow)
    )
    result = await conn.execute(query)
    session = result.first()
    assert session["kernels_tag"] == expected

    # Delete test kernel data explicitly
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data1) & (kernels.c.session_id == session_id)
        )
    )
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data2) & (kernels.c.session_id == session_id)
        )
    )


@pytest.mark.asyncio
async def test_agg_to_array(session_info):
    session_id, conn = session_info
    test_data1, test_data2 = "a", "b"
    expected = ["a", "b", None]

    # Insert more kernel data
    result = await conn.execute(sa.select(kernels).where(kernels.c.session_id == session_id))
    orig_kernel = result.first()
    kernel_data = {
        "session_id": session_id,
        "domain_name": orig_kernel["domain_name"],
        "group_id": orig_kernel["group_id"],
        "user_uuid": orig_kernel["user_uuid"],
        "cluster_role": "sub",
        "occupied_slots": {},
        "repl_in_port": 0,
        "repl_out_port": 0,
        "stdin_port": 0,
        "stdout_port": 0,
        "vfolder_mounts": {},
    }
    await conn.execute(
        sa.insert(
            kernels,
            {
                "tag": test_data1,
                **kernel_data,
            },
        )
    )
    await conn.execute(
        sa.insert(
            kernels,
            {
                "tag": test_data2,
                **kernel_data,
            },
        )
    )

    # Fetch Session's kernel and check `kernels_tag` field
    query = (
        sa.select(SessionRow, agg_to_array(KernelRow.tag).label("kernels_tag"))
        .select_from(sa.join(SessionRow, KernelRow))
        .where(SessionRow.id == session_id)
        .group_by(SessionRow)
    )
    result = await conn.execute(query)
    session = result.first()
    assert session["kernels_tag"] == expected

    # Delete test kernel data explicitly
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data1) & (kernels.c.session_id == session_id)
        )
    )
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data2) & (kernels.c.session_id == session_id)
        )
    )
