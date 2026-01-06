"""Integration tests for purger with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchPurgerResult,
    BatchPurgerSpec,
    Purger,
    PurgerResult,
    execute_batch_purger,
    execute_purger,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Note: This test file uses test-specific ORM models defined here, not application models.
# Tables are created/dropped per test class, which is appropriate for testing the purger itself.


# =============================================================================
# Single-row Purger Tests
# =============================================================================


class PurgerTestRowInt(Base):
    """ORM model for single-row purger testing with integer PK."""

    __tablename__ = "test_purger_int_pk"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False, default="pending")


class PurgerTestRowUUID(Base):
    """ORM model for single-row purger testing with UUID PK."""

    __tablename__ = "test_purger_uuid_pk"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False, default="pending")


class TestPurgerIntPK:
    """Tests for single-row purger with integer PK."""

    @pytest.fixture
    async def int_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[PurgerTestRowInt], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: Base.metadata.create_all(c, [PurgerTestRowInt.__table__]))

        yield PurgerTestRowInt

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_purger_int_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[PurgerTestRowInt],
    ) -> AsyncGenerator[list[int], None]:
        """Insert sample data and return their IDs."""
        ids: list[int] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = PurgerTestRowInt(name=f"item-{i}", status="active")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_delete_by_int_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[PurgerTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test deleting a single row by integer PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            purger: Purger[PurgerTestRowInt] = Purger(
                row_class=PurgerTestRowInt,
                pk_value=target_id,
            )

            result = await execute_purger(db_sess, purger)

            assert result is not None
            assert isinstance(result, PurgerResult)
            assert result.row.id == target_id
            assert result.row.name == "item-0"

            # Verify row was deleted
            count_result = await db_sess.execute(
                sa.select(sa.func.count()).select_from(int_row_class.__table__)
            )
            assert count_result.scalar() == 2

    async def test_delete_no_matching_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[PurgerTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test deleting when PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            purger: Purger[PurgerTestRowInt] = Purger(
                row_class=PurgerTestRowInt,
                pk_value=99999,
            )

            result = await execute_purger(db_sess, purger)

            assert result is None

            # Verify no rows were deleted
            count_result = await db_sess.execute(
                sa.select(sa.func.count()).select_from(int_row_class.__table__)
            )
            assert count_result.scalar() == 3


class TestPurgerUUIDPK:
    """Tests for single-row purger with UUID PK."""

    @pytest.fixture
    async def uuid_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[PurgerTestRowUUID], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [PurgerTestRowUUID.__table__])
            )

        yield PurgerTestRowUUID

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_purger_uuid_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[PurgerTestRowUUID],
    ) -> AsyncGenerator[list[UUID], None]:
        """Insert sample data and return their UUIDs."""
        ids: list[UUID] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = PurgerTestRowUUID(id=uuid.uuid4(), name=f"item-{i}", status="active")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_delete_by_uuid_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[PurgerTestRowUUID],
        sample_data: list[UUID],
    ) -> None:
        """Test deleting a single row by UUID PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            purger: Purger[PurgerTestRowUUID] = Purger(
                row_class=PurgerTestRowUUID,
                pk_value=target_id,
            )

            result = await execute_purger(db_sess, purger)

            assert result is not None
            assert isinstance(result, PurgerResult)
            assert result.row.id == target_id

    async def test_delete_no_matching_uuid(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[PurgerTestRowUUID],
        sample_data: list[UUID],
    ) -> None:
        """Test deleting when UUID PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            purger: Purger[PurgerTestRowUUID] = Purger(
                row_class=PurgerTestRowUUID,
                pk_value=uuid.uuid4(),
            )

            result = await execute_purger(db_sess, purger)

            assert result is None


# =============================================================================
# Batch Purger Tests (renamed from original Purger tests)
# =============================================================================


class SimpleBatchPurgerSpec(BatchPurgerSpec[Base]):
    """Simple batch purger spec for testing with configurable conditions."""

    def __init__(
        self,
        row_class: type[Base],
        conditions: list[sa.sql.expression.ColumnElement[bool]] | None = None,
    ) -> None:
        self._row_class = row_class
        self._conditions = conditions or []

    def build_subquery(self) -> sa.sql.Select[tuple[Base]]:
        query = sa.select(self._row_class)
        for cond in self._conditions:
            query = query.where(cond)
        return query


class BatchPurgerBasicRow(Base):
    """ORM model for basic batch purger testing."""

    __tablename__ = "test_batch_purger_basic"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False)


class BatchPurgerBatchingRow(Base):
    """ORM model for batch purger batching tests."""

    __tablename__ = "test_batch_purger_batching"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False)


class BatchPurgerEdgeCaseRow(Base):
    """ORM model for batch purger edge case tests."""

    __tablename__ = "test_batch_purger_empty"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=True)


class TestBatchPurgerBasic:
    """Basic tests for batch purger operations."""

    @pytest.fixture
    async def test_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[BatchPurgerBasicRow], None]:
        """Create test table structure."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: BatchPurgerBasicRow.__table__.create(c, checkfirst=True))

        yield BatchPurgerBasicRow

        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: BatchPurgerBasicRow.__table__.drop(c, checkfirst=True))

    @pytest.fixture
    async def test_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_row_class: type[BatchPurgerBasicRow],
    ) -> type[BatchPurgerBasicRow]:
        """Insert 100 test rows (1-50: active, 51-100: inactive)."""
        async with database_connection.begin_session() as db_sess:
            for i in range(1, 101):
                row = BatchPurgerBasicRow(
                    id=i,
                    name=f"item-{i:03d}",
                    status="active" if i <= 50 else "inactive",
                )
                db_sess.add(row)
        return test_row_class

    async def test_delete_with_single_condition(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_rows: type[BatchPurgerBasicRow],
    ) -> None:
        """Test deletion with a single condition."""
        row_class = test_rows

        async with database_connection.begin_session() as db_sess:
            spec = SimpleBatchPurgerSpec(
                row_class=row_class,
                conditions=[row_class.status == "inactive"],
            )
            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)

            assert isinstance(result, BatchPurgerResult)
            assert result.deleted_count == 50

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 50

    async def test_delete_with_multiple_conditions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_rows: type[BatchPurgerBasicRow],
    ) -> None:
        """Test deletion with multiple conditions (AND logic)."""
        row_class = test_rows

        async with database_connection.begin_session() as db_sess:
            spec = SimpleBatchPurgerSpec(
                row_class=row_class,
                conditions=[
                    row_class.status == "active",
                    row_class.id > 25,
                ],
            )
            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 25

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 75

    async def test_delete_with_no_conditions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_rows: type[BatchPurgerBasicRow],
    ) -> None:
        """Test deletion with no conditions (delete all)."""
        row_class = test_rows

        async with database_connection.begin_session() as db_sess:
            spec = SimpleBatchPurgerSpec(row_class=row_class)
            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 100

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 0

    async def test_delete_with_no_matching_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_rows: type[BatchPurgerBasicRow],
    ) -> None:
        """Test deletion when no rows match the condition."""
        row_class = test_rows

        async with database_connection.begin_session() as db_sess:
            spec = SimpleBatchPurgerSpec(
                row_class=row_class,
                conditions=[row_class.status == "deleted"],
            )
            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 0

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 100


