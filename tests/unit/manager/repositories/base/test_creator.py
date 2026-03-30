"""Integration tests for creator with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from datetime import datetime
from typing import TYPE_CHECKING

import aiohttp.web
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.repository import (
    RepositoryIntegrityError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.repositories.base import (
    BulkCreator,
    BulkCreatorResult,
    Creator,
    CreatorResult,
    CreatorSpec,
    IntegrityErrorCheck,
    execute_bulk_creator,
    execute_bulk_creator_partial,
    execute_creator,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class CreatorTestRow(Base):  # type: ignore[misc]
    """ORM model for creator testing using declarative mapping."""

    __tablename__ = "test_creator_orm"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    value: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)


class SimpleCreatorSpec(CreatorSpec[CreatorTestRow]):
    """Simple creator spec for testing."""

    def __init__(self, name: str, value: str | None = None) -> None:
        self._name = name
        self._value = value

    def build_row(self) -> CreatorTestRow:
        return CreatorTestRow(name=self._name, value=self._value)


class FailingCreatorSpec(CreatorSpec[CreatorTestRow]):
    """Creator spec that simulates a failure during build_row."""

    def __init__(self, should_fail: bool = True, name: str = "test") -> None:
        self._should_fail = should_fail
        self._name = name

    def build_row(self) -> CreatorTestRow:
        if self._should_fail:
            raise ValueError(f"Simulated failure for {self._name}")
        return CreatorTestRow(name=self._name, value="success")


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
            db_result = await db_sess.execute(
                sa.select(sa.func.count()).select_from(CreatorTestRow)
            )
            assert db_result.scalar() == 0

            spec = SimpleCreatorSpec(name="test-item", value="test-value")
            creator: Creator[CreatorTestRow] = Creator(spec=spec)

            create_result = await execute_creator(db_sess, creator)

            assert isinstance(create_result, CreatorResult)
            assert create_result.row.name == "test-item"
            assert create_result.row.value == "test-value"
            assert create_result.row.id is not None

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


# =============================================================================
# Tests for server_default values (UUID, timestamp)
# =============================================================================


class CreatorTestRowWithDefaults(Base):  # type: ignore[misc]
    """ORM model with server_default columns for testing.

    This model uses server_default for:
    - id: UUID generated by database (uuid_generate_v4())
    - created_at: timestamp generated by database (now())
    """

    __tablename__ = "test_creator_with_defaults"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


class DefaultsCreatorSpec(CreatorSpec[CreatorTestRowWithDefaults]):
    """Creator spec for model with server_default columns."""

    def __init__(self, name: str) -> None:
        self._name = name

    def build_row(self) -> CreatorTestRowWithDefaults:
        return CreatorTestRowWithDefaults(name=self._name)


@pytest.fixture
async def create_tables_with_defaults(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create test tables with server_default columns."""
    async with with_tables(database_connection, [CreatorTestRowWithDefaults]):
        yield


