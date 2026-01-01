"""Integration tests for creator with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base import (
    Creator,
    CreatorResult,
    CreatorSpec,
    execute_creator,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class CreatorTestRow(Base):
    """ORM model for creator testing using declarative mapping."""

    __tablename__ = "test_creator_orm"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    value = sa.Column(sa.String(100), nullable=True)


class SimpleCreatorSpec(CreatorSpec[CreatorTestRow]):
    """Simple creator spec for testing."""

    def __init__(self, name: str, value: str | None = None) -> None:
        self._name = name
        self._value = value

    def build_row(self) -> CreatorTestRow:
        return CreatorTestRow(name=self._name, value=self._value)


class TestCreatorBasic:
    """Basic tests for creator operations."""

    @pytest.fixture
    async def orm_table(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[sa.Table, None]:
        """Create ORM test table."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: Base.metadata.create_all(c, [CreatorTestRow.__table__]))

        yield CreatorTestRow.__table__

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_creator_orm CASCADE"))

    async def test_create_single_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        orm_table: sa.Table,
    ) -> None:
        """Test creating a single row with execute_creator."""
        async with database_connection.begin_session() as db_sess:
            # Verify table is empty
            result = await db_sess.execute(sa.select(sa.func.count()).select_from(orm_table))
            assert result.scalar() == 0

            spec = SimpleCreatorSpec(name="test-item", value="test-value")
            creator: Creator[CreatorTestRow] = Creator(spec=spec)

            result = await execute_creator(db_sess, creator)

            assert isinstance(result, CreatorResult)
            assert result.row.name == "test-item"
            assert result.row.value == "test-value"
            assert result.row.id is not None

            # Verify row was inserted
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(orm_table))
            assert count_result.scalar() == 1

    async def test_create_row_with_null_value(
        self,
        database_connection: ExtendedAsyncSAEngine,
        orm_table: sa.Table,
    ) -> None:
        """Test creating a row with null optional field."""
        async with database_connection.begin_session() as db_sess:
            spec = SimpleCreatorSpec(name="null-value-item")
            creator: Creator[CreatorTestRow] = Creator(spec=spec)

            result = await execute_creator(db_sess, creator)

            assert result.row.name == "null-value-item"
            assert result.row.value is None
            assert result.row.id is not None

    async def test_create_multiple_rows_sequentially(
        self,
        database_connection: ExtendedAsyncSAEngine,
        orm_table: sa.Table,
    ) -> None:
        """Test creating multiple rows in sequence."""
        async with database_connection.begin_session() as db_sess:
            for i in range(5):
                spec = SimpleCreatorSpec(name=f"item-{i}", value=f"value-{i}")
                creator: Creator[CreatorTestRow] = Creator(spec=spec)
                result = await execute_creator(db_sess, creator)
                assert result.row.name == f"item-{i}"

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(orm_table))
            assert count_result.scalar() == 5
