"""Integration tests for purger with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base import (
    Purger,
    PurgeTarget,
    execute_purger,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class SimplePurgeTarget(PurgeTarget):
    """Simple purge target for testing with configurable conditions."""

    def __init__(
        self,
        pk_col: sa.Column,
        conditions: list[sa.sql.expression.ColumnElement[bool]] | None = None,
    ) -> None:
        self._pk_col = pk_col
        self._conditions = conditions or []

    @property
    def pk_column(self) -> sa.Column:
        return self._pk_col

    def build_subquery(self) -> sa.sql.Select:
        query = sa.select(self._pk_col)
        for cond in self._conditions:
            query = query.where(cond)
        return query


async def _count_rows(conn: AsyncConnection, table: sa.Table) -> int:
    """Count total rows in table."""
    result = await conn.execute(sa.select(sa.func.count()).select_from(table))
    return result.scalar() or 0


class TestPurgerBasic:
    """Basic tests for purger operations."""

    @pytest.fixture
    async def test_table(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[sa.Table, None]:
        """Create test table structure."""
        metadata = sa.MetaData()
        table = sa.Table(
            "test_purger_basic",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50)),
            sa.Column("status", sa.String(20)),
        )

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [table]))

        yield table

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.drop_all(c, [table]))

    @pytest.fixture
    async def test_rows(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table: sa.Table,
    ) -> sa.Table:
        """Insert 100 test rows (1-50: active, 51-100: inactive)."""
        async with database_engine.begin() as conn:
            await conn.execute(
                test_table.insert(),
                [
                    {
                        "id": i,
                        "name": f"item-{i:03d}",
                        "status": "active" if i <= 50 else "inactive",
                    }
                    for i in range(1, 101)
                ],
            )
        return test_table

    async def test_delete_with_single_condition(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test deletion with a single condition."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.status == "inactive"],
            )
            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 50
            assert await _count_rows(conn, table) == 50

    async def test_delete_with_multiple_conditions(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test deletion with multiple conditions (AND logic)."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[
                    table.c.status == "active",
                    table.c.id > 25,
                ],
            )
            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 25
            assert await _count_rows(conn, table) == 75

    async def test_delete_with_no_conditions(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test deletion with no conditions (delete all)."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(pk_col=table.c.id)
            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 100
            assert await _count_rows(conn, table) == 0

    async def test_delete_with_no_matching_rows(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test deletion when no rows match the condition."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.status == "deleted"],
            )
            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 0
            assert await _count_rows(conn, table) == 100


class TestPurgerBatching:
    """Tests for batched deletion."""

    @pytest.fixture
    async def test_table(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[sa.Table, None]:
        """Create test table structure."""
        metadata = sa.MetaData()
        table = sa.Table(
            "test_purger_batching",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50)),
            sa.Column("status", sa.String(20)),
        )

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [table]))

        yield table

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.drop_all(c, [table]))

    @pytest.fixture
    async def test_rows(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table: sa.Table,
    ) -> sa.Table:
        """Insert 100 test rows (1-50: active, 51-100: inactive)."""
        async with database_engine.begin() as conn:
            await conn.execute(
                test_table.insert(),
                [
                    {
                        "id": i,
                        "name": f"item-{i:03d}",
                        "status": "active" if i <= 50 else "inactive",
                    }
                    for i in range(1, 101)
                ],
            )
        return test_table

    async def test_batch_deletion(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test batched deletion with batch_size."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.status == "inactive"],
            )
            purger = Purger(target=target, batch_size=10)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 50
            assert await _count_rows(conn, table) == 50

    async def test_batch_deletion_exact_batch_size(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test when total rows to delete equals batch_size exactly."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.id <= 10],
            )
            purger = Purger(target=target, batch_size=10)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 10
            assert await _count_rows(conn, table) == 90

    async def test_batch_deletion_partial_last_batch(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test when last batch is smaller than batch_size."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.id <= 25],
            )
            purger = Purger(target=target, batch_size=10)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 25
            assert await _count_rows(conn, table) == 75

    async def test_batch_deletion_single_batch(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test when all rows fit in single batch."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.id <= 5],
            )
            purger = Purger(target=target, batch_size=100)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 5
            assert await _count_rows(conn, table) == 95


class TestPurgerEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    async def empty_table(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[sa.Table, None]:
        """Create empty test table."""
        metadata = sa.MetaData()
        table = sa.Table(
            "test_purger_empty",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50)),
        )

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [table]))

        yield table

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.drop_all(c, [table]))

    @pytest.fixture
    async def single_row_table(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[sa.Table, None]:
        """Create test table with single row."""
        metadata = sa.MetaData()
        table = sa.Table(
            "test_purger_single",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50)),
        )

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [table]))
            await conn.execute(table.insert(), [{"id": 1, "name": "only-one"}])

        yield table

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.drop_all(c, [table]))

    @pytest.fixture
    async def table_with_rows(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[sa.Table, None]:
        """Create test table with 100 rows for no-match testing."""
        metadata = sa.MetaData()
        table = sa.Table(
            "test_purger_nomatch",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("status", sa.String(20)),
        )

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [table]))
            await conn.execute(
                table.insert(),
                [{"id": i, "status": "active"} for i in range(1, 101)],
            )

        yield table

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.drop_all(c, [table]))

    async def test_empty_table(
        self,
        database_engine: ExtendedAsyncSAEngine,
        empty_table: sa.Table,
    ) -> None:
        """Test purger on empty table."""
        table = empty_table

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(pk_col=table.c.id)

            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]
            assert result.deleted_count == 0

            purger = Purger(target=target, batch_size=10)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]
            assert result.deleted_count == 0

    async def test_single_item_deletion(
        self,
        database_engine: ExtendedAsyncSAEngine,
        single_row_table: sa.Table,
    ) -> None:
        """Test purger with single item."""
        table = single_row_table

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(pk_col=table.c.id)
            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 1
            assert await _count_rows(conn, table) == 0

    async def test_batch_deletion_empty_result(
        self,
        database_engine: ExtendedAsyncSAEngine,
        table_with_rows: sa.Table,
    ) -> None:
        """Test batched deletion when no rows match condition."""
        table = table_with_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.status == "nonexistent"],
            )
            purger = Purger(target=target, batch_size=10)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 0
            assert await _count_rows(conn, table) == 100


class TestPurgeTargetWithComplexConditions:
    """Tests for PurgeTarget with complex conditions."""

    @pytest.fixture
    async def test_table(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[sa.Table, None]:
        """Create test table structure."""
        metadata = sa.MetaData()
        table = sa.Table(
            "test_purger_complex",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("status", sa.String(20)),
        )

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [table]))

        yield table

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: metadata.drop_all(c, [table]))

    @pytest.fixture
    async def test_rows(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table: sa.Table,
    ) -> sa.Table:
        """Insert 100 test rows (1-50: active, 51-100: inactive)."""
        async with database_engine.begin() as conn:
            await conn.execute(
                test_table.insert(),
                [
                    {
                        "id": i,
                        "status": "active" if i <= 50 else "inactive",
                    }
                    for i in range(1, 101)
                ],
            )
        return test_table

    async def test_with_or_conditions(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test purge target with OR combined conditions."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[sa.or_(table.c.id <= 10, table.c.id >= 91)],
            )
            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 20
            assert await _count_rows(conn, table) == 80

    async def test_with_negated_condition(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_rows: sa.Table,
    ) -> None:
        """Test purge target with negated condition."""
        table = test_rows

        async with database_engine.begin() as conn:
            target = SimplePurgeTarget(
                pk_col=table.c.id,
                conditions=[table.c.status != "active"],
            )
            purger = Purger(target=target)
            result = await execute_purger(conn, purger)  # type: ignore[arg-type]

            assert result.deleted_count == 50
            assert await _count_rows(conn, table) == 50


class PurgerTestRow(Base):
    """ORM model for purger testing using declarative mapping."""

    __tablename__ = "test_purger_orm"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False)


class ORMPurgeTarget(PurgeTarget):
    """Purge target using ORM model class."""

    def __init__(
        self,
        model: type[Base],
        pk_attr: str,
        conditions: list[sa.sql.expression.ColumnElement[bool]] | None = None,
    ) -> None:
        self._model = model
        self._pk_attr = pk_attr
        self._conditions = conditions or []

    @property
    def pk_column(self) -> sa.Column:
        return getattr(self._model, self._pk_attr)

    def build_subquery(self) -> sa.sql.Select:
        query = sa.select(getattr(self._model, self._pk_attr))
        for cond in self._conditions:
            query = query.where(cond)
        return query


class TestPurgerWithORMModel:
    """Tests for purger operations using ORM model based on declarative Base."""

    @pytest.fixture
    async def orm_table(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[PurgerTestRow], None]:
        """Create ORM model table structure."""
        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: PurgerTestRow.__table__.create(c, checkfirst=True))

        yield PurgerTestRow

        async with database_engine.begin() as conn:
            await conn.run_sync(lambda c: PurgerTestRow.__table__.drop(c, checkfirst=True))

    @pytest.fixture
    async def orm_rows(
        self,
        database_engine: ExtendedAsyncSAEngine,
        orm_table: type[PurgerTestRow],
    ) -> type[PurgerTestRow]:
        """Insert 100 test rows using ORM model (1-50: active, 51-100: inactive)."""
        async with database_engine.begin_session() as db_sess:
            for i in range(1, 101):
                row = PurgerTestRow(
                    id=i,
                    name=f"item-{i:03d}",
                    status="active" if i <= 50 else "inactive",
                )
                db_sess.add(row)
        return orm_table

    async def test_delete_with_orm_model(
        self,
        database_engine: ExtendedAsyncSAEngine,
        orm_rows: type[PurgerTestRow],
    ) -> None:
        """Test deletion using ORM model with single condition."""
        model = orm_rows

        async with database_engine.begin_session() as db_sess:
            target = ORMPurgeTarget(
                model=model,
                pk_attr="id",
                conditions=[model.status == "inactive"],
            )
            purger = Purger(target=target)
            result = await execute_purger(db_sess, purger)

            assert result.deleted_count == 50

            # Verify remaining rows
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(model))
            assert count_result.scalar() == 50

    async def test_delete_with_orm_model_batched(
        self,
        database_engine: ExtendedAsyncSAEngine,
        orm_rows: type[PurgerTestRow],
    ) -> None:
        """Test batched deletion using ORM model."""
        model = orm_rows

        async with database_engine.begin_session() as db_sess:
            target = ORMPurgeTarget(
                model=model,
                pk_attr="id",
                conditions=[model.status == "inactive"],
            )
            purger = Purger(target=target, batch_size=10)
            result = await execute_purger(db_sess, purger)

            assert result.deleted_count == 50

            # Verify remaining rows
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(model))
            assert count_result.scalar() == 50

    async def test_delete_all_with_orm_model(
        self,
        database_engine: ExtendedAsyncSAEngine,
        orm_rows: type[PurgerTestRow],
    ) -> None:
        """Test deleting all rows using ORM model."""
        model = orm_rows

        async with database_engine.begin_session() as db_sess:
            target = ORMPurgeTarget(
                model=model,
                pk_attr="id",
            )
            purger = Purger(target=target)
            result = await execute_purger(db_sess, purger)

            assert result.deleted_count == 100

            # Verify no rows remain
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(model))
            assert count_result.scalar() == 0

    async def test_delete_with_complex_condition_orm(
        self,
        database_engine: ExtendedAsyncSAEngine,
        orm_rows: type[PurgerTestRow],
    ) -> None:
        """Test deletion with complex conditions using ORM model."""
        model = orm_rows

        async with database_engine.begin_session() as db_sess:
            target = ORMPurgeTarget(
                model=model,
                pk_attr="id",
                conditions=[
                    sa.or_(model.id <= 10, model.id >= 91),
                ],
            )
            purger = Purger(target=target)
            result = await execute_purger(db_sess, purger)

            assert result.deleted_count == 20

            # Verify remaining rows
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(model))
            assert count_result.scalar() == 80
