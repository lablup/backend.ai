"""Verifies the `kernel_usage_records` copy that adds `resource_group_id` against a real database.

The two tables it reads are created in a separate schema in their 26.4 shape, which the
copy reaches through `search_path`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Final

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Connection

from ai.backend.manager.models.alembic.kernel_usage_record_rebuild import (
    KernelUsageRecordRebuild,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

_SCHEMA: Final[str] = "kernel_usage_record_probe"

_TABLES: Final[tuple[str, ...]] = (
    """CREATE TABLE scaling_groups (
        name VARCHAR(64) NOT NULL,
        id UUID NOT NULL,
        CONSTRAINT pk_scaling_groups PRIMARY KEY (name),
        CONSTRAINT uq_scaling_groups_id UNIQUE (id)
    )""",
    """CREATE TABLE kernel_usage_records (
        id UUID NOT NULL,
        kernel_id UUID NOT NULL,
        user_uuid UUID NOT NULL,
        resource_group VARCHAR(64) NOT NULL,
        period_start TIMESTAMP WITH TIME ZONE NOT NULL,
        resource_usage JSONB NOT NULL,
        CONSTRAINT pk_kernel_usage_records PRIMARY KEY (id)
    )""",
    "CREATE INDEX ix_kernel_usage_records_kernel_id ON kernel_usage_records (kernel_id)",
    "CREATE INDEX ix_kernel_usage_records_resource_group ON kernel_usage_records (resource_group)",
    "CREATE INDEX ix_kernel_usage_rg_period ON kernel_usage_records (resource_group, period_start)",
    "CREATE INDEX ix_kernel_usage_user_period ON kernel_usage_records (user_uuid, period_start)",
)

_DEFAULT_GROUP_ID: Final[uuid.UUID] = uuid.uuid4()
_GPU_GROUP_ID: Final[uuid.UUID] = uuid.uuid4()
_GROUPS: Final[dict[str, uuid.UUID]] = {"default": _DEFAULT_GROUP_ID, "gpu": _GPU_GROUP_ID}

_IN_DEFAULT: Final[uuid.UUID] = uuid.uuid4()
_IN_GPU: Final[uuid.UUID] = uuid.uuid4()
_IN_REMOVED_GROUP: Final[uuid.UUID] = uuid.uuid4()
_RECORDS: Final[dict[uuid.UUID, str]] = {
    _IN_DEFAULT: "default",
    _IN_GPU: "gpu",
    _IN_REMOVED_GROUP: "removed",
}
_EXPECTED: Final[dict[uuid.UUID, uuid.UUID]] = {
    _IN_DEFAULT: _DEFAULT_GROUP_ID,
    _IN_GPU: _GPU_GROUP_ID,
}

_INDEXES: Final[dict[str, str]] = {
    "pk_kernel_usage_records": "(id)",
    "ix_kernel_usage_records_kernel_id": "(kernel_id)",
    "ix_kernel_usage_records_resource_group": "(resource_group)",
    "ix_kernel_usage_rg_period": "(resource_group, period_start)",
    "ix_kernel_usage_user_period": "(user_uuid, period_start)",
}


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with database_connection.begin() as conn:
        await conn.execute(sa.text(f"CREATE SCHEMA {_SCHEMA}"))
        await conn.execute(sa.text(f"SET LOCAL search_path TO {_SCHEMA}"))
        for statement in _TABLES:
            await conn.execute(sa.text(statement))
        for name, group_id in _GROUPS.items():
            await conn.execute(
                sa.text("INSERT INTO scaling_groups (name, id) VALUES (:name, :id)").bindparams(
                    name=name, id=group_id
                )
            )
        for record_id, group in _RECORDS.items():
            await conn.execute(
                sa.text(
                    "INSERT INTO kernel_usage_records"
                    " (id, kernel_id, user_uuid, resource_group, period_start, resource_usage)"
                    " VALUES (:id, :kernel_id, :user_uuid, :group, now(), '{}'::jsonb)"
                ).bindparams(
                    id=record_id, kernel_id=uuid.uuid4(), user_uuid=uuid.uuid4(), group=group
                )
            )
    try:
        yield database_connection
    finally:
        async with database_connection.begin() as conn:
            await conn.execute(sa.text(f"DROP SCHEMA {_SCHEMA} CASCADE"))


def _copy(conn: Connection) -> None:
    rebuild = KernelUsageRecordRebuild(conn)
    if "resource_group_id" not in rebuild.columns():
        rebuild.run()


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.execute(sa.text(f"SET LOCAL search_path TO {_SCHEMA}"))
        await conn.run_sync(_copy)


async def _resource_group_ids(db: ExtendedAsyncSAEngine) -> dict[uuid.UUID, uuid.UUID]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.text(f"SELECT id, resource_group_id FROM {_SCHEMA}.kernel_usage_records")
        )
        return {row.id: row.resource_group_id for row in rows}


async def _indexes(db: ExtendedAsyncSAEngine) -> dict[str, str]:
    """Maps each index to its column list."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.text(
                "SELECT indexname, indexdef FROM pg_indexes"
                " WHERE schemaname = :schema AND tablename = 'kernel_usage_records'"
            ).bindparams(schema=_SCHEMA)
        )
        return {row.indexname: row.indexdef[row.indexdef.index("(") :] for row in rows}


class TestKernelUsageRecordRebuild:
    async def test_resolved_rows_carry_the_group_id_and_the_rest_are_dropped(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _run(db)

        assert await _resource_group_ids(db) == _EXPECTED

    async def test_column_is_not_null(self, db: ExtendedAsyncSAEngine) -> None:
        await _run(db)

        async with db.begin_readonly() as conn:
            nullable = await conn.scalar(
                sa.text(
                    "SELECT NOT attnotnull FROM pg_attribute"
                    f" WHERE attrelid = '{_SCHEMA}.kernel_usage_records'::regclass"
                    " AND attname = 'resource_group_id'"
                )
            )
        assert nullable is False

    async def test_keys_and_indexes_keep_their_names(self, db: ExtendedAsyncSAEngine) -> None:
        await _run(db)

        assert await _indexes(db) == _INDEXES

    async def test_running_it_again_changes_nothing(self, db: ExtendedAsyncSAEngine) -> None:
        await _run(db)
        await _run(db)

        assert await _resource_group_ids(db) == _EXPECTED
