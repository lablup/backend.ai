"""
Tests for StorageNamespaceRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.storage_namespace.searchers import StorageNamespaceSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.storage_namespace.repository import (
    StorageNamespaceRepository,
)
from ai.backend.testutils.db import with_tables


class TestStorageNamespaceRepository:
    """Test cases for StorageNamespaceRepository"""

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
            [StorageNamespaceRow],
        ):
            yield database_connection

    @pytest.fixture
    def storage_namespace_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> StorageNamespaceRepository:
        """Create a StorageNamespaceRepository instance"""
        return StorageNamespaceRepository(db_with_cleanup)

    @pytest.fixture
    def namespace_ops(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> OpsRepository[StorageNamespaceData]:
        """Registration and searches run through the generic ops repository."""
        return OpsRepository(V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    def test_storage_id(self) -> uuid.UUID:
        """Return a test storage UUID (no actual storage row needed due to no FK constraint)"""
        return uuid.uuid4()

    @pytest.fixture
    async def sample_storage_namespace_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_storage_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample storage namespace directly in DB and return its ID"""
        namespace_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            namespace = StorageNamespaceRow(
                id=namespace_id,
                storage_id=test_storage_id,
                namespace="test-namespace",
            )
            db_sess.add(namespace)
            await db_sess.flush()

        yield namespace_id

    @pytest.fixture
    async def sample_storage_namespaces_for_filtering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[uuid.UUID, uuid.UUID], None]:
        """Create sample storage namespaces with different storage_ids for filter testing"""
        namespace_map: dict[uuid.UUID, uuid.UUID] = {}
        storage_ids = [uuid.uuid4(), uuid.uuid4()]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, storage_id in enumerate(storage_ids):
                namespace_id = uuid.uuid4()
                namespace = StorageNamespaceRow(
                    id=namespace_id,
                    storage_id=storage_id,
                    namespace=f"filter-test-namespace-{i}",
                )
                db_sess.add(namespace)
                namespace_map[storage_id] = namespace_id
            await db_sess.flush()

        yield namespace_map

    @pytest.fixture
    async def sample_storage_namespaces_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_storage_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample storage namespaces with predictable names for ordering tests"""
        namespace_ids = []
        names = ["alpha-ns", "beta-ns", "gamma-ns", "delta-ns"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                namespace_id = uuid.uuid4()
                namespace = StorageNamespaceRow(
                    id=namespace_id,
                    storage_id=test_storage_id,
                    namespace=name,
                )
                db_sess.add(namespace)
                namespace_ids.append(namespace_id)
            await db_sess.flush()

        yield namespace_ids

    @pytest.fixture
    async def sample_storage_namespaces_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_storage_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 storage namespaces for pagination testing"""
        namespace_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                namespace_id = uuid.uuid4()
                namespace = StorageNamespaceRow(
                    id=namespace_id,
                    storage_id=test_storage_id,
                    namespace=f"pagination-test-ns-{i:02d}",
                )
                db_sess.add(namespace)
                namespace_ids.append(namespace_id)
            await db_sess.flush()

        yield namespace_ids

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_storage_namespaces_filter_by_storage_id(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_filtering: dict[uuid.UUID, uuid.UUID],
    ) -> None:
        """Test searching storage namespaces filtered by storage_id returns only matching namespaces"""
        target_storage_id = list(sample_storage_namespaces_for_filtering.keys())[0]
        other_storage_id = list(sample_storage_namespaces_for_filtering.keys())[1]

        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: StorageNamespaceRow.storage_id == target_storage_id,
            ],
            orders=[],
        )

        result = await namespace_ops.search_in_global(searcher)

        result_namespace_ids = [ns.id for ns in result.items]
        assert sample_storage_namespaces_for_filtering[target_storage_id] in result_namespace_ids
        assert sample_storage_namespaces_for_filtering[other_storage_id] not in result_namespace_ids

    async def test_search_storage_namespaces_filter_by_namespace_pattern(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching storage namespaces with namespace pattern filter"""
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: StorageNamespaceRow.namespace.like("alpha%"),
            ],
            orders=[],
        )

        result = await namespace_ops.search_in_global(searcher)

        assert len(result.items) == 1
        assert result.items[0].namespace == "alpha-ns"

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_storage_namespaces_order_by_namespace_ascending(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching storage namespaces ordered by namespace ascending"""
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[StorageNamespaceRow.namespace.asc()],
        )

        result = await namespace_ops.search_in_global(searcher)

        result_names = [ns.namespace for ns in result.items]
        assert result_names == sorted(result_names)
        assert result_names[0] == "alpha-ns"
        assert result_names[-1] == "gamma-ns"

    async def test_search_storage_namespaces_order_by_namespace_descending(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching storage namespaces ordered by namespace descending"""
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[StorageNamespaceRow.namespace.desc()],
        )

        result = await namespace_ops.search_in_global(searcher)

        result_names = [ns.namespace for ns in result.items]
        assert result_names == sorted(result_names, reverse=True)
        assert result_names[0] == "gamma-ns"
        assert result_names[-1] == "alpha-ns"

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_storage_namespaces_offset_pagination_first_page(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await namespace_ops.search_in_global(searcher)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_storage_namespaces_offset_pagination_second_page(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await namespace_ops.search_in_global(searcher)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_storage_namespaces_offset_pagination_last_page(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await namespace_ops.search_in_global(searcher)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_storage_namespaces_with_pagination_filter_and_order(
        self,
        namespace_ops: OpsRepository[StorageNamespaceData],
        storage_namespace_repository: StorageNamespaceRepository,
        sample_storage_namespaces_for_pagination: list[uuid.UUID],
        test_storage_id: uuid.UUID,
    ) -> None:
        """Test searching storage namespaces with pagination, filter condition, and ordering combined"""
        # Filter: only namespaces with the test storage_id
        # Order: by namespace ascending
        # Pagination: limit 5, offset 2
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=5, offset=2),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: StorageNamespaceRow.storage_id == test_storage_id,
            ],
            orders=[StorageNamespaceRow.namespace.asc()],
        )

        result = await namespace_ops.search_in_global(searcher)

        # Total namespaces with test_storage_id: 25, so total_count should be 25
        assert result.total_count == 25
        # With limit=5, offset=2, we get items at indices 2, 3, 4, 5, 6 of sorted results
        assert len(result.items) == 5

        # Verify ordering is ascending
        result_names = [ns.namespace for ns in result.items]
        assert result_names == sorted(result_names)