class TestBatchPurgerBatching:
    """Tests for batched deletion."""

    @pytest.fixture
    async def test_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[BatchPurgerBatchingRow], None]:
        """Create test table structure."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: BatchPurgerBatchingRow.__table__.create(c, checkfirst=True)
            )

        yield BatchPurgerBatchingRow

        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: BatchPurgerBatchingRow.__table__.drop(c, checkfirst=True))

    @pytest.fixture
    async def test_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_row_class: type[BatchPurgerBatchingRow],
    ) -> type[BatchPurgerBatchingRow]:
        """Insert 100 test rows (1-50: active, 51-100: inactive)."""
        async with database_connection.begin_session() as db_sess:
            for i in range(1, 101):
                row = BatchPurgerBatchingRow(
                    id=i,
                    name=f"item-{i:03d}",
                    status="active" if i <= 50 else "inactive",
                )
                db_sess.add(row)
        return test_row_class

    async def test_batch_deletion(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_rows: type[BatchPurgerBatchingRow],
    ) -> None:
        """Test batched deletion with batch_size."""
        row_class = test_rows

        async with database_connection.begin_session() as db_sess:
            spec = SimpleBatchPurgerSpec(
                row_class=row_class,
                conditions=[row_class.status == "inactive"],
            )
            purger = BatchPurger(spec=spec, batch_size=10)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 50

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 50

    async def test_batch_deletion_exact_batch_size(
        self,
        database_connection: ExtendedAsyncSAEngine,
        test_rows: type[BatchPurgerBatchingRow],
    ) -> None:
        """Test when total rows to delete equals batch_size exactly."""
        row_class = test_rows

        async with database_connection.begin_session() as db_sess:
            spec = SimpleBatchPurgerSpec(
                row_class=row_class,
                conditions=[row_class.id <= 10],
            )
            purger = BatchPurger(spec=spec, batch_size=10)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 10

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 90


class TestBatchPurgerEdgeCases:
    """Tests for batch purger edge cases."""

    @pytest.fixture
    async def empty_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[BatchPurgerEdgeCaseRow], None]:
        """Create empty test table."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: BatchPurgerEdgeCaseRow.__table__.create(c, checkfirst=True)
            )

        yield BatchPurgerEdgeCaseRow

        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: BatchPurgerEdgeCaseRow.__table__.drop(c, checkfirst=True))

    async def test_empty_table(
        self,
        database_connection: ExtendedAsyncSAEngine,
        empty_row_class: type[BatchPurgerEdgeCaseRow],
    ) -> None:
        """Test batch purger on empty table."""
        row_class = empty_row_class

        async with database_connection.begin_session() as db_sess:
            spec = SimpleBatchPurgerSpec(row_class=row_class)

            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)
            assert result.deleted_count == 0

            purger = BatchPurger(spec=spec, batch_size=10)
            result = await execute_batch_purger(db_sess, purger)
            assert result.deleted_count == 0


