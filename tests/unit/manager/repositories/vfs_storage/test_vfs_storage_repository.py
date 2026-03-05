"""
Tests for VFSStorageRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.errors.vfs_storage import VFSStorageNotFoundError
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.vfs_storage.creators import VFSStorageCreatorSpec
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.repositories.vfs_storage.updaters import VFSStorageUpdaterSpec
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


class TestVFSStorageRepository:
    """Test cases for VFSStorageRepository"""

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
            [ArtifactStorageRow, VFSStorageRow],
        ):
            yield database_connection

    @pytest.fixture
    def vfs_storage_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VFSStorageRepository:
        """Create a VFSStorageRepository instance"""
        return VFSStorageRepository(db_with_cleanup)

    @pytest.fixture
    async def sample_vfs_storage_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample VFS storage directly in DB and return its ID"""
        storage_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            storage = VFSStorageRow(
                id=storage_id,
                name="test-vfs-storage",
                host="localhost",
                base_path="/mnt/vfs/test",
            )
            db_sess.add(storage)
            await db_sess.flush()

        yield storage_id

    @pytest.fixture
    def vfs_storage_creator_spec(self) -> VFSStorageCreatorSpec:
        """Spec for creating a new VFS storage"""
        return VFSStorageCreatorSpec(
            name="new-vfs-storage",
            host="storage-host-1",
            base_path="/mnt/nfs/new",
        )

    @pytest.fixture
    def vfs_storage_updater_spec(self) -> VFSStorageUpdaterSpec:
        """Spec for updating VFS storage fields"""
        return VFSStorageUpdaterSpec(
            host=OptionalState.update("updated-host"),
            base_path=OptionalState.update("/mnt/vfs/updated"),
        )

    @pytest.fixture
    async def sample_vfs_storages_for_filtering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create sample VFS storages with different hosts for filter testing"""
        storage_map: dict[str, uuid.UUID] = {}
        hosts = ["host-a", "host-b"]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, host in enumerate(hosts):
                storage_id = uuid.uuid4()
                storage = VFSStorageRow(
                    id=storage_id,
                    name=f"filter-test-storage-{host}-{i}",
                    host=host,
                    base_path=f"/mnt/vfs/{host}",
                )
                db_sess.add(storage)
                storage_map[host] = storage_id
            await db_sess.flush()

        yield storage_map

    @pytest.fixture
    async def sample_vfs_storages_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample VFS storages with predictable names for ordering tests"""
        storage_ids = []
        names = ["alpha-storage", "beta-storage", "gamma-storage", "delta-storage"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                storage_id = uuid.uuid4()
                storage = VFSStorageRow(
                    id=storage_id,
                    name=name,
                    host="localhost",
                    base_path=f"/mnt/vfs/{name}",
                )
                db_sess.add(storage)
                storage_ids.append(storage_id)
            await db_sess.flush()

        yield storage_ids

    @pytest.fixture
    async def sample_vfs_storages_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 VFS storages for pagination testing"""
        storage_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                storage_id = uuid.uuid4()
                storage = VFSStorageRow(
                    id=storage_id,
                    name=f"pagination-test-storage-{i:02d}",
                    host="localhost",
                    base_path=f"/mnt/vfs/pagination/{i:02d}",
                )
                db_sess.add(storage)
                storage_ids.append(storage_id)
            await db_sess.flush()

        yield storage_ids

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_vfs_storages_filter_by_host(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_filtering: dict[str, uuid.UUID],
    ) -> None:
        """Test searching VFS storages filtered by host returns only matching storages"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: VFSStorageRow.host == "host-a",
            ],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        result_storage_ids = [storage.id for storage in result.items]
        assert sample_vfs_storages_for_filtering["host-a"] in result_storage_ids
        assert sample_vfs_storages_for_filtering["host-b"] not in result_storage_ids

    async def test_search_vfs_storages_filter_by_name_pattern(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages with name pattern filter"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: VFSStorageRow.name.like("alpha%"),
            ],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 1
        assert result.items[0].name == "alpha-storage"

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_vfs_storages_order_by_name_ascending(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages ordered by name ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[VFSStorageRow.name.asc()],
        )

        result = await vfs_storage_repository.search(querier=querier)

        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names)
        assert result_names[0] == "alpha-storage"
        assert result_names[-1] == "gamma-storage"

    async def test_search_vfs_storages_order_by_name_descending(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages ordered by name descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[VFSStorageRow.name.desc()],
        )

        result = await vfs_storage_repository.search(querier=querier)

        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names, reverse=True)
        assert result_names[0] == "gamma-storage"
        assert result_names[-1] == "alpha-storage"

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_vfs_storages_offset_pagination_first_page(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_vfs_storages_offset_pagination_second_page(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_vfs_storages_offset_pagination_last_page(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await vfs_storage_repository.search(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_vfs_storages_with_pagination_filter_and_order(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storages_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching VFS storages with pagination, filter condition, and ordering combined"""
        # Filter: only storages with localhost host
        # Order: by name ascending
        # Pagination: limit 5, offset 2
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=2),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: VFSStorageRow.host == "localhost",
            ],
            orders=[VFSStorageRow.name.asc()],
        )

        result = await vfs_storage_repository.search(querier=querier)

        # Total localhost storages: 25, so total_count should be 25
        assert result.total_count == 25
        # With limit=5, offset=2, we get items at indices 2, 3, 4, 5, 6 of sorted results
        assert len(result.items) == 5

        # Verify ordering is ascending
        result_names = [storage.name for storage in result.items]
        assert result_names == sorted(result_names)

    # =========================================================================
    # Tests - Get by ID
    # =========================================================================

    async def test_get_by_id(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storage_id: uuid.UUID,
    ) -> None:
        """Test retrieving VFS storage by ID"""
        result = await vfs_storage_repository.get_by_id(sample_vfs_storage_id)

        assert result.id == sample_vfs_storage_id
        assert result.name == "test-vfs-storage"
        assert result.host == "localhost"
        assert str(result.base_path) == "/mnt/vfs/test"

    async def test_get_by_id_not_found(
        self,
        vfs_storage_repository: VFSStorageRepository,
    ) -> None:
        """Test retrieving non-existent VFS storage raises error"""
        with pytest.raises(VFSStorageNotFoundError):
            await vfs_storage_repository.get_by_id(uuid.uuid4())

    # =========================================================================
    # Tests - Get by Name
    # =========================================================================

    async def test_get_by_name(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storage_id: uuid.UUID,
    ) -> None:
        """Test retrieving VFS storage by name"""
        result = await vfs_storage_repository.get_by_name("test-vfs-storage")

        assert result.id == sample_vfs_storage_id
        assert result.name == "test-vfs-storage"

    async def test_get_by_name_not_found(
        self,
        vfs_storage_repository: VFSStorageRepository,
    ) -> None:
        """Test retrieving non-existent VFS storage by name raises error"""
        with pytest.raises(VFSStorageNotFoundError):
            await vfs_storage_repository.get_by_name("non-existent-storage")

    # =========================================================================
    # Tests - Create
    # =========================================================================

    async def test_create(
        self,
        vfs_storage_repository: VFSStorageRepository,
        vfs_storage_creator_spec: VFSStorageCreatorSpec,
    ) -> None:
        """Test creating a new VFS storage via Creator"""
        result = await vfs_storage_repository.create(Creator(spec=vfs_storage_creator_spec))

        assert result.name == "new-vfs-storage"
        assert result.host == "storage-host-1"
        assert str(result.base_path) == "/mnt/nfs/new"
        assert result.id is not None

        # Verify persisted in DB
        fetched = await vfs_storage_repository.get_by_id(result.id)
        assert fetched.name == "new-vfs-storage"

    async def test_create_duplicate_name_raises_error(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storage_id: uuid.UUID,
        vfs_storage_creator_spec: VFSStorageCreatorSpec,
    ) -> None:
        """Test creating VFS storage with duplicate name raises error"""
        duplicate_spec = VFSStorageCreatorSpec(
            name="test-vfs-storage",
            host=vfs_storage_creator_spec.host,
            base_path=vfs_storage_creator_spec.base_path,
        )
        with pytest.raises(Exception):
            await vfs_storage_repository.create(Creator(spec=duplicate_spec))

    # =========================================================================
    # Tests - Update
    # =========================================================================

    async def test_update(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storage_id: uuid.UUID,
        vfs_storage_updater_spec: VFSStorageUpdaterSpec,
    ) -> None:
        """Test updating an existing VFS storage via Updater"""
        updater = Updater(spec=vfs_storage_updater_spec, pk_value=sample_vfs_storage_id)
        result = await vfs_storage_repository.update(updater)

        assert result.id == sample_vfs_storage_id
        assert result.host == "updated-host"
        assert str(result.base_path) == "/mnt/vfs/updated"
        # Unchanged fields remain the same
        assert result.name == "test-vfs-storage"

    async def test_update_partial(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storage_id: uuid.UUID,
    ) -> None:
        """Test partial update only changes specified fields"""
        partial_spec = VFSStorageUpdaterSpec(
            host=OptionalState.update("partial-updated-host"),
        )
        updater = Updater(spec=partial_spec, pk_value=sample_vfs_storage_id)
        result = await vfs_storage_repository.update(updater)

        assert result.host == "partial-updated-host"
        # base_path should remain unchanged
        assert str(result.base_path) == "/mnt/vfs/test"

    async def test_update_not_found(
        self,
        vfs_storage_repository: VFSStorageRepository,
    ) -> None:
        """Test updating non-existent VFS storage raises error"""
        not_found_updater = Updater(
            spec=VFSStorageUpdaterSpec(
                host=OptionalState.update("updated-host"),
            ),
            pk_value=uuid.uuid4(),
        )

        with pytest.raises(VFSStorageNotFoundError):
            await vfs_storage_repository.update(not_found_updater)

    # =========================================================================
    # Tests - Delete
    # =========================================================================

    async def test_delete(
        self,
        vfs_storage_repository: VFSStorageRepository,
        sample_vfs_storage_id: uuid.UUID,
    ) -> None:
        """Test deleting an existing VFS storage"""
        deleted_id = await vfs_storage_repository.delete(sample_vfs_storage_id)

        assert deleted_id == sample_vfs_storage_id

        # Verify it no longer exists
        with pytest.raises(VFSStorageNotFoundError):
            await vfs_storage_repository.get_by_id(sample_vfs_storage_id)

    async def test_delete_not_found(
        self,
        vfs_storage_repository: VFSStorageRepository,
    ) -> None:
        """Test deleting non-existent VFS storage raises error"""
        with pytest.raises(VFSStorageNotFoundError):
            await vfs_storage_repository.delete(uuid.uuid4())
