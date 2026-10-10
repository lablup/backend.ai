"""Verifies the `audit_logs` rebuild against a real database.

`audit_logs` is created in a separate schema in the shape each starting release leaves it,
and the rebuild reaches it through `search_path`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Final

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.alembic.audit_log_rebuild import AuditLogRebuild
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

_SCHEMA: Final[str] = "audit_log_rebuild_probe"

# audit_logs as 26.4 leaves it.
_TABLE_26_4: Final[str] = """
CREATE TABLE audit_logs (
    id UUID NOT NULL,
    entity_type VARCHAR NOT NULL,
    operation VARCHAR NOT NULL,
    entity_id VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    action_id UUID NOT NULL,
    request_id VARCHAR,
    triggered_by VARCHAR,
    description VARCHAR NOT NULL,
    duration INTERVAL,
    status VARCHAR(64) NOT NULL,
    CONSTRAINT pk_audit_logs PRIMARY KEY (id)
);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX ix_audit_logs_entity_type ON audit_logs (entity_type);
CREATE INDEX ix_audit_logs_operation ON audit_logs (operation);
CREATE INDEX ix_audit_logs_entity_id ON audit_logs (entity_id);
"""

# What 26.8 adds before 37d711158a8c: acted_as as uuid, the lookup columns and audit_log_scopes.
_ADDITIONS_26_8: Final[str] = """
ALTER TABLE audit_logs ADD COLUMN acted_as UUID;
ALTER TABLE audit_logs ADD COLUMN action_kind VARCHAR;
ALTER TABLE audit_logs ADD COLUMN lookup_kind VARCHAR;
ALTER TABLE audit_logs ADD COLUMN lookup_key VARCHAR;
CREATE INDEX ix_audit_logs_lookup ON audit_logs (lookup_kind, lookup_key);
CREATE TABLE audit_log_scopes (
    id UUID NOT NULL,
    audit_log_id UUID NOT NULL,
    scope_type VARCHAR NOT NULL,
    scope_id VARCHAR NOT NULL,
    CONSTRAINT pk_audit_log_scopes PRIMARY KEY (id),
    CONSTRAINT fk_audit_log_scopes_audit_log_id_audit_logs
        FOREIGN KEY (audit_log_id) REFERENCES audit_logs (id) ON DELETE CASCADE,
    CONSTRAINT uq_audit_log_scope UNIQUE (audit_log_id, scope_type, scope_id)
);
"""

_INDEXES_26_4: Final[dict[str, str]] = {
    "ix_audit_logs_created_at": "(created_at)",
    "ix_audit_logs_entity_id": "(entity_id)",
    "ix_audit_logs_entity_type": "(entity_type)",
    "ix_audit_logs_operation": "(operation)",
}


@dataclass(frozen=True)
class _Row:
    id: uuid.UUID
    entity_type: str
    operation: str
    triggered_by: str | None


_USER: Final[str] = str(uuid.uuid4())
_SESSION_CREATE: Final[_Row] = _Row(uuid.uuid4(), "session", "create", _USER)
_SYSTEM_PURGE: Final[_Row] = _Row(uuid.uuid4(), "session", "purge", None)
_AGENT_UPDATE_BY_USER: Final[_Row] = _Row(uuid.uuid4(), "agent", "update", _USER)
_HEARTBEAT: Final[_Row] = _Row(uuid.uuid4(), "agent", "update", None)
_ROWS: Final[tuple[_Row, ...]] = (
    _SESSION_CREATE,
    _SYSTEM_PURGE,
    _AGENT_UPDATE_BY_USER,
    _HEARTBEAT,
)
_KEPT: Final[tuple[_Row, ...]] = (_SESSION_CREATE, _SYSTEM_PURGE, _AGENT_UPDATE_BY_USER)


async def _execute(db: ExtendedAsyncSAEngine, script: str) -> None:
    async with db.begin() as conn:
        await conn.execute(sa.text(f"SET LOCAL search_path TO {_SCHEMA}"))
        for statement in filter(str.strip, script.split(";")):
            await conn.execute(sa.text(statement))


async def _insert_rows(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        for row in _ROWS:
            await conn.execute(
                sa.text(
                    f"INSERT INTO {_SCHEMA}.audit_logs"
                    " (id, entity_type, operation, action_id, triggered_by, description, status)"
                    " VALUES (:id, :entity_type, :operation, :action_id, :triggered_by, '', 'success')"
                ).bindparams(
                    id=row.id,
                    entity_type=row.entity_type,
                    operation=row.operation,
                    action_id=uuid.uuid4(),
                    triggered_by=row.triggered_by,
                )
            )


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with database_connection.begin() as conn:
        await conn.execute(sa.text(f"CREATE SCHEMA {_SCHEMA}"))
    try:
        yield database_connection
    finally:
        async with database_connection.begin() as conn:
            await conn.execute(sa.text(f"DROP SCHEMA {_SCHEMA} CASCADE"))


@pytest.fixture
async def table_26_4(db: ExtendedAsyncSAEngine) -> ExtendedAsyncSAEngine:
    await _execute(db, _TABLE_26_4)
    await _insert_rows(db)
    return db


@pytest.fixture
async def table_with_varchar_acted_as(table_26_4: ExtendedAsyncSAEngine) -> ExtendedAsyncSAEngine:
    await _execute(
        table_26_4,
        "ALTER TABLE audit_logs ADD COLUMN acted_as VARCHAR;"
        "UPDATE audit_logs SET acted_as = triggered_by",
    )
    return table_26_4


_DELEGATED_TO: Final[uuid.UUID] = uuid.uuid4()


@pytest.fixture
async def table_26_8(table_26_4: ExtendedAsyncSAEngine) -> ExtendedAsyncSAEngine:
    await _execute(table_26_4, _ADDITIONS_26_8)
    async with table_26_4.begin() as conn:
        await conn.execute(
            sa.text(
                f"UPDATE {_SCHEMA}.audit_logs SET acted_as = :acted_as WHERE id = :id"
            ).bindparams(acted_as=_DELEGATED_TO, id=_SESSION_CREATE.id)
        )
        for row in (_SESSION_CREATE, _HEARTBEAT):
            await conn.execute(
                sa.text(
                    f"INSERT INTO {_SCHEMA}.audit_log_scopes"
                    " (id, audit_log_id, scope_type, scope_id)"
                    " VALUES (:id, :audit_log_id, 'domain', 'default')"
                ).bindparams(id=uuid.uuid4(), audit_log_id=row.id)
            )
    return table_26_4


async def _rebuild(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.execute(sa.text(f"SET LOCAL search_path TO {_SCHEMA}"))
        await conn.run_sync(lambda sync_conn: AuditLogRebuild(sync_conn).run())


async def _rows(db: ExtendedAsyncSAEngine) -> dict[uuid.UUID, tuple[uuid.UUID | None, str]]:
    """Maps each row id to its `acted_as` and `action_name`."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.text(f"SELECT id, acted_as, action_name FROM {_SCHEMA}.audit_logs")
        )
        return {row.id: (row.acted_as, row.action_name) for row in rows}