class BatchPurgerTestRow(Base):
    """ORM model for batch purger testing using declarative mapping."""

    __tablename__ = "test_batch_purger_orm"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False)


class ORMBatchPurgerSpec(BatchPurgerSpec[Base]):
    """Batch purger spec using ORM model class."""

    def __init__(
        self,
        row_class: type[Base],
        conditions: list[sa.sql.expression.ColumnElement[bool]] | None = None,
    ) -> None:
        self._row_class = row_class
        self._conditions = conditions or []

    def build_subquery(self) -> sa.sql.Select[tuple[Base]]:
        query = sa.select(self._row_class)
        for cond in self._conditions:
            query = query.where(cond)
        return query


class TestBatchPurgerWithORMModel:
    """Tests for batch purger operations using ORM model."""

    @pytest.fixture
    async def orm_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[BatchPurgerTestRow], None]:
        """Create ORM model table structure."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: BatchPurgerTestRow.__table__.create(c, checkfirst=True))

        yield BatchPurgerTestRow

        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: BatchPurgerTestRow.__table__.drop(c, checkfirst=True))

    @pytest.fixture
    async def orm_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        orm_row_class: type[BatchPurgerTestRow],
    ) -> type[BatchPurgerTestRow]:
        """Insert 100 test rows using ORM model (1-50: active, 51-100: inactive)."""
        async with database_connection.begin_session() as db_sess:
            for i in range(1, 101):
                row = BatchPurgerTestRow(
                    id=i,
                    name=f"item-{i:03d}",
                    status="active" if i <= 50 else "inactive",
                )
                db_sess.add(row)
        return orm_row_class

    async def test_delete_with_orm_model(
        self,
        database_connection: ExtendedAsyncSAEngine,
        orm_rows: type[BatchPurgerTestRow],
    ) -> None:
        """Test deletion using ORM model with single condition."""
        row_class = orm_rows

        async with database_connection.begin_session() as db_sess:
            spec = ORMBatchPurgerSpec(
                row_class=row_class,
                conditions=[row_class.status == "inactive"],
            )
            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 50

            # Verify remaining rows
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 50

    async def test_delete_with_orm_model_batched(
        self,
        database_connection: ExtendedAsyncSAEngine,
        orm_rows: type[BatchPurgerTestRow],
    ) -> None:
        """Test batched deletion using ORM model."""
        row_class = orm_rows

        async with database_connection.begin_session() as db_sess:
            spec = ORMBatchPurgerSpec(
                row_class=row_class,
                conditions=[row_class.status == "inactive"],
            )
            purger = BatchPurger(spec=spec, batch_size=10)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 50

            # Verify remaining rows
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 50


# =============================================================================
# Batch Purger Composite PK Tests
# =============================================================================


class BatchPurgerCompositePKRow(Base):
    """ORM model for composite PK batch purger testing."""

    __tablename__ = "test_batch_purger_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id = sa.Column(sa.Integer, primary_key=True)
    item_id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False)


class CompositePKBatchPurgerSpec(BatchPurgerSpec[BatchPurgerCompositePKRow]):
    """Batch purger spec for composite PK testing."""

    def __init__(
        self,
        conditions: list[sa.sql.expression.ColumnElement[bool]] | None = None,
    ) -> None:
        self._conditions = conditions or []

    def build_subquery(self) -> sa.sql.Select[tuple[BatchPurgerCompositePKRow]]:
        query = sa.select(BatchPurgerCompositePKRow)
        for cond in self._conditions:
            query = query.where(cond)
        return query


class TestBatchPurgerCompositePK:
    """Tests for batch purger with composite primary key."""

    @pytest.fixture
    async def composite_pk_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[BatchPurgerCompositePKRow], None]:
        """Create test table with composite PK."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: BatchPurgerCompositePKRow.__table__.create(c, checkfirst=True)
            )

        yield BatchPurgerCompositePKRow

        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: BatchPurgerCompositePKRow.__table__.drop(c, checkfirst=True)
            )

    @pytest.fixture
    async def composite_pk_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        composite_pk_row_class: type[BatchPurgerCompositePKRow],
    ) -> type[BatchPurgerCompositePKRow]:
        """Insert test rows with composite PK (3 tenants x 10 items each)."""
        async with database_connection.begin_session() as db_sess:
            for tenant_id in range(1, 4):  # 3 tenants
                for item_id in range(1, 11):  # 10 items each
                    row = BatchPurgerCompositePKRow(
                        tenant_id=tenant_id,
                        item_id=item_id,
                        name=f"item-{tenant_id}-{item_id}",
                        status="active" if item_id <= 5 else "inactive",
                    )
                    db_sess.add(row)
        return composite_pk_row_class

    async def test_delete_with_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        composite_pk_rows: type[BatchPurgerCompositePKRow],
    ) -> None:
        """Test deletion with composite primary key."""
        row_class = composite_pk_rows

        async with database_connection.begin_session() as db_sess:
            # Delete all inactive items (items 6-10 for each tenant = 15 rows)
            spec = CompositePKBatchPurgerSpec(
                conditions=[row_class.status == "inactive"],
            )
            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 15  # 3 tenants * 5 inactive items

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 15  # 3 tenants * 5 active items

    async def test_delete_with_composite_pk_specific_tenant(
        self,
        database_connection: ExtendedAsyncSAEngine,
        composite_pk_rows: type[BatchPurgerCompositePKRow],
    ) -> None:
        """Test deletion with composite PK filtering by one PK column."""
        row_class = composite_pk_rows

        async with database_connection.begin_session() as db_sess:
            # Delete all items for tenant 2
            spec = CompositePKBatchPurgerSpec(
                conditions=[row_class.tenant_id == 2],
            )
            purger = BatchPurger(spec=spec)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 10  # All 10 items for tenant 2

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 20  # Remaining items for tenants 1 and 3

    async def test_delete_with_composite_pk_batched(
        self,
        database_connection: ExtendedAsyncSAEngine,
        composite_pk_rows: type[BatchPurgerCompositePKRow],
    ) -> None:
        """Test batched deletion with composite primary key."""
        row_class = composite_pk_rows

        async with database_connection.begin_session() as db_sess:
            # Delete inactive items with small batch size
            spec = CompositePKBatchPurgerSpec(
                conditions=[row_class.status == "inactive"],
            )
            purger = BatchPurger(spec=spec, batch_size=5)
            result = await execute_batch_purger(db_sess, purger)

            assert result.deleted_count == 15

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(row_class))
            assert count_result.scalar() == 15
