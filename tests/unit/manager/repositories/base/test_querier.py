"""Integration tests for querier with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import Base, IDColumn
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BatchQuerierResult,
    OffsetPagination,
    Querier,
    QuerierResult,
    execute_batch_querier,
    execute_querier,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Single-row Querier Tests
# =============================================================================


class QuerierTestRowInt(Base):
    """ORM model for querier testing with integer PK."""

    __tablename__ = "test_querier_int_pk"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    value = sa.Column(sa.String(100), nullable=True)


class QuerierTestRowUUID(Base):
    """ORM model for querier testing with UUID PK."""

    __tablename__ = "test_querier_uuid_pk"
    __table_args__ = {"extend_existing": True}

    id = IDColumn()
    name = sa.Column(sa.String(50), nullable=False)
    value = sa.Column(sa.String(100), nullable=True)


class TestQuerierIntPK:
    """Tests for single-row querier with integer primary key."""

    @pytest.fixture
    async def int_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[QuerierTestRowInt], None]:
        """Create ORM test table with integer PK and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [QuerierTestRowInt.__table__])
            )

        yield QuerierTestRowInt

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_querier_int_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[QuerierTestRowInt],
    ) -> AsyncGenerator[list[dict[str, int | str]], None]:
        """Insert sample data and return list of inserted data."""
        data: list[dict[str, int | str]] = [
            {"id": 1, "name": "item-1", "value": "value-1"},
            {"id": 2, "name": "item-2", "value": "value-2"},
            {"id": 3, "name": "item-3", "value": "value-3"},
        ]

        async with database_connection.begin_session() as db_sess:
            table = int_row_class.__table__
            await db_sess.execute(table.insert(), data)

        yield data

    async def test_query_by_int_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[QuerierTestRowInt],
        sample_data: list[dict[str, int | str]],
    ) -> None:
        """Test querying a single row by integer primary key."""
        async with database_connection.begin_session() as db_sess:
            querier: Querier[QuerierTestRowInt] = Querier(
                row_class=QuerierTestRowInt,
                pk_value=2,
            )

            result = await execute_querier(db_sess, querier)

            assert result is not None
            assert isinstance(result, QuerierResult)
            assert result.row.id == 2
            assert result.row.name == "item-2"
            assert result.row.value == "value-2"

    async def test_query_no_matching_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[QuerierTestRowInt],
        sample_data: list[dict[str, int | str]],
    ) -> None:
        """Test querying a non-existent row returns None."""
        async with database_connection.begin_session() as db_sess:
            querier: Querier[QuerierTestRowInt] = Querier(
                row_class=QuerierTestRowInt,
                pk_value=999,
            )

            result = await execute_querier(db_sess, querier)

            assert result is None


class TestQuerierUUIDPK:
    """Tests for single-row querier with UUID primary key."""

    @pytest.fixture
    async def uuid_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[QuerierTestRowUUID], None]:
        """Create ORM test table with UUID PK and return row class."""
        async with database_connection.begin() as conn:
            await conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [QuerierTestRowUUID.__table__])
            )

        yield QuerierTestRowUUID

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_querier_uuid_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[QuerierTestRowUUID],
    ) -> AsyncGenerator[list[dict[str, UUID | str]], None]:
        """Insert sample data and return list of inserted data."""
        data: list[dict[str, UUID | str]] = [
            {"id": uuid4(), "name": "item-1", "value": "value-1"},
            {"id": uuid4(), "name": "item-2", "value": "value-2"},
            {"id": uuid4(), "name": "item-3", "value": "value-3"},
        ]

        async with database_connection.begin_session() as db_sess:
            table = uuid_row_class.__table__
            await db_sess.execute(table.insert(), data)

        yield data

    async def test_query_by_uuid_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[QuerierTestRowUUID],
        sample_data: list[dict[str, UUID | str]],
    ) -> None:
        """Test querying a single row by UUID primary key."""
        target_id = sample_data[1]["id"]

        async with database_connection.begin_session() as db_sess:
            querier: Querier[QuerierTestRowUUID] = Querier(
                row_class=QuerierTestRowUUID,
                pk_value=target_id,
            )

            result = await execute_querier(db_sess, querier)

            assert result is not None
            assert isinstance(result, QuerierResult)
            assert result.row.id == target_id
            assert result.row.name == "item-2"
            assert result.row.value == "value-2"

    async def test_query_no_matching_uuid(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[QuerierTestRowUUID],
        sample_data: list[dict[str, UUID | str]],
    ) -> None:
        """Test querying a non-existent UUID returns None."""
        non_existent_uuid = uuid4()

        async with database_connection.begin_session() as db_sess:
            querier: Querier[QuerierTestRowUUID] = Querier(
                row_class=QuerierTestRowUUID,
                pk_value=non_existent_uuid,
            )

            result = await execute_querier(db_sess, querier)

            assert result is None


