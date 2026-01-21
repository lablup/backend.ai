"""Integration tests for upserter with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base import (
    Upserter,
    UpserterResult,
    UpserterSpec,
    execute_upserter,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class UpserterTestRow(Base):
    """ORM model for upserter testing."""

    __tablename__ = "test_upserter_orm"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False, unique=True)
    value = sa.Column(sa.String(100), nullable=True)


class SimpleUpserterSpec(UpserterSpec[UpserterTestRow]):
    """Simple upserter spec for testing."""

    def __init__(self, name: str, value: str | None = None) -> None:
        self._name = name
        self._value = value

    @property
    def row_class(self) -> type[UpserterTestRow]:
        return UpserterTestRow

    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self._name, "value": self._value}

    def build_update_values(self) -> dict[str, Any]:
        # On conflict, only update value (not name since it's the conflict key)
        return {"value": self._value}


class TestUpserterBasic:
    """Tests for upserter operations."""

    @pytest.fixture
    async def upserter_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpserterTestRow], None]:
        """Create ORM test table with unique constraint on name and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: Base.metadata.create_all(c, [UpserterTestRow.__table__]))

        yield UpserterTestRow

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_upserter_orm CASCADE"))

    async def test_upsert_insert_new_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test upserting a new row (insert case)."""
        async with database_connection.begin_session() as db_sess:
            spec = SimpleUpserterSpec(name="new-item", value="initial-value")
            upserter: Upserter[UpserterTestRow] = Upserter(spec=spec)

            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["name"],
            )

            assert isinstance(result, UpserterResult)
            assert result.row.name == "new-item"
            assert result.row.value == "initial-value"

            table = upserter_row_class.__table__
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 1

    async def test_upsert_update_existing_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test upserting an existing row (update case)."""
        table = upserter_row_class.__table__
        async with database_connection.begin_session() as db_sess:
            # First insert
            await db_sess.execute(table.insert().values(name="existing-item", value="old-value"))
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 1

            # Upsert should update
            spec = SimpleUpserterSpec(name="existing-item", value="new-value")
            upserter: Upserter[UpserterTestRow] = Upserter(spec=spec)

            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["name"],
            )

            assert result.row.name == "existing-item"
            assert result.row.value == "new-value"

            # Should still be 1 row (updated, not inserted)
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 1

            # Verify the value was actually updated
            row_result = await db_sess.execute(
                sa.select(table).where(table.c.name == "existing-item")
            )
            row = row_result.fetchone()
            assert row is not None
            assert row.value == "new-value"
