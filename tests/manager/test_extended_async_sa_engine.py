from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.orm import declarative_base

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass(frozen=True)
class IsolationTestRowData:
    """
    Represents a test data row from the test_isolation_data table.
    """

    value: str
    version: int


Base = declarative_base()


class IsolationDataModel(Base):  # type: ignore
    """ORM model for test_isolation_data table."""

    __tablename__ = "test_isolation_data"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    value = sa.Column(sa.String(255), nullable=False)
    version = sa.Column(sa.Integer, nullable=False, default=1)

    def __init__(self, value: str, version: int = 1) -> None:
        self.value = value
        self.version = version


class TestExtendedAsyncSAEngineReadCommitted:
    """
    Test suite for ExtendedAsyncSAEngine's READ COMMITTED isolation level methods.

    This test class verifies the behavior of:
    - begin_read_committed: Read-write connection with READ COMMITTED isolation
    - begin_readonly_read_committed: Read-only connection with READ COMMITTED isolation
    - begin_session_read_committed: Read-write session with READ COMMITTED isolation
    - begin_readonly_session_read_committed: Read-only session with READ COMMITTED isolation
    """

    @pytest.fixture
    def test_table_metadata(self) -> sa.MetaData:
        """Create test table metadata for isolation level testing."""
        return IsolationDataModel.metadata

    @pytest.fixture
    def orm_model(self) -> type[IsolationDataModel]:
        """Provide ORM model class for session-based tests."""
        return IsolationDataModel

    @pytest.fixture(autouse=True)
    async def test_table_in_db(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_metadata: sa.MetaData,
    ) -> AsyncIterator[sa.Table]:
        """Create test table in database and clean up after test."""
        async with database_engine.begin() as conn:
            await conn.run_sync(test_table_metadata.create_all)

        table = test_table_metadata.tables["test_isolation_data"]
        yield table

        async with database_engine.begin() as conn:
            await conn.run_sync(test_table_metadata.drop_all)

    async def _insert_test_data_returning_id(
        self,
        conn: AsyncConnection,
        test_table: sa.Table,
        value: str,
        version: int = 1,
    ) -> int:
        result = await conn.execute(
            sa.insert(test_table).values(value=value, version=version).returning(test_table.c.id)
        )
        row = result.fetchone()
        assert row is not None
        return row[0]

    async def _get_row_data_by_id(
        self,
        conn: AsyncConnection,
        test_table: sa.Table,
        row_id: int,
    ) -> IsolationTestRowData | None:
        result = await conn.execute(
            sa.select(test_table.c.value, test_table.c.version).where(test_table.c.id == row_id)
        )
        row = result.fetchone()
        if row is None:
            return None
        return IsolationTestRowData(value=row[0], version=row[1])

    @pytest.mark.asyncio
    async def test_begin_read_committed_basic(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """Test basic functionality of begin_read_committed."""
        test_value = "test_value"
        expected_version = 1

        # Insert and read data using READ COMMITTED connection
        async with database_engine.begin_read_committed() as conn:
            row_id = await self._insert_test_data_returning_id(conn, test_table_in_db, test_value)
            data = await self._get_row_data_by_id(conn, test_table_in_db, row_id)

        assert data is not None
        assert data.value == test_value
        assert data.version == expected_version

    @pytest.mark.asyncio
    async def test_begin_read_committed_isolation_level(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Verify that the connection uses READ COMMITTED isolation level."""
        expected_isolation_level = "read committed"

        async with database_engine.begin_read_committed() as conn:
            # Query the current isolation level from PostgreSQL
            result = await conn.execute(sa.text("SHOW transaction_isolation;"))
            isolation_level = result.scalar()

        assert isolation_level == expected_isolation_level

    @pytest.mark.asyncio
    async def test_begin_read_committed_can_write(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """Verify that read-write connection can perform writes."""
        test_value = "write_test"
        expected_version = 1

        # Insert data using READ COMMITTED connection
        async with database_engine.begin_read_committed() as conn:
            row_id = await self._insert_test_data_returning_id(conn, test_table_in_db, test_value)

        # Verify data was committed
        async with database_engine.begin() as conn:
            data = await self._get_row_data_by_id(conn, test_table_in_db, row_id)

        assert data is not None
        assert data.value == test_value
        assert data.version == expected_version

    @pytest.mark.asyncio
    async def test_begin_readonly_read_committed_basic(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """Test basic functionality of begin_readonly_read_committed."""
        test_value = "test_value"
        expected_version = 1

        # First insert some data using regular connection
        async with database_engine.begin() as conn:
            row_id = await self._insert_test_data_returning_id(conn, test_table_in_db, test_value)

        # Now read using READ COMMITTED read-only connection
        async with database_engine.begin_readonly_read_committed() as conn:
            data = await self._get_row_data_by_id(conn, test_table_in_db, row_id)

        assert data is not None
        assert data.value == test_value
        assert data.version == expected_version

    @pytest.mark.asyncio
    async def test_begin_readonly_read_committed_isolation_level(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Verify that the connection uses READ COMMITTED isolation level."""
        expected_isolation_level = "read committed"

        async with database_engine.begin_readonly_read_committed() as conn:
            # Query the current isolation level from PostgreSQL
            result = await conn.execute(sa.text("SHOW transaction_isolation;"))
            isolation_level = result.scalar()

        assert isolation_level == expected_isolation_level

    @pytest.mark.asyncio
    async def test_begin_readonly_read_committed_cannot_write(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """Verify that read-only connection cannot perform writes."""
        test_value = "should_fail"

        with pytest.raises(sa.exc.DBAPIError) as exc_info:
            async with database_engine.begin_readonly_read_committed() as conn:
                await conn.execute(sa.insert(test_table_in_db).values(value=test_value, version=1))

        # PostgreSQL raises "cannot execute INSERT in a read-only transaction"
        assert "read-only" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_begin_session_read_committed_basic(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
        orm_model: type[IsolationDataModel],
    ) -> None:
        """Test basic functionality of begin_session_read_committed using ORM."""
        session_value_1 = "session_value_1"
        session_value_2 = "session_value_2"
        row_ids: list[int] = []

        # Insert data using READ COMMITTED session with ORM
        async with database_engine.begin_session_read_committed() as session:
            model1 = orm_model(value=session_value_1, version=1)
            model2 = orm_model(value=session_value_2, version=1)

            session.add(model1)
            session.add(model2)
            await session.flush()

            row_ids.append(model1.id)
            row_ids.append(model2.id)

            # Verify data within session using ORM query
            result = await session.execute(sa.select(orm_model).where(orm_model.id.in_(row_ids)))
            objs = result.scalars().all()
            values = [obj.value for obj in objs]

        # Session should auto-commit
        assert session_value_1 in values
        assert session_value_2 in values

    @pytest.mark.asyncio
    async def test_begin_session_read_committed_isolation_level(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Verify that the session uses READ COMMITTED isolation level."""
        expected_isolation_level = "read committed"

        async with database_engine.begin_session_read_committed() as session:
            # Query the current isolation level
            result = await session.execute(sa.text("SHOW transaction_isolation;"))
            isolation_level = result.scalar()

        assert isolation_level == expected_isolation_level

    @pytest.mark.asyncio
    async def test_begin_session_read_committed_auto_commit(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
        orm_model: type[IsolationDataModel],
    ) -> None:
        """Verify that session auto-commits on exit using ORM."""
        test_value = "auto_commit_test"

        # Insert in session using ORM
        async with database_engine.begin_session_read_committed() as session:
            model = orm_model(value=test_value, version=1)
            session.add(model)
            await session.flush()
            row_id = model.id

        # Verify data persisted after session exit
        async with database_engine.begin_readonly() as conn:
            data = await self._get_row_data_by_id(conn, test_table_in_db, row_id)

        assert data is not None
        assert data.value == test_value

    @pytest.mark.asyncio
    async def test_begin_readonly_session_read_committed_basic(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
        orm_model: type[IsolationDataModel],
    ) -> None:
        """Test basic functionality of begin_readonly_session_read_committed using ORM."""
        test_value = "readonly_session_test"
        expected_version = 1

        # Insert test data
        async with database_engine.begin() as conn:
            row_id = await self._insert_test_data_returning_id(conn, test_table_in_db, test_value)

        # Read using READ COMMITTED read-only session with ORM
        async with database_engine.begin_readonly_session_read_committed() as session:
            result = await session.execute(sa.select(orm_model).where(orm_model.id == row_id))
            model = result.scalar_one_or_none()

        assert model is not None
        assert model.value == test_value
        assert model.version == expected_version

    @pytest.mark.asyncio
    async def test_begin_readonly_session_read_committed_isolation_level(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Verify that the read-only session uses READ COMMITTED isolation level."""
        expected_isolation_level = "read committed"

        async with database_engine.begin_readonly_session_read_committed() as session:
            # Query the current isolation level
            result = await session.execute(sa.text("SHOW transaction_isolation;"))
            isolation_level = result.scalar()

        assert isolation_level == expected_isolation_level

    @pytest.mark.asyncio
    async def test_begin_readonly_session_read_committed_cannot_write(
        self,
        database_engine: ExtendedAsyncSAEngine,
        orm_model: type[IsolationDataModel],
    ) -> None:
        """Verify that read-only session cannot perform writes using ORM."""
        test_value = "should_fail"

        with pytest.raises(sa.exc.DBAPIError) as exc_info:
            async with database_engine.begin_readonly_session_read_committed() as session:
                model = orm_model(value=test_value, version=1)
                session.add(model)
                await session.flush()

        # PostgreSQL raises "cannot execute INSERT in a read-only transaction"
        assert "read-only" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_read_committed_sees_committed_changes(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """
        Verify READ COMMITTED isolation allows seeing committed changes from other transactions.

        This is a key characteristic of READ COMMITTED isolation level.
        """
        initial_value = "initial_value"
        updated_value = "updated_value"
        initial_version = 1
        updated_version = 2

        # Insert initial data using READ COMMITTED connection
        async with database_engine.begin_read_committed() as conn:
            row_id = await self._insert_test_data_returning_id(
                conn, test_table_in_db, initial_value
            )

        # Start a READ COMMITTED read-only connection
        async with database_engine.begin_readonly_read_committed() as read_conn:
            # Read initial value
            data = await self._get_row_data_by_id(read_conn, test_table_in_db, row_id)
            assert data is not None
            assert data.value == initial_value
            assert data.version == initial_version

            # Update value in a separate READ COMMITTED transaction
            async with database_engine.begin_read_committed() as write_conn:
                await write_conn.execute(
                    sa.update(test_table_in_db)
                    .where(test_table_in_db.c.id == row_id)
                    .values(value=updated_value, version=updated_version)
                )

            # READ COMMITTED should see the committed change
            data_after = await self._get_row_data_by_id(read_conn, test_table_in_db, row_id)
            assert data_after is not None
            assert data_after.value == updated_value
            assert data_after.version == updated_version

    @pytest.mark.asyncio
    async def test_multiple_concurrent_readonly_read_committed_connections(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """Test multiple concurrent READ COMMITTED read-only connections."""
        test_value = "concurrent_test"

        # Insert test data using READ COMMITTED connection
        async with database_engine.begin_read_committed() as conn:
            row_id = await self._insert_test_data_returning_id(conn, test_table_in_db, test_value)

        # Open multiple READ COMMITTED connections concurrently
        async with (
            database_engine.begin_readonly_read_committed() as conn1,
            database_engine.begin_readonly_read_committed() as conn2,
            database_engine.begin_readonly_read_committed() as conn3,
        ):
            # All should be able to read the same data
            data1 = await self._get_row_data_by_id(conn1, test_table_in_db, row_id)
            data2 = await self._get_row_data_by_id(conn2, test_table_in_db, row_id)
            data3 = await self._get_row_data_by_id(conn3, test_table_in_db, row_id)

        assert data1 == data2 == data3
        assert data1 is not None
        assert data1.value == test_value

    @pytest.mark.asyncio
    async def test_read_committed_prevents_dirty_reads(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """
        Dirty reads occur when a transaction reads uncommitted changes from another transaction.
        READ COMMITTED must NOT allow this.
        """
        initial_value = "committed_value"
        uncommitted_value = "uncommitted_value"
        initial_version = 1
        uncommitted_version = 2

        # Insert initial data using READ COMMITTED connection
        async with database_engine.begin_read_committed() as conn:
            row_id = await self._insert_test_data_returning_id(
                conn, test_table_in_db, initial_value
            )

        # Start a write transaction but don't commit it yet
        async with database_engine.begin() as write_conn:
            # Update value but don't commit
            await write_conn.execute(
                sa.update(test_table_in_db)
                .where(test_table_in_db.c.id == row_id)
                .values(value=uncommitted_value, version=uncommitted_version)
            )

            # Start a READ COMMITTED read-only connection while write transaction is still open
            async with database_engine.begin_readonly_read_committed() as read_conn:
                # Should NOT see uncommitted changes (dirty read)
                data = await self._get_row_data_by_id(read_conn, test_table_in_db, row_id)
                assert data is not None
                assert data.value == initial_value
                assert data.version == initial_version

                # Verify we're NOT seeing the uncommitted changes
                assert data.value != uncommitted_value
                assert data.version != uncommitted_version

            # Rollback the write transaction
            await write_conn.rollback()

        # Verify final state is still the initial value
        async with database_engine.begin_readonly_read_committed() as final_conn:
            final_data = await self._get_row_data_by_id(final_conn, test_table_in_db, row_id)
            assert final_data is not None
            assert final_data.value == initial_value
            assert final_data.version == initial_version

    @pytest.mark.asyncio
    async def test_read_committed_allows_phantom_reads(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """
        Verify READ COMMITTED isolation allows phantom reads.
        """
        category = "test_category"
        value1 = "existing_row_test_category"
        value2 = "phantom_row_test_category"

        # Insert initial data using READ COMMITTED connection
        async with database_engine.begin_read_committed() as conn:
            await self._insert_test_data_returning_id(conn, test_table_in_db, value1)

        # Start a READ COMMITTED read-only connection
        async with database_engine.begin_readonly_read_committed() as read_conn:
            # First query: count rows with specific category
            initial_result = await read_conn.execute(
                sa.select(sa.func.count())
                .select_from(test_table_in_db)
                .where(test_table_in_db.c.value.like(f"%{category}%"))
            )
            initial_count = initial_result.scalar()
            assert initial_count == 1  # Only one row initially

            # Get initial row IDs
            initial_rows = await read_conn.execute(
                sa.select(test_table_in_db.c.id).where(
                    test_table_in_db.c.value.like(f"%{category}%")
                )
            )
            initial_ids = {row.id for row in initial_rows}

            # Another transaction inserts a new row and commits using READ COMMITTED
            async with database_engine.begin_read_committed() as write_conn:
                await self._insert_test_data_returning_id(write_conn, test_table_in_db, value2)

            # Second query in same READ COMMITTED transaction
            # Should see the newly inserted row (phantom read)
            final_result = await read_conn.execute(
                sa.select(sa.func.count())
                .select_from(test_table_in_db)
                .where(test_table_in_db.c.value.like(f"%{category}%"))
            )
            final_count = final_result.scalar()

            final_rows = await read_conn.execute(
                sa.select(test_table_in_db.c.id).where(
                    test_table_in_db.c.value.like(f"%{category}%")
                )
            )
            final_ids = {row.id for row in final_rows}

            # Phantom read verification: count should increase
            assert final_count == initial_count + 1
            assert final_count == 2

            # New rows appeared (phantom rows)
            phantom_ids = final_ids - initial_ids
            assert len(phantom_ids) == 1

    @pytest.mark.asyncio
    async def test_read_committed_phantom_read_with_range_query(
        self,
        database_engine: ExtendedAsyncSAEngine,
        test_table_in_db: sa.Table,
    ) -> None:
        """
        Verify READ COMMITTED allows phantom reads with range queries.

        This test specifically checks phantom reads with a range condition,
        which is a common scenario where phantom reads occur.
        """
        # Insert initial data with versions 1-3 using READ COMMITTED connection
        async with database_engine.begin_read_committed() as conn:
            for version in range(1, 4):
                await self._insert_test_data_returning_id(
                    conn, test_table_in_db, f"value_{version}", version
                )

        # Start a READ COMMITTED transaction
        async with database_engine.begin_readonly_read_committed() as read_conn:
            # First range query: get rows with version >= 1 and <= 3
            initial_result = await read_conn.execute(
                sa.select(test_table_in_db.c.id, test_table_in_db.c.version)
                .where(test_table_in_db.c.version.between(1, 5))
                .order_by(test_table_in_db.c.version)
            )
            initial_rows = list(initial_result)
            initial_versions = [row.version for row in initial_rows]
            assert len(initial_rows) == 3
            assert initial_versions == [1, 2, 3]

            # Another transaction inserts rows with versions 4 and 5 using READ COMMITTED
            async with database_engine.begin_read_committed() as write_conn:
                for version in [4, 5]:
                    await write_conn.execute(
                        sa.insert(test_table_in_db).values(
                            value=f"value_{version}", version=version
                        )
                    )

            # Same range query again - should see phantom rows
            final_result = await read_conn.execute(
                sa.select(test_table_in_db.c.id, test_table_in_db.c.version)
                .where(test_table_in_db.c.version.between(1, 5))
                .order_by(test_table_in_db.c.version)
            )
            final_rows = list(final_result)
            final_versions = [row.version for row in final_rows]

            # Phantom reads: new rows appear in range
            assert len(final_rows) == 5
            assert final_versions == [1, 2, 3, 4, 5]

            # Verify phantom count
            phantom_count = len(final_rows) - len(initial_rows)
            assert phantom_count == 2