class TestCreatorServerDefaults:
    """Tests for server_default value population after flush (without refresh)."""

    async def test_execute_creator_populates_server_defaults(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables_with_defaults: None,
    ) -> None:
        """Test that server_default values (UUID, timestamp) are populated after flush."""
        async with database_connection.begin_session() as db_sess:
            spec = DefaultsCreatorSpec(name="test-with-defaults")
            creator: Creator[CreatorTestRowWithDefaults] = Creator(spec=spec)

            result = await execute_creator(db_sess, creator)

            # Verify server_default values are populated
            assert result.row.id is not None, "UUID should be generated by server_default"
            assert isinstance(result.row.id, uuid.UUID), "ID should be a valid UUID"
            assert result.row.created_at is not None, (
                "created_at should be generated by server_default"
            )
            assert isinstance(result.row.created_at, datetime), "created_at should be a datetime"
            assert result.row.name == "test-with-defaults"

    async def test_execute_bulk_creator_populates_server_defaults(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables_with_defaults: None,
    ) -> None:
        """Test that server_default values are populated for all rows in bulk create."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                DefaultsCreatorSpec(name="bulk-item-0"),
                DefaultsCreatorSpec(name="bulk-item-1"),
                DefaultsCreatorSpec(name="bulk-item-2"),
            ]
            bulk_creator: BulkCreator[CreatorTestRowWithDefaults] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)

            assert len(result.rows) == 3

            # Verify all rows have server_default values populated
            for i, row in enumerate(result.rows):
                assert row.id is not None, f"Row {i}: UUID should be generated"
                assert isinstance(row.id, uuid.UUID), f"Row {i}: ID should be a valid UUID"
                assert row.created_at is not None, f"Row {i}: created_at should be generated"
                assert isinstance(row.created_at, datetime), (
                    f"Row {i}: created_at should be a datetime"
                )
                assert row.name == f"bulk-item-{i}"

            # Verify all UUIDs are unique
            ids = [row.id for row in result.rows]
            assert len(set(ids)) == 3, "All UUIDs should be unique"

    async def test_execute_bulk_creator_server_defaults_match_database(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables_with_defaults: None,
    ) -> None:
        """Test that server_default values match what's actually in the database."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                DefaultsCreatorSpec(name="verify-item-0"),
                DefaultsCreatorSpec(name="verify-item-1"),
            ]
            bulk_creator: BulkCreator[CreatorTestRowWithDefaults] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)
            created_ids = [row.id for row in result.rows]
            created_timestamps = [row.created_at for row in result.rows]

            # Re-query from database to verify values match
            query = (
                sa.select(CreatorTestRowWithDefaults)
                .where(CreatorTestRowWithDefaults.id.in_(created_ids))
                .order_by(CreatorTestRowWithDefaults.name)
            )
            db_result = await db_sess.execute(query)
            db_rows = db_result.scalars().all()

            assert len(db_rows) == 2

            # Verify IDs match
            db_ids = {row.id for row in db_rows}
            assert set(created_ids) == db_ids, "IDs from result should match database"

            # Verify timestamps match (within reasonable tolerance)
            for db_row in db_rows:
                idx = 0 if db_row.name == "verify-item-0" else 1
                assert db_row.created_at == created_timestamps[idx], (
                    "Timestamps should match database"
                )


# =============================================================================
# Tests for Python-side default values
# =============================================================================


class CreatorTestRowWithPythonDefaults(Base):  # type: ignore[misc]
    """ORM model with Python-side default columns for testing.

    This model uses Python default for:
    - id: UUID generated by Python (uuid.uuid4)
    - status: default string value
    - count: default integer value
    """

    __tablename__ = "test_creator_with_python_defaults"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="active")
    count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)


class PythonDefaultsCreatorSpec(CreatorSpec[CreatorTestRowWithPythonDefaults]):
    """Creator spec for model with Python-side default columns."""

    def __init__(self, name: str) -> None:
        self._name = name

    def build_row(self) -> CreatorTestRowWithPythonDefaults:
        return CreatorTestRowWithPythonDefaults(name=self._name)


@pytest.fixture
async def create_tables_with_python_defaults(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create test tables with Python-side default columns."""
    async with with_tables(database_connection, [CreatorTestRowWithPythonDefaults]):
        yield


class TestCreatorPythonDefaults:
    """Tests for Python-side default value population."""

    async def test_execute_creator_populates_python_defaults(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables_with_python_defaults: None,
    ) -> None:
        """Test that Python default values are populated."""
        async with database_connection.begin_session() as db_sess:
            spec = PythonDefaultsCreatorSpec(name="test-python-defaults")
            creator: Creator[CreatorTestRowWithPythonDefaults] = Creator(spec=spec)

            result = await execute_creator(db_sess, creator)

            # Verify Python default values are populated
            assert result.row.id is not None, "UUID should be generated by Python default"
            assert isinstance(result.row.id, uuid.UUID), "ID should be a valid UUID"
            assert result.row.status == "active", "status should have Python default"
            assert result.row.count == 0, "count should have Python default"
            assert result.row.name == "test-python-defaults"

    async def test_execute_bulk_creator_populates_python_defaults(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables_with_python_defaults: None,
    ) -> None:
        """Test that Python default values are populated for all rows in bulk create."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                PythonDefaultsCreatorSpec(name="bulk-python-0"),
                PythonDefaultsCreatorSpec(name="bulk-python-1"),
                PythonDefaultsCreatorSpec(name="bulk-python-2"),
            ]
            bulk_creator: BulkCreator[CreatorTestRowWithPythonDefaults] = BulkCreator(specs=specs)

            result = await execute_bulk_creator(db_sess, bulk_creator)

            assert len(result.rows) == 3

            # Verify all rows have Python default values
            for i, row in enumerate(result.rows):
                assert row.id is not None, f"Row {i}: UUID should be generated"
                assert isinstance(row.id, uuid.UUID), f"Row {i}: ID should be a valid UUID"
                assert row.status == "active", f"Row {i}: status should have default"
                assert row.count == 0, f"Row {i}: count should have default"
                assert row.name == f"bulk-python-{i}"

            # Verify all UUIDs are unique
            ids = [row.id for row in result.rows]
            assert len(set(ids)) == 3, "All UUIDs should be unique"