async def _columns(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, bool]]:
    """Maps each column to its type and whether it allows NULL."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.text(
                "SELECT attname, format_type(atttypid, atttypmod) AS type, NOT attnotnull AS nullable"
                " FROM pg_attribute"
                f" WHERE attrelid = '{_SCHEMA}.audit_logs'::regclass AND attnum > 0"
                " AND NOT attisdropped"
            )
        )
        return {row.attname: (row.type, row.nullable) for row in rows}


async def _indexes(db: ExtendedAsyncSAEngine, table: str) -> dict[str, str]:
    """Maps each index to its column list."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.text(
                "SELECT indexname, indexdef FROM pg_indexes"
                " WHERE schemaname = :schema AND tablename = :table"
            ).bindparams(schema=_SCHEMA, table=table)
        )
        return {row.indexname: row.indexdef[row.indexdef.index("(") :] for row in rows}


async def _scope_audit_log_ids(db: ExtendedAsyncSAEngine) -> set[uuid.UUID]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.text(f"SELECT audit_log_id FROM {_SCHEMA}.audit_log_scopes"))
        return {row.audit_log_id for row in rows}


def _expected(row: _Row, acted_as: uuid.UUID | None = None) -> tuple[uuid.UUID | None, str]:
    if acted_as is None and row.triggered_by is not None:
        acted_as = uuid.UUID(row.triggered_by)
    return acted_as, f"{row.entity_type}:{row.operation}"


