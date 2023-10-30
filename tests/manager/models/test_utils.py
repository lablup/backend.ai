import uuid
from datetime import datetime
from typing import Union

import pytest
import sqlalchemy
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.manager.models import KernelRow, SessionRow, kernels
from ai.backend.manager.models.utils import (
    agg_to_array,
    agg_to_str,
    sql_append_lists_to_list,
)


async def _select_kernel_row(
    conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
    session_id: Union[str, uuid.UUID],
):
    query = kernels.select().select_from(kernels).where(kernels.c.session_id == session_id)
    kernel, *_ = await conn.execute(query)
    return kernel


@pytest.mark.asyncio
async def test_sql_json_merge__default(session_info):
    session_id, conn = session_info
    expected: list[list[str, str]] = []
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_sql_append_lists_to_list(session_info):
    session_id, conn = session_info
    timestamp = datetime.now(tzutc()).isoformat()
    expected = [
        ["PENDING", timestamp],
        ["PREPARING", timestamp],
        ["TERMINATING", timestamp],
        ["TERMINATED", timestamp],
    ]

    query = (
        kernels.update()
        .values(
            {
                "status_history": sql_append_lists_to_list(
                    kernels.c.status_history,
                    ["PENDING", timestamp],
                    ["PREPARING", timestamp],
                ),
            }
        )
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    query = (
        kernels.update()
        .values(
            {
                "status_history": sql_append_lists_to_list(
                    kernels.c.status_history,
                    ["TERMINATING", timestamp],
                    ["TERMINATED", timestamp],
                ),
            }
        )
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


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
