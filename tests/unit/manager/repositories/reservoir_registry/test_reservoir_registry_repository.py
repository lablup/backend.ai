"""
Tests for ReservoirRegistryRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.testutils.db import with_tables


class TestReservoirRegistryRepository:
    """Test cases for ReservoirRegistryRepository"""

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
                ReservoirRegistryRow,
                ArtifactRegistryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample Reservoir registry directly in DB and return its ID"""
        registry_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Create Reservoir registry row
            reservoir_registry = ReservoirRegistryRow(
                id=registry_id,
                endpoint="https://reservoir.example.com",
                access_key="test-access-key",
                secret_key="test-secret-key",
                api_version="v1",
            )
            db_sess.add(reservoir_registry)
            await db_sess.flush()

            # Create artifact registry meta row
            artifact_registry = ArtifactRegistryRow(
                registry_id=registry_id,
                name="test-reservoir-registry",
                type=ArtifactRegistryType.RESERVOIR.value,
            )
            db_sess.add(artifact_registry)
            await db_sess.flush()

        yield registry_id

    @pytest.fixture
    async def sample_registries_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample Reservoir registries with predictable names for ordering tests"""
        registry_ids = []
        names = ["alpha-registry", "beta-registry", "gamma-registry", "delta-registry"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                registry_id = uuid.uuid4()

                reservoir_registry = ReservoirRegistryRow(
                    id=registry_id,
                    endpoint=f"https://reservoir.example.com/{name}",
                    access_key="test-access-key",
                    secret_key="test-secret-key",
                    api_version="v1",
                )
                db_sess.add(reservoir_registry)
                await db_sess.flush()

                artifact_registry = ArtifactRegistryRow(
                    registry_id=registry_id,
                    name=name,
                    type=ArtifactRegistryType.RESERVOIR.value,
                )
                db_sess.add(artifact_registry)
                registry_ids.append(registry_id)
            await db_sess.flush()

        yield registry_ids

    @pytest.fixture
    async def sample_registries_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 sample Reservoir registries for pagination testing"""
        registry_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                registry_id = uuid.uuid4()

                reservoir_registry = ReservoirRegistryRow(
                    id=registry_id,
                    endpoint=f"https://reservoir.example.com/registry-{i:02d}",
                    access_key="test-access-key",
                    secret_key="test-secret-key",
                    api_version="v1",
                )
                db_sess.add(reservoir_registry)
                await db_sess.flush()

                artifact_registry = ArtifactRegistryRow(
                    registry_id=registry_id,
                    name=f"reservoir-registry-{i:02d}",
                    type=ArtifactRegistryType.RESERVOIR.value,
                )
                db_sess.add(artifact_registry)
                registry_ids.append(registry_id)
            await db_sess.flush()

        yield registry_ids

    @pytest.fixture
    async def reservoir_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ReservoirRegistryRepository, None]:
        """Create ReservoirRegistryRepository instance with database"""
        repo = ReservoirRegistryRepository(db=db_with_cleanup)
        yield repo

    # =========================================================================
    # Tests - Get by ID
    # =========================================================================

    async def test_get_registry_data_by_id(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registry_id: uuid.UUID,
    ) -> None:
        """Test retrieving Reservoir registry by ID"""
        retrieved_registry = await reservoir_repository.get_reservoir_registry_data_by_id(
            sample_registry_id
        )

        assert retrieved_registry is not None
        assert retrieved_registry.id == sample_registry_id
        assert retrieved_registry.name == "test-reservoir-registry"
        assert retrieved_registry.endpoint == "https://reservoir.example.com"

    async def test_get_registry_data_by_id_not_found(
        self,
        reservoir_repository: ReservoirRegistryRepository,
    ) -> None:
        """Test retrieving non-existent Reservoir registry raises error"""
        with pytest.raises(ArtifactRegistryNotFoundError):
            await reservoir_repository.get_reservoir_registry_data_by_id(uuid.uuid4())

    # =========================================================================
    # Tests - Get by Name
    # =========================================================================

    async def test_get_registry_data_by_name(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registry_id: uuid.UUID,
    ) -> None:
        """Test retrieving Reservoir registry by name"""
        retrieved_registry = await reservoir_repository.get_registry_data_by_name(
            "test-reservoir-registry"
        )

        assert retrieved_registry is not None
        assert retrieved_registry.id == sample_registry_id
        assert retrieved_registry.name == "test-reservoir-registry"

    async def test_get_registry_data_by_name_not_found(
        self,
        reservoir_repository: ReservoirRegistryRepository,
    ) -> None:
        """Test retrieving non-existent Reservoir registry by name raises error"""
        with pytest.raises(ArtifactRegistryNotFoundError):
            await reservoir_repository.get_registry_data_by_name("non-existent-registry")

    # =========================================================================
    # Tests - Get Multiple
    # =========================================================================

    async def test_get_registries_by_ids(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test retrieving multiple Reservoir registries by IDs"""
        registry_ids = sample_registries_for_ordering[:2]
        retrieved_registries = await reservoir_repository.get_registries_by_ids(registry_ids)

        assert len(retrieved_registries) == 2
        retrieved_ids = [r.id for r in retrieved_registries]
        for registry_id in registry_ids:
            assert registry_id in retrieved_ids

    async def test_get_registries_by_ids_empty(
        self,
        reservoir_repository: ReservoirRegistryRepository,
    ) -> None:
        """Test retrieving multiple Reservoir registries with empty list returns empty"""
        retrieved_registries = await reservoir_repository.get_registries_by_ids([])

        assert len(retrieved_registries) == 0

    # =========================================================================
    # Tests - List
    # =========================================================================

    async def test_list_registries(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test listing all Reservoir registries"""
        registries = await reservoir_repository.list_reservoir_registries()

        assert len(registries) >= 4
        registry_ids = [r.id for r in registries]
        for expected_id in sample_registries_for_ordering:
            assert expected_id in registry_ids

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_registries_offset_pagination_first_page(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ReservoirRegistryRow.endpoint.like("%reservoir.example.com/registry-%"),
            ],
            orders=[],
        )

        result = await reservoir_repository.search_registries(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_registries_offset_pagination_second_page(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ReservoirRegistryRow.endpoint.like("%reservoir.example.com/registry-%"),
            ],
            orders=[],
        )

        result = await reservoir_repository.search_registries(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_registries_offset_pagination_last_page(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ReservoirRegistryRow.endpoint.like("%reservoir.example.com/registry-%"),
            ],
            orders=[],
        )

        result = await reservoir_repository.search_registries(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_registries_order_by_endpoint_ascending(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching Reservoir registries ordered by endpoint ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ReservoirRegistryRow.endpoint.in_([
                    "https://reservoir.example.com/alpha-registry",
                    "https://reservoir.example.com/beta-registry",
                    "https://reservoir.example.com/gamma-registry",
                    "https://reservoir.example.com/delta-registry",
                ]),
            ],
            orders=[ReservoirRegistryRow.endpoint.asc()],
        )

        result = await reservoir_repository.search_registries(querier=querier)

        result_endpoints = [registry.endpoint for registry in result.items]
        assert result_endpoints == sorted(result_endpoints)

    async def test_search_registries_order_by_endpoint_descending(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching Reservoir registries ordered by endpoint descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ReservoirRegistryRow.endpoint.in_([
                    "https://reservoir.example.com/alpha-registry",
                    "https://reservoir.example.com/beta-registry",
                    "https://reservoir.example.com/gamma-registry",
                    "https://reservoir.example.com/delta-registry",
                ]),
            ],
            orders=[ReservoirRegistryRow.endpoint.desc()],
        )

        result = await reservoir_repository.search_registries(querier=querier)

        result_endpoints = [registry.endpoint for registry in result.items]
        assert result_endpoints == sorted(result_endpoints, reverse=True)

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_registries_with_pagination_filter_and_order(
        self,
        reservoir_repository: ReservoirRegistryRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching Reservoir registries with pagination, filter, and ordering combined"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=5),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: ReservoirRegistryRow.endpoint.like("%reservoir.example.com/registry-%"),
            ],
            orders=[ReservoirRegistryRow.endpoint.asc()],
        )

        result = await reservoir_repository.search_registries(querier=querier)

        # Total matching registries: 25, so total_count should be 25
        assert result.total_count == 25
        # With limit=5, offset=5, we get 5 items
        assert len(result.items) == 5

        # Verify ordering is ascending
        result_endpoints = [registry.endpoint for registry in result.items]
        assert result_endpoints == sorted(result_endpoints)
