"""Verifies the JSON null to SQL NULL migration against a real database.

The tables it names are created as one-column stand-ins in a separate schema, which the
migration reaches through `search_path`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Final

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.alembic.versions.e4a9c2d71b58_turn_json_null_pydantic_columns_into_sql_null import (
    NULLABLE_PYDANTIC_COLUMNS,
    turn_json_null_into_sql_null,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

_SCHEMA: Final[str] = "json_null_probe"
_OBJECT_TEXT: Final[str] = '{"key": "value"}'


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with database_connection.begin() as conn:
        await conn.execute(sa.text(f"CREATE SCHEMA {_SCHEMA}"))
        for table, column in NULLABLE_PYDANTIC_COLUMNS:
            await conn.execute(
                sa.text(f"CREATE TABLE {_SCHEMA}.{table} (id integer PRIMARY KEY, {column} jsonb)")
            )
            await conn.execute(
                sa.text(
                    f"INSERT INTO {_SCHEMA}.{table} (id, {column}) VALUES "
                    "(1, 'null'::jsonb), (2, CAST(:object AS jsonb)), (3, NULL)"
                ).bindparams(object=_OBJECT_TEXT)
            )
    try:
        yield database_connection
    finally:
        async with database_connection.begin() as conn:
            await conn.execute(sa.text(f"DROP SCHEMA {_SCHEMA} CASCADE"))


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.execute(sa.text(f"SET LOCAL search_path TO {_SCHEMA}"))
        await conn.run_sync(turn_json_null_into_sql_null)


async def _values(db: ExtendedAsyncSAEngine, table: str, column: str) -> dict[int, str | None]:
    """Maps each row id to its value as JSON text, or None for SQL NULL."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.text(f"SELECT id, {column}::text AS value FROM {_SCHEMA}.{table} ORDER BY id")
        )
        return {row.id: row.value for row in rows}


class TestTurnJsonNullIntoSqlNull:
    @pytest.mark.parametrize(("table", "column"), NULLABLE_PYDANTIC_COLUMNS)
    async def test_json_null_becomes_sql_null_and_objects_stay(
        self, db: ExtendedAsyncSAEngine, table: str, column: str
    ) -> None:
        await _run(db)

        assert await _values(db, table, column) == {1: None, 2: _OBJECT_TEXT, 3: None}

    async def test_running_it_again_changes_nothing(self, db: ExtendedAsyncSAEngine) -> None:
        await _run(db)
        await _run(db)

        for table, column in NULLABLE_PYDANTIC_COLUMNS:
            assert await _values(db, table, column) == {1: None, 2: _OBJECT_TEXT, 3: None}
