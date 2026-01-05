"""
Tests for ArtifactRegistryRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.testutils.db import with_tables


class TestArtifactRegistryRepository:
    """Test cases for ArtifactRegistryRepository"""

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
                ArtifactRegistryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample artifact registry directly in DB and return its ID"""
        registry_id = uuid.uuid4()
        row_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            registry = ArtifactRegistryRow(
                id=row_id,
                registry_id=registry_id,
                name="test-huggingface-registry",
                type=ArtifactRegistryType.HUGGINGFACE.value,
            )
            db_sess.add(registry)
            await db_sess.flush()

        yield registry_id

    @pytest.fixture
    async def sample_registries_for_filtering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[ArtifactRegistryType, uuid.UUID], None]:
        """Create sample artifact registries with different types for filter testing"""
        registry_map: dict[ArtifactRegistryType, uuid.UUID] = {}
        types = [ArtifactRegistryType.HUGGINGFACE, ArtifactRegistryType.RESERVOIR]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, registry_type in enumerate(types):
                registry_id = uuid.uuid4()
                row_id = uuid.uuid4()
                registry = ArtifactRegistryRow(
                    id=row_id,
                    registry_id=registry_id,
                    name=f"type-test-{registry_type.value}-{i}",
                    type=registry_type.value,
                )
                db_sess.add(registry)
                registry_map[registry_type] = registry_id
            await db_sess.flush()

        yield registry_map

    @pytest.fixture
    async def sample_registries_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample artifact registries with predictable names for ordering tests"""
        registry_ids = []
        names = ["alpha-registry", "beta-registry", "gamma-registry", "delta-registry"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                registry_id = uuid.uuid4()
                row_id = uuid.uuid4()
                registry = ArtifactRegistryRow(
                    id=row_id,
                    registry_id=registry_id,
                    name=name,
                    type=ArtifactRegistryType.HUGGINGFACE.value,
                )
                db_sess.add(registry)
                registry_ids.append(registry_id)
            await db_sess.flush()

        yield registry_ids

    @pytest.fixture
    async def sample_registries_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 sample artifact registries for pagination testing"""
        registry_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                registry_id = uuid.uuid4()
                row_id = uuid.uuid4()
                registry = ArtifactRegistryRow(
                    id=row_id,
                    registry_id=registry_id,
                    name=f"registry-{i:02d}",
                    type=ArtifactRegistryType.HUGGINGFACE.value,
                )
                db_sess.add(registry)
                registry_ids.append(registry_id)
            await db_sess.flush()

        yield registry_ids

    @pytest.fixture
    async def artifact_registry_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ArtifactRegistryRepository, None]:
        """Create ArtifactRegistryRepository instance with database"""
        repo = ArtifactRegistryRepository(db=db_with_cleanup)
        yield repo

    # =========================================================================
    # Tests - Get by ID
    # =========================================================================

    async def test_get_artifact_registry_data(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registry_id: uuid.UUID,
    ) -> None:
        """Test retrieving artifact registry by registry_id"""
        retrieved_registry = await artifact_registry_repository.get_artifact_registry_data(
            sample_registry_id
        )

        assert retrieved_registry is not None
        assert retrieved_registry.registry_id == sample_registry_id
        assert retrieved_registry.name == "test-huggingface-registry"
        assert retrieved_registry.type == ArtifactRegistryType.HUGGINGFACE

    async def test_get_artifact_registry_data_not_found(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
    ) -> None:
        """Test retrieving non-existent artifact registry raises error"""
        with pytest.raises(ArtifactRegistryNotFoundError):
            await artifact_registry_repository.get_artifact_registry_data(uuid.uuid4())

    # =========================================================================
    # Tests - Get by Name
    # =========================================================================

    async def test_get_artifact_registry_data_by_name(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registry_id: uuid.UUID,
    ) -> None:
        """Test retrieving artifact registry by name"""
        retrieved_registry = await artifact_registry_repository.get_artifact_registry_data_by_name(
            "test-huggingface-registry"
        )

        assert retrieved_registry is not None
        assert retrieved_registry.registry_id == sample_registry_id
        assert retrieved_registry.name == "test-huggingface-registry"

    async def test_get_artifact_registry_data_by_name_not_found(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
    ) -> None:
        """Test retrieving non-existent artifact registry by name raises error"""
        with pytest.raises(ArtifactRegistryNotFoundError):
            await artifact_registry_repository.get_artifact_registry_data_by_name(
                "non-existent-registry"
            )

    # =========================================================================
    # Tests - Get Multiple
    # =========================================================================

    async def test_get_artifact_registry_datas(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test retrieving multiple artifact registries by IDs"""
        registry_ids = sample_registries_for_ordering[:2]
        retrieved_registries = await artifact_registry_repository.get_artifact_registry_datas(
            registry_ids
        )

        assert len(retrieved_registries) == 2
        retrieved_ids = [r.registry_id for r in retrieved_registries]
        for registry_id in registry_ids:
            assert registry_id in retrieved_ids

    async def test_get_artifact_registry_datas_empty(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
    ) -> None:
        """Test retrieving multiple artifact registries with empty list returns empty"""
        retrieved_registries = await artifact_registry_repository.get_artifact_registry_datas([])

        assert len(retrieved_registries) == 0

    # =========================================================================
    # Tests - Get Type
    # =========================================================================

    async def test_get_artifact_registry_type(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registry_id: uuid.UUID,
    ) -> None:
        """Test retrieving artifact registry type by ID"""
        registry_type = await artifact_registry_repository.get_artifact_registry_type(
            sample_registry_id
        )

        assert registry_type == ArtifactRegistryType.HUGGINGFACE

    async def test_get_artifact_registry_type_not_found(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
    ) -> None:
        """Test retrieving type for non-existent artifact registry raises error"""
        with pytest.raises(ArtifactRegistryNotFoundError):
            await artifact_registry_repository.get_artifact_registry_type(uuid.uuid4())

    # =========================================================================
    # Tests - List
    # =========================================================================

    async def test_list_artifact_registry_data(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test listing all artifact registries"""
        registries = await artifact_registry_repository.list_artifact_registry_data()

        assert len(registries) >= 4
        registry_ids = [r.registry_id for r in registries]
        for expected_id in sample_registries_for_ordering:
            assert expected_id in registry_ids

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_artifact_registries_filter_by_type(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_filtering: dict[ArtifactRegistryType, uuid.UUID],
    ) -> None:
        """Test searching artifact registries filtered by type returns only matching registries"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRegistryRow.type == ArtifactRegistryType.HUGGINGFACE.value,
            ],
            orders=[],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        result_registry_ids = [registry.registry_id for registry in result.items]
        assert (
            sample_registries_for_filtering[ArtifactRegistryType.HUGGINGFACE] in result_registry_ids
        )
        assert (
            sample_registries_for_filtering[ArtifactRegistryType.RESERVOIR]
            not in result_registry_ids
        )

    async def test_search_artifact_registries_filter_by_name_pattern(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching artifact registries filtered by name pattern"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRegistryRow.name.like("alpha%"),
            ],
            orders=[],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        assert len(result.items) == 1
        for registry in result.items:
            assert registry.name.startswith("alpha")

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_artifact_registries_order_by_name_ascending(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching artifact registries ordered by name ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRegistryRow.name.in_([
                    "alpha-registry",
                    "beta-registry",
                    "gamma-registry",
                    "delta-registry",
                ]),
            ],
            orders=[ArtifactRegistryRow.name.asc()],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        result_names = [registry.name for registry in result.items]
        assert result_names == sorted(result_names)
        assert result_names[0] == "alpha-registry"
        assert result_names[-1] == "gamma-registry"

    async def test_search_artifact_registries_order_by_name_descending(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching artifact registries ordered by name descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRegistryRow.name.in_([
                    "alpha-registry",
                    "beta-registry",
                    "gamma-registry",
                    "delta-registry",
                ]),
            ],
            orders=[ArtifactRegistryRow.name.desc()],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        result_names = [registry.name for registry in result.items]
        assert result_names == sorted(result_names, reverse=True)
        assert result_names[0] == "gamma-registry"
        assert result_names[-1] == "alpha-registry"

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_artifact_registries_offset_pagination_first_page(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRegistryRow.name.like("registry-%"),
            ],
            orders=[],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_artifact_registries_offset_pagination_second_page(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[
                lambda: ArtifactRegistryRow.name.like("registry-%"),
            ],
            orders=[],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_artifact_registries_offset_pagination_last_page(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[
                lambda: ArtifactRegistryRow.name.like("registry-%"),
            ],
            orders=[],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_artifact_registries_with_pagination_filter_and_order(
        self,
        artifact_registry_repository: ArtifactRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching artifact registries with pagination, filter condition, and ordering combined"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=5),
            conditions=[
                lambda: ArtifactRegistryRow.name.like("registry-%"),
                lambda: ArtifactRegistryRow.type == ArtifactRegistryType.HUGGINGFACE.value,
            ],
            orders=[ArtifactRegistryRow.name.asc()],
        )

        result = await artifact_registry_repository.search_artifact_registries(querier=querier)

        # Total matching registries: 25, so total_count should be 25
        assert result.total_count == 25
        # With limit=5, offset=5, we get items at indices 5-9 of sorted results
        assert len(result.items) == 5

        # Verify ordering is ascending
        result_names = [registry.name for registry in result.items]
        assert result_names == sorted(result_names)

        # Verify all returned items are HUGGINGFACE type
        for registry in result.items:
            assert registry.type == ArtifactRegistryType.HUGGINGFACE