class TestBulkCreatorPartialFailure:
    """Tests for partial failure handling in bulk creator operations."""

    async def test_all_rows_succeed_with_partial_failure_support(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that all successful rows work correctly with new function."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(name="item-0", value="value-0"),
                SimpleCreatorSpec(name="item-1", value="value-1"),
                SimpleCreatorSpec(name="item-2", value="value-2"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator_partial(db_sess, bulk_creator)

            assert len(result.successes) == 3
            assert len(result.errors) == 0
            assert result.success_count() == 3
            assert not result.has_failures()

            # Verify order is preserved
            assert result.successes[0].name == "item-0"
            assert result.successes[1].name == "item-1"
            assert result.successes[2].name == "item-2"

    async def test_all_rows_fail(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that all failing specs are captured in errors."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                FailingCreatorSpec(should_fail=True, name="fail-0"),
                FailingCreatorSpec(should_fail=True, name="fail-1"),
                FailingCreatorSpec(should_fail=True, name="fail-2"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator_partial(db_sess, bulk_creator)

            assert len(result.successes) == 0
            assert len(result.errors) == 3
            assert result.success_count() == 0
            assert result.has_failures()

            # Verify error details
            for i, error in enumerate(result.errors):
                assert error.index == i
                assert error.spec == specs[i]
                assert isinstance(error.exception, ValueError)
                assert f"fail-{i}" in str(error.exception)

    async def test_partial_success_some_fail(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test mixed success and failure scenario."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(name="success-0", value="value-0"),
                FailingCreatorSpec(should_fail=True, name="fail-1"),
                SimpleCreatorSpec(name="success-2", value="value-2"),
                FailingCreatorSpec(should_fail=True, name="fail-3"),
                SimpleCreatorSpec(name="success-4", value="value-4"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator_partial(db_sess, bulk_creator)

            assert len(result.successes) == 3
            assert len(result.errors) == 2
            assert result.success_count() == 3
            assert result.has_failures()

            # Verify successes
            assert result.successes[0].name == "success-0"
            assert result.successes[1].name == "success-2"
            assert result.successes[2].name == "success-4"

            # Verify errors
            assert result.errors[0].index == 1
            assert result.errors[1].index == 3

    async def test_partial_success_preserves_database_state(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that successful rows are persisted even when some fail."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(name="persist-0", value="value-0"),
                FailingCreatorSpec(should_fail=True, name="fail-1"),
                SimpleCreatorSpec(name="persist-2", value="value-2"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator_partial(db_sess, bulk_creator)

            assert len(result.successes) == 2
            assert len(result.errors) == 1

            # Verify database state
            created_ids = [row.id for row in result.successes]
            query = (
                sa.select(CreatorTestRow)
                .where(CreatorTestRow.id.in_(created_ids))
                .order_by(CreatorTestRow.id)
            )
            db_result = await db_sess.execute(query)
            db_rows = db_result.scalars().all()

            assert len(db_rows) == 2
            assert db_rows[0].name == "persist-0"
            assert db_rows[1].name == "persist-2"

    async def test_empty_specs_with_partial_failure(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that empty specs return empty result."""
        async with database_connection.begin_session() as db_sess:
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=[])

            result = await execute_bulk_creator_partial(db_sess, bulk_creator)

            assert len(result.successes) == 0
            assert len(result.errors) == 0
            assert result.success_count() == 0
            assert not result.has_failures()

    async def test_error_includes_spec_and_exception(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that error information includes full context."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                FailingCreatorSpec(should_fail=True, name="error-test"),
            ]
            bulk_creator: BulkCreator[CreatorTestRow] = BulkCreator(specs=specs)

            result = await execute_bulk_creator_partial(db_sess, bulk_creator)

            assert len(result.errors) == 1
            error = result.errors[0]

            # Verify error structure
            assert error.spec is specs[0]
            assert error.index == 0
            assert isinstance(error.exception, ValueError)
            assert "error-test" in str(error.exception)


# =============================================================================
# Tests for integrity error handling in creator operations
# =============================================================================


class CreatorTestRowWithUnique(Base):  # type: ignore[misc]
    """ORM model with a unique constraint for integrity error testing."""

    __tablename__ = "test_creator_unique"
    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_test_creator_unique_name"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class _TestDuplicateNameError(BackendAIError, aiohttp.web.HTTPConflict):
    """Test domain error simulating a duplicate name conflict."""

    error_type = "https://api.backend.ai/probs/test-duplicate-name"
    error_title = "Duplicate name."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class UniqueCreatorSpec(CreatorSpec[CreatorTestRowWithUnique]):
    """Creator spec with integrity_error_checks for unique constraint."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=_TestDuplicateNameError(extra_msg="name already exists"),
                constraint_name="uq_test_creator_unique_name",
            ),
        )

    def build_row(self) -> CreatorTestRowWithUnique:
        return CreatorTestRowWithUnique(name=self._name)


class PlainUniqueCreatorSpec(CreatorSpec[CreatorTestRowWithUnique]):
    """Creator spec WITHOUT integrity_error_checks (uses default empty)."""

    def __init__(self, name: str) -> None:
        self._name = name

    def build_row(self) -> CreatorTestRowWithUnique:
        return CreatorTestRowWithUnique(name=self._name)


class NonMatchingUniqueCreatorSpec(CreatorSpec[CreatorTestRowWithUnique]):
    """Creator spec with integrity_error_checks that won't match."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=_TestDuplicateNameError(extra_msg="wrong constraint"),
                constraint_name="uq_nonexistent_constraint",
            ),
        )

    def build_row(self) -> CreatorTestRowWithUnique:
        return CreatorTestRowWithUnique(name=self._name)


@pytest.fixture
async def create_unique_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create test tables with unique constraint."""
    async with with_tables(database_connection, [CreatorTestRowWithUnique]):
        yield


class TestCreatorIntegrityErrorHandling:
    """Tests for integrity error handling in execute_creator."""

    async def test_matching_check_raises_domain_error(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """IntegrityError with matching check raises domain error."""
        async with database_connection.begin_session() as db_sess:
            # Insert first row
            spec1 = UniqueCreatorSpec(name="duplicate")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session(commit_on_end=False) as db_sess:
            # Insert duplicate → should raise domain error
            spec2 = UniqueCreatorSpec(name="duplicate")
            with pytest.raises(_TestDuplicateNameError, match="name already exists"):
                await execute_creator(db_sess, Creator(spec=spec2))

    async def test_empty_checks_raises_repository_integrity_error(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """IntegrityError with no checks (empty default) raises RepositoryIntegrityError."""
        async with database_connection.begin_session() as db_sess:
            spec1 = PlainUniqueCreatorSpec(name="duplicate")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session(commit_on_end=False) as db_sess:
            spec2 = PlainUniqueCreatorSpec(name="duplicate")
            with pytest.raises(RepositoryIntegrityError):
                await execute_creator(db_sess, Creator(spec=spec2))

    async def test_non_matching_check_raises_repository_integrity_error(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """IntegrityError with non-matching check raises RepositoryIntegrityError."""
        async with database_connection.begin_session() as db_sess:
            spec1 = NonMatchingUniqueCreatorSpec(name="duplicate")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session(commit_on_end=False) as db_sess:
            spec2 = NonMatchingUniqueCreatorSpec(name="duplicate")
            with pytest.raises(UniqueConstraintViolationError):
                await execute_creator(db_sess, Creator(spec=spec2))


class TestBulkCreatorIntegrityErrorHandling:
    """Tests for integrity error handling in execute_bulk_creator."""

    async def test_matching_check_raises_domain_error(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """IntegrityError with matching check raises domain error (all-or-nothing)."""
        async with database_connection.begin_session() as db_sess:
            spec1 = UniqueCreatorSpec(name="existing")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session(commit_on_end=False) as db_sess:
            specs = [
                UniqueCreatorSpec(name="new-item"),
                UniqueCreatorSpec(name="existing"),  # duplicate
            ]
            with pytest.raises(_TestDuplicateNameError, match="name already exists"):
                await execute_bulk_creator(db_sess, BulkCreator(specs=specs))

    async def test_empty_checks_raises_repository_integrity_error(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """IntegrityError with empty checks raises RepositoryIntegrityError."""
        async with database_connection.begin_session() as db_sess:
            spec1 = PlainUniqueCreatorSpec(name="existing")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session(commit_on_end=False) as db_sess:
            specs = [
                PlainUniqueCreatorSpec(name="existing"),  # duplicate
            ]
            with pytest.raises(RepositoryIntegrityError):
                await execute_bulk_creator(db_sess, BulkCreator(specs=specs))


class TestBulkCreatorPartialIntegrityErrorHandling:
    """Tests for integrity error handling in execute_bulk_creator_partial."""

    async def test_matching_check_stores_domain_error(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """IntegrityError with matching check stores domain error in BulkCreatorError."""
        async with database_connection.begin_session() as db_sess:
            spec1 = UniqueCreatorSpec(name="existing")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session() as db_sess:
            specs = [
                UniqueCreatorSpec(name="new-item"),
                UniqueCreatorSpec(name="existing"),  # duplicate
            ]
            result = await execute_bulk_creator_partial(db_sess, BulkCreator(specs=specs))

            assert len(result.successes) == 1
            assert result.successes[0].name == "new-item"
            assert len(result.errors) == 1
            assert isinstance(result.errors[0].exception, _TestDuplicateNameError)
            assert result.errors[0].index == 1

    async def test_empty_checks_stores_repository_integrity_error(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """IntegrityError with no checks stores RepositoryIntegrityError."""
        async with database_connection.begin_session() as db_sess:
            spec1 = PlainUniqueCreatorSpec(name="existing")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session() as db_sess:
            specs = [
                PlainUniqueCreatorSpec(name="existing"),  # duplicate
            ]
            result = await execute_bulk_creator_partial(db_sess, BulkCreator(specs=specs))

            assert len(result.successes) == 0
            assert len(result.errors) == 1
            assert isinstance(result.errors[0].exception, RepositoryIntegrityError)
            assert not isinstance(result.errors[0].exception, _TestDuplicateNameError)

    async def test_mixed_successes_and_integrity_errors(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """Mix of integrity errors and successes produces correct results."""
        async with database_connection.begin_session() as db_sess:
            spec1 = UniqueCreatorSpec(name="existing-1")
            await execute_creator(db_sess, Creator(spec=spec1))
            spec2 = UniqueCreatorSpec(name="existing-2")
            await execute_creator(db_sess, Creator(spec=spec2))

        async with database_connection.begin_session() as db_sess:
            specs = [
                UniqueCreatorSpec(name="new-a"),
                UniqueCreatorSpec(name="existing-1"),  # duplicate
                UniqueCreatorSpec(name="new-b"),
                UniqueCreatorSpec(name="existing-2"),  # duplicate
                UniqueCreatorSpec(name="new-c"),
            ]
            result = await execute_bulk_creator_partial(db_sess, BulkCreator(specs=specs))

            assert len(result.successes) == 3
            assert result.successes[0].name == "new-a"
            assert result.successes[1].name == "new-b"
            assert result.successes[2].name == "new-c"

            assert len(result.errors) == 2
            assert result.errors[0].index == 1
            assert result.errors[1].index == 3
            assert isinstance(result.errors[0].exception, _TestDuplicateNameError)
            assert isinstance(result.errors[1].exception, _TestDuplicateNameError)

    async def test_raw_integrity_error_never_leaks(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_unique_tables: None,
    ) -> None:
        """Raw sa.exc.IntegrityError never appears in BulkCreatorError.exception."""
        async with database_connection.begin_session() as db_sess:
            spec1 = PlainUniqueCreatorSpec(name="existing")
            await execute_creator(db_sess, Creator(spec=spec1))

        async with database_connection.begin_session() as db_sess:
            specs = [
                PlainUniqueCreatorSpec(name="existing"),  # duplicate, no checks
            ]
            result = await execute_bulk_creator_partial(db_sess, BulkCreator(specs=specs))

            assert len(result.errors) == 1
            # Must be a RepositoryIntegrityError, never raw sa.exc.IntegrityError
            assert isinstance(result.errors[0].exception, RepositoryIntegrityError)
