"""
Tests for ObjectStorageRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.errors.object_storage import ObjectStorageNotFoundError
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.testutils.db import with_tables


class TestObjectStorageRepository:
    """Test cases for ObjectStorageRepository"""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                ObjectStorageRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_storage_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample Object storage directly in DB and return its ID"""
        storage_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            object_storage = ObjectStorageRow(
                id=storage_id,
                name="test-object-storage",
                host="storage-proxy-1",
                access_key="test-access-key",
                secret_key="test-secret-key",
                endpoint="https://s3.example.com",
                region="us-east-1",
            )
            db_sess.add(object_storage)
            await db_sess.flush()

        yield storage_id

    @pytest.fixture
    async def sample_storages_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample Object storages with predictable names for ordering tests"""
        storage_ids = []
        names = ["alpha-storage", "beta-storage", "gamma-storage", "delta-storage"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                storage_id = uuid.uuid4()

                object_storage = ObjectStorageRow(
                    id=storage_id,
                    name=name,
                    host="storage-proxy-1",
                    access_key="test-access-key",
                    secret_key="test-secret-key",
                    endpoint=f"https://s3.example.com/{name}",
                    region="us-east-1",
                )
                db_sess.add(object_storage)
                storage_ids.append(storage_id)
            await db_sess.flush()

        yield storage_ids

    @pytest.fixture
    async def sample_storages_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 sample Object storages for pagination testing"""
        storage_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                storage_id = uuid.uuid4()

                object_storage = ObjectStorageRow(
                    id=storage_id,
                    name=f"object-storage-{i:02d}",
                    host="storage-proxy-1",
                    access_key="test-access-key",
                    secret_key="test-secret-key",
                    endpoint=f"https://s3.example.com/storage-{i:02d}",
                    region="us-east-1",
                )
                db_sess.add(object_storage)
                storage_ids.append(storage_id)
            await db_sess.flush()

        yield storage_ids

    @pytest.fixture
    async def object_storage_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ObjectStorageRepository, None]:
        """Create ObjectStorageRepository instance with database"""
        repo = ObjectStorageRepository(db=db_with_cleanup)
        yield repo

    # =========================================================================
    # Tests - Get by ID
    # =========================================================================

    async def test_get_by_id(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storage_id: uuid.UUID,
    ) -> None:
        """Test retrieving Object storage by ID"""
        retrieved_storage = await object_storage_repository.get_by_id(sample_storage_id)

        assert retrieved_storage is not None
        assert retrieved_storage.id == sample_storage_id
        assert retrieved_storage.name == "test-object-storage"
        assert retrieved_storage.endpoint == "https://s3.example.com"

    async def test_get_by_id_not_found(
        self,
        object_storage_repository: ObjectStorageRepository,
    ) -> None:
        """Test retrieving non-existent Object storage raises error"""
        with pytest.raises(ObjectStorageNotFoundError):
            await object_storage_repository.get_by_id(uuid.uuid4())

    # =========================================================================
    # Tests - Get by Name
    # =========================================================================

    async def test_get_by_name(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storage_id: uuid.UUID,
    ) -> None:
        """Test retrieving Object storage by name"""
        retrieved_storage = await object_storage_repository.get_by_name("test-object-storage")

        assert retrieved_storage is not None
        assert retrieved_storage.id == sample_storage_id
        assert retrieved_storage.name == "test-object-storage"

    async def test_get_by_name_not_found(
        self,
        object_storage_repository: ObjectStorageRepository,
    ) -> None:
        """Test retrieving non-existent Object storage by name raises error"""
        with pytest.raises(ObjectStorageNotFoundError):
            await object_storage_repository.get_by_name("non-existent-storage")

    # =========================================================================
    # Tests - List
    # =========================================================================

    async def test_list_object_storages(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test listing all Object storages"""
        storages = await object_storage_repository.list_object_storages()

        assert len(storages) == 4
        storage_ids = [s.id for s in storages]
        for expected_id in sample_storages_for_ordering:
            assert expected_id in storage_ids

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_offset_pagination_first_page(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ObjectStorageRow.name.like("object-storage-%"),
            ],
            orders=[],
        )

        result = await object_storage_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_offset_pagination_second_page(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ObjectStorageRow.name.like("object-storage-%"),
            ],
            orders=[],
        )

        result = await object_storage_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_offset_pagination_last_page(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ObjectStorageRow.name.like("object-storage-%"),
            ],
            orders=[],
        )

        result = await object_storage_repository.search(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_order_by_name_ascending(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching Object storages ordered by name ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ObjectStorageRow.name.in_([
                    "alpha-storage",
                    "beta-storage",
                    "gamma-storage",
                    "delta-storage",
                ]),
            ],
            orders=[ObjectStorageRow.name.asc()],
        )

        result = await object_storage_repository.search(querier=querier)

        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names)

    async def test_search_order_by_name_descending(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching Object storages ordered by name descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ObjectStorageRow.name.in_([
                    "alpha-storage",
                    "beta-storage",
                    "gamma-storage",
                    "delta-storage",
                ]),
            ],
            orders=[ObjectStorageRow.name.desc()],
        )

        result = await object_storage_repository.search(querier=querier)

        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names, reverse=True)

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_with_pagination_filter_and_order(
        self,
        object_storage_repository: ObjectStorageRepository,
        sample_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching Object storages with pagination, filter, and ordering combined"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=5),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ObjectStorageRow.name.like("object-storage-%"),
            ],
            orders=[ObjectStorageRow.name.asc()],
        )

        result = await object_storage_repository.search(querier=querier)

        # Total matching storages: 25, so total_count should be 25
        assert result.total_count == 25
        # With limit=5, offset=5, we get 5 items
        assert len(result.items) == 5

        # Verify ordering is ascending
        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names)
