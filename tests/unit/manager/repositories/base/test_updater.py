"""Integration tests for updater with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base import (
    BatchUpdater,
    BatchUpdaterResult,
    BatchUpdaterSpec,
    Updater,
    UpdaterResult,
    UpdaterSpec,
    execute_batch_updater,
    execute_updater,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class UpdaterTestRowInt(Base):
    """ORM model for updater testing with integer PK."""

    __tablename__ = "test_updater_int_pk"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False, default="pending")
    value = sa.Column(sa.Integer, nullable=True)


class UpdaterTestRowUUID(Base):
    """ORM model for updater testing with UUID PK."""

    __tablename__ = "test_updater_uuid_pk"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False, default="pending")


class UpdaterTestRowStr(Base):
    """ORM model for updater testing with string PK."""

    __tablename__ = "test_updater_str_pk"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.String(50), primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    status = sa.Column(sa.String(20), nullable=False, default="pending")


# Single Updater Specs for each row type


class IntPKStatusUpdaterSpec(UpdaterSpec[UpdaterTestRowInt]):
    """Updater spec for updating status on integer PK table."""

    def __init__(self, new_status: str, new_value: int | None = None) -> None:
        self._new_status = new_status
        self._new_value = new_value

    @property
    def row_class(self) -> type[UpdaterTestRowInt]:
        return UpdaterTestRowInt

    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"status": self._new_status}
        if self._new_value is not None:
            values["value"] = self._new_value
        return values


class UUIDPKStatusUpdaterSpec(UpdaterSpec[UpdaterTestRowUUID]):
    """Updater spec for updating status on UUID PK table."""

    def __init__(self, new_status: str) -> None:
        self._new_status = new_status

    @property
    def row_class(self) -> type[UpdaterTestRowUUID]:
        return UpdaterTestRowUUID

    def build_values(self) -> dict[str, Any]:
        return {"status": self._new_status}


class StrPKStatusUpdaterSpec(UpdaterSpec[UpdaterTestRowStr]):
    """Updater spec for updating status on string PK table."""

    def __init__(self, new_status: str) -> None:
        self._new_status = new_status

    @property
    def row_class(self) -> type[UpdaterTestRowStr]:
        return UpdaterTestRowStr

    def build_values(self) -> dict[str, Any]:
        return {"status": self._new_status}


# Batch Updater Specs


class IntPKBatchUpdaterSpec(BatchUpdaterSpec[UpdaterTestRowInt]):
    """Batch updater spec for updating status on integer PK table."""

    def __init__(self, new_status: str) -> None:
        self._new_status = new_status

    @property
    def row_class(self) -> type[UpdaterTestRowInt]:
        return UpdaterTestRowInt

    def build_values(self) -> dict[str, Any]:
        return {"status": self._new_status}


class TestUpdaterIntPK:
    """Tests for single-row updater with integer PK."""

    @pytest.fixture
    async def int_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowInt], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowInt.__table__])
            )

        yield UpdaterTestRowInt

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_int_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
    ) -> AsyncGenerator[list[int], None]:
        """Insert sample data and return their IDs."""
        ids: list[int] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = UpdaterTestRowInt(name=f"item-{i}", status="pending", value=i * 10)
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_update_by_int_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating a single row by integer PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKStatusUpdaterSpec(new_status="active"),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert isinstance(result, UpdaterResult)
            assert result.row.status == "active"
            assert result.row.id == target_id

    async def test_update_multiple_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating multiple fields at once."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[1]
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKStatusUpdaterSpec(new_status="completed", new_value=999),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert result.row.status == "completed"
            assert result.row.value == 999

    async def test_update_no_matching_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating when PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKStatusUpdaterSpec(new_status="active"),
                pk_value=99999,
            )

            result = await execute_updater(db_sess, updater)

            assert result is None


class TestUpdaterUUIDPK:
    """Tests for single-row updater with UUID PK."""

    @pytest.fixture
    async def uuid_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowUUID], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowUUID.__table__])
            )

        yield UpdaterTestRowUUID

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_uuid_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[UpdaterTestRowUUID],
    ) -> AsyncGenerator[list[UUID], None]:
        """Insert sample data and return their UUIDs."""
        ids: list[UUID] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = UpdaterTestRowUUID(id=uuid.uuid4(), name=f"item-{i}", status="pending")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_update_by_uuid_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[UpdaterTestRowUUID],
        sample_data: list[UUID],
    ) -> None:
        """Test updating a single row by UUID PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            updater: Updater[UpdaterTestRowUUID] = Updater(
                spec=UUIDPKStatusUpdaterSpec(new_status="active"),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert isinstance(result, UpdaterResult)
            assert result.row.status == "active"
            assert result.row.id == target_id

    async def test_update_no_matching_uuid(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[UpdaterTestRowUUID],
        sample_data: list[UUID],
    ) -> None:
        """Test updating when UUID PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            non_existent_id = uuid.uuid4()
            updater: Updater[UpdaterTestRowUUID] = Updater(
                spec=UUIDPKStatusUpdaterSpec(new_status="active"),
                pk_value=non_existent_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is None


class TestUpdaterStrPK:
    """Tests for single-row updater with string PK."""

    @pytest.fixture
    async def str_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowStr], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowStr.__table__])
            )

        yield UpdaterTestRowStr

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_str_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        str_row_class: type[UpdaterTestRowStr],
    ) -> AsyncGenerator[list[str], None]:
        """Insert sample data and return their string IDs."""
        ids: list[str] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                str_id = f"item-key-{i}"
                row = UpdaterTestRowStr(id=str_id, name=f"item-{i}", status="pending")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(str_id)
        yield ids

    async def test_update_by_str_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        str_row_class: type[UpdaterTestRowStr],
        sample_data: list[str],
    ) -> None:
        """Test updating a single row by string PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            updater: Updater[UpdaterTestRowStr] = Updater(
                spec=StrPKStatusUpdaterSpec(new_status="active"),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert isinstance(result, UpdaterResult)
            assert result.row.status == "active"
            assert result.row.id == target_id

    async def test_update_no_matching_str(
        self,
        database_connection: ExtendedAsyncSAEngine,
        str_row_class: type[UpdaterTestRowStr],
        sample_data: list[str],
    ) -> None:
        """Test updating when string PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowStr] = Updater(
                spec=StrPKStatusUpdaterSpec(new_status="active"),
                pk_value="non-existent-key",
            )

            result = await execute_updater(db_sess, updater)

            assert result is None


class TestBatchUpdater:
    """Tests for batch updater operations."""

    @pytest.fixture
    async def int_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowInt], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowInt.__table__])
            )

        yield UpdaterTestRowInt

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_int_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
    ) -> AsyncGenerator[list[int], None]:
        """Insert sample data and return their IDs."""
        ids: list[int] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = UpdaterTestRowInt(name=f"item-{i}", status="pending", value=i * 10)
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_bulk_update(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating multiple rows at once."""
        async with database_connection.begin_session() as db_sess:
            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "pending",
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 3

            query = (
                sa.select(sa.func.count())
                .select_from(UpdaterTestRowInt.__table__)
                .where(UpdaterTestRowInt.__table__.c.status == "processed")
            )
            count = (await db_sess.execute(query)).scalar()
            assert count == 3

    async def test_bulk_update_with_multiple_conditions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update with multiple AND conditions."""
        async with database_connection.begin_session() as db_sess:
            # Only update rows with status="pending" AND value >= 10
            # sample_data has values: 0, 10, 20 -> should update 2 rows
            spec = IntPKBatchUpdaterSpec(new_status="filtered")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "pending",
                    lambda: UpdaterTestRowInt.__table__.c.value >= 10,
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 2

            query = (
                sa.select(sa.func.count())
                .select_from(UpdaterTestRowInt.__table__)
                .where(UpdaterTestRowInt.__table__.c.status == "filtered")
            )
            count = (await db_sess.execute(query)).scalar()
            assert count == 2

    async def test_bulk_update_no_matching_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update when no rows match."""
        async with database_connection.begin_session() as db_sess:
            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "nonexistent",
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 0

    async def test_bulk_update_empty_table(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
    ) -> None:
        """Test batch updating an empty table."""
        async with database_connection.begin_session() as db_sess:
            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "pending",
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 0