class TestRebuildFrom26_4:
    async def test_heartbeats_are_dropped_and_new_columns_are_filled(
        self, table_26_4: ExtendedAsyncSAEngine
    ) -> None:
        await _rebuild(table_26_4)

        assert await _rows(table_26_4) == {row.id: _expected(row) for row in _KEPT}

    async def test_columns_take_their_final_types(self, table_26_4: ExtendedAsyncSAEngine) -> None:
        await _rebuild(table_26_4)

        columns = await _columns(table_26_4)
        assert columns["acted_as"] == ("uuid", True)
        assert columns["action_name"] == ("character varying", False)
        assert columns["status"] == ("character varying(64)", False)

    async def test_keys_and_indexes_keep_their_names(
        self, table_26_4: ExtendedAsyncSAEngine
    ) -> None:
        await _rebuild(table_26_4)

        assert await _indexes(table_26_4, "audit_logs") == {
            **_INDEXES_26_4,
            "pk_audit_logs": "(id)",
            "ix_audit_logs_action_name": "(action_name)",
        }

    async def test_running_it_again_changes_nothing(
        self, table_26_4: ExtendedAsyncSAEngine
    ) -> None:
        await _rebuild(table_26_4)
        await _rebuild(table_26_4)

        assert await _rows(table_26_4) == {row.id: _expected(row) for row in _KEPT}


class TestRebuildWithVarcharActedAs:
    async def test_acted_as_is_cast_to_uuid(
        self, table_with_varchar_acted_as: ExtendedAsyncSAEngine
    ) -> None:
        await _rebuild(table_with_varchar_acted_as)

        assert await _rows(table_with_varchar_acted_as) == {row.id: _expected(row) for row in _KEPT}
        assert (await _columns(table_with_varchar_acted_as))["acted_as"] == ("uuid", True)


class TestRebuildFrom26_8:
    async def test_existing_acted_as_is_kept(self, table_26_8: ExtendedAsyncSAEngine) -> None:
        await _rebuild(table_26_8)

        assert await _rows(table_26_8) == {
            _SESSION_CREATE.id: _expected(_SESSION_CREATE, acted_as=_DELEGATED_TO),
            _SYSTEM_PURGE.id: (None, "session:purge"),
            _AGENT_UPDATE_BY_USER.id: (None, "agent:update"),
        }

    async def test_lookup_index_is_rebuilt(self, table_26_8: ExtendedAsyncSAEngine) -> None:
        await _rebuild(table_26_8)

        assert (await _indexes(table_26_8, "audit_logs"))["ix_audit_logs_lookup"] == (
            "(lookup_kind, lookup_key)"
        )

    async def test_scopes_of_heartbeats_are_dropped(
        self, table_26_8: ExtendedAsyncSAEngine
    ) -> None:
        await _rebuild(table_26_8)

        assert await _scope_audit_log_ids(table_26_8) == {_SESSION_CREATE.id}

    async def test_scope_foreign_key_points_at_the_new_table(
        self, table_26_8: ExtendedAsyncSAEngine
    ) -> None:
        await _rebuild(table_26_8)

        async with table_26_8.begin() as conn:
            await conn.execute(sa.text(f"DELETE FROM {_SCHEMA}.audit_logs"))
        assert await _scope_audit_log_ids(table_26_8) == set()
