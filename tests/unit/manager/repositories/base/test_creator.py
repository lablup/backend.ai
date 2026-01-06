"""Integration tests for creator with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base import (
    BulkCreator,
    BulkCreatorResult,
    Creator,
    CreatorResult,
    CreatorSpec,
    execute_bulk_creator,
    execute_creator,
)
from ai.backend.testutils.db import with_tables

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


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create test tables using with_tables."""
    async with with_tables(database_connection, [CreatorTestRow]):
        yield


class TestCreatorBasic:
    """Basic tests for creator operations."""

    async def test_create_single_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating a single row with execute_creator."""
        async with database_connection.begin_session() as db_sess:
            # Verify table is empty
            result = await db_sess.execute(sa.select(sa.func.count()).select_from(CreatorTestRow))
            assert result.scalar() == 0

            spec = SimpleCreatorSpec(name="test-item", value="test-value")
            creator: Creator[CreatorTestRow] = Creator(spec=spec)

            result = await execute_creator(db_sess, creator)

            assert isinstance(result, CreatorResult)
            assert result.row.name == "test-item"
            assert result.row.value == "test-value"
            assert result.row.id is not None

            # Verify row was inserted
            count_result = await db_sess.execute(
                sa.select(sa.func.count()).select_from(CreatorTestRow)
            )
            assert count_result.scalar() == 1

    async def test_create_row_with_null_value(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
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
        create_tables: None,
    ) -> None:
        """Test creating multiple rows in sequence."""
        async with database_connection.begin_session() as db_sess:
            for i in range(5):
                spec = SimpleCreatorSpec(name=f"item-{i}", value=f"value-{i}")
                creator: Creator[CreatorTestRow] = Creator(spec=spec)
                result = await execute_creator(db_sess, creator)
                assert result.row.name == f"item-{i}"

            count_result = await db_sess.execute(
                sa.select(sa.func.count()).select_from(CreatorTestRow)
            )
            assert count_result.scalar() == 5


class TestBulkCreator:
    """Tests for bulk creator operations."""

    async def test_bulk_create_multiple_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating multiple rows with execute_bulk_creator."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(name="item-0", value="value-0"),
                SimpleCreatorSpec(name="item-1", value="value-1"),
                SimpleCreatorSpec(name="item-2", value="value-2"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)

            assert isinstance(result, BulkCreatorResult)
            assert len(result.rows) == 3

            # Verify all rows have generated IDs
            for row in result.rows:
                assert row.id is not None

            # Verify fields are correctly set
            assert result.rows[0].name == "item-0"
            assert result.rows[0].value == "value-0"
            assert result.rows[1].name == "item-1"
            assert result.rows[1].value == "value-1"
            assert result.rows[2].name == "item-2"
            assert result.rows[2].value == "value-2"

    async def test_bulk_create_verifies_in_database(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that bulk created rows are actually persisted in database."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(name="db-item-0", value="db-value-0"),
                SimpleCreatorSpec(name="db-item-1", value="db-value-1"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)
            created_ids = [row.id for row in result.rows]

            # Re-query from database to verify persistence
            query = (
                sa.select(CreatorTestRow)
                .where(CreatorTestRow.id.in_(created_ids))
                .order_by(CreatorTestRow.id)
            )
            db_result = await db_sess.execute(query)
            db_rows = db_result.scalars().all()

            assert len(db_rows) == 2
            assert db_rows[0].name == "db-item-0"
            assert db_rows[0].value == "db-value-0"
            assert db_rows[1].name == "db-item-1"
            assert db_rows[1].value == "db-value-1"

    async def test_bulk_create_empty_specs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk create with empty specs returns empty result."""
        async with database_connection.begin_session() as db_sess:
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=[])

            result = await execute_bulk_creator(db_sess, bulk_creator)

            assert isinstance(result, BulkCreatorResult)
            assert len(result.rows) == 0

            # Verify no rows were inserted
            count_result = await db_sess.execute(
                sa.select(sa.func.count()).select_from(CreatorTestRow)
            )
            assert count_result.scalar() == 0

    async def test_bulk_create_single_spec(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk create with single spec works correctly."""
        async with database_connection.begin_session() as db_sess:
            specs = [SimpleCreatorSpec(name="single-item", value="single-value")]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)

            assert len(result.rows) == 1
            assert result.rows[0].name == "single-item"
            assert result.rows[0].value == "single-value"
            assert result.rows[0].id is not None

    async def test_bulk_create_preserves_order(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that bulk create preserves input order in results."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(name="zebra", value="z"),
                SimpleCreatorSpec(name="apple", value="a"),
                SimpleCreatorSpec(name="mango", value="m"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)

            # Verify order matches input, not alphabetical
            assert result.rows[0].name == "zebra"
            assert result.rows[1].name == "apple"
            assert result.rows[2].name == "mango"

    async def test_bulk_create_with_null_values(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk create with nullable fields set to None."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(name="with-value", value="has-value"),
                SimpleCreatorSpec(name="without-value"),  # value is None
                SimpleCreatorSpec(name="also-without"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)

            assert result.rows[0].value == "has-value"
            assert result.rows[1].value is None
            assert result.rows[2].value is None

            # Verify in database
            created_ids = [row.id for row in result.rows]
            query = (
                sa.select(CreatorTestRow)
                .where(CreatorTestRow.id.in_(created_ids))
                .order_by(CreatorTestRow.id)
            )
            db_result = await db_sess.execute(query)
            db_rows = db_result.scalars().all()

            assert db_rows[0].value == "has-value"
            assert db_rows[1].value is None
            assert db_rows[2].value is None