# =============================================================================
# Batch Querier Tests
# =============================================================================


class BatchQuerierTestRow(Base):
    """ORM model for batch querier testing."""

    __tablename__ = "test_batch_querier_orm"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False)


class TestBatchQuerierBasic:
    """Tests for batch querier operations."""

    @pytest.fixture
    async def batch_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[BatchQuerierTestRow], None]:
        """Create ORM test table for batch querier and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [BatchQuerierTestRow.__table__])
            )

        yield BatchQuerierTestRow

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_batch_querier_orm CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_row_class: type[BatchQuerierTestRow],
    ) -> AsyncGenerator[list[dict[str, int | str]], None]:
        """Insert sample data for batch querier tests."""
        data = [
            {"id": i, "name": f"item-{i}", "status": "active" if i % 2 == 0 else "inactive"}
            for i in range(1, 11)
        ]

        async with database_connection.begin_session() as db_sess:
            table = batch_row_class.__table__
            await db_sess.execute(table.insert(), data)

        yield data

    async def test_batch_query_with_pagination(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_row_class: type[BatchQuerierTestRow],
        sample_data: list[dict[str, int | str]],
    ) -> None:
        """Test batch querier with offset pagination."""
        async with database_connection.begin_session() as db_sess:
            table = batch_row_class.__table__
            query = sa.select(table)
            querier = BatchQuerier(
                pagination=OffsetPagination(offset=0, limit=5),
            )

            result = await execute_batch_querier(db_sess, query, querier)

            assert isinstance(result, BatchQuerierResult)
            assert len(result.rows) == 5
            assert result.total_count == 10
            assert result.has_next_page is True
            assert result.has_previous_page is False

    async def test_batch_query_with_condition(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_row_class: type[BatchQuerierTestRow],
        sample_data: list[dict[str, int | str]],
    ) -> None:
        """Test batch querier with filter condition."""
        async with database_connection.begin_session() as db_sess:
            table = batch_row_class.__table__
            query = sa.select(table)
            querier = BatchQuerier(
                pagination=OffsetPagination(offset=0, limit=10),
                conditions=[lambda: table.c.status == "active"],
            )

            result = await execute_batch_querier(db_sess, query, querier)

            assert len(result.rows) == 5  # Only even-numbered items are active
            assert result.total_count == 5
            for row in result.rows:
                assert row.status == "active"

    async def test_batch_query_empty_result(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_row_class: type[BatchQuerierTestRow],
        sample_data: list[dict[str, int | str]],
    ) -> None:
        """Test batch querier with no matching rows."""
        async with database_connection.begin_session() as db_sess:
            table = batch_row_class.__table__
            query = sa.select(table)
            querier = BatchQuerier(
                pagination=OffsetPagination(offset=0, limit=10),
                conditions=[lambda: table.c.status == "deleted"],
            )

            result = await execute_batch_querier(db_sess, query, querier)

            assert len(result.rows) == 0
            assert result.total_count == 0
            assert result.has_next_page is False
            assert result.has_previous_page is False
