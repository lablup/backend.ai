import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

import pytest
import sqlalchemy
from dateutil.tz import tzutc

from ai.backend.manager.models import kernels
from ai.backend.manager.models.utils import sql_json_merge


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
    expected: Optional[Dict[str, Any]] = None
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_sql_json_merge__deeper_object(session_info):
    session_id, conn = session_info
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
        kernels.update()
        .values(
            {
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    ("kernel", "session"),
                    {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
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
async def test_sql_json_merge__append_values(session_info):
    session_id, conn = session_info
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
        kernels.update()
        .values(
            {
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    ("kernel", "session"),
                    {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
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
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    ("kernel", "session"),
                    {
                        "TERMINATING": timestamp,
                        "TERMINATED": timestamp,
                    },
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
async def test_sql_json_merge__kernel_status_history(session_info):
    session_id, conn = session_info
    timestamp = datetime.now(tzutc()).isoformat()
    expected = {
        "PENDING": timestamp,
        "PREPARING": timestamp,
        "TERMINATING": timestamp,
        "TERMINATED": timestamp,
    }
    query = (
        kernels.update()
        .values(
            {
                # "status_history": sqlalchemy.func.coalesce(sqlalchemy.text("'{}'::jsonb")).concat(
                #     sqlalchemy.func.cast(
                #         {"PENDING": timestamp, "PREPARING": timestamp},
                #         sqlalchemy.dialects.postgresql.JSONB,
                #     ),
                # ),
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    (),
                    {
                        "PENDING": timestamp,
                        "PREPARING": timestamp,
                    },
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
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    (),
                    {
                        "TERMINATING": timestamp,
                        "TERMINATED": timestamp,
                    },
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
async def test_sql_json_merge__mixed_formats(session_info):
    session_id, conn = session_info
    timestamp = datetime.now(tzutc()).isoformat()
    expected = {
        "PENDING": timestamp,
        "kernel": {
            "PREPARING": timestamp,
        },
    }
    query = (
        kernels.update()
        .values(
            {
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    (),
                    {
                        "PENDING": timestamp,
                    },
                ),
            }
        )
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    query = (
        kernels.update()
        .values(
            {
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    ("kernel",),
                    {
                        "PREPARING": timestamp,
                    },
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
async def test_sql_json_merge__json_serializable_types(session_info):
    session_id, conn = session_info
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
        kernels.update()
        .values(
            {
                "status_history": sql_json_merge(
                    kernels.c.status_history,
                    (),
                    expected,
                ),
            }
        )
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected
