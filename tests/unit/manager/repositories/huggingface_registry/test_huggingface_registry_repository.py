"""
Tests for HuggingFaceRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.testutils.db import with_tables


class TestHuggingFaceRepository:
    """Test cases for HuggingFaceRepository"""

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
                HuggingFaceRegistryRow,
                ArtifactRegistryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample HuggingFace registry directly in DB and return its ID"""
        registry_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Create HuggingFace registry row
            hf_registry = HuggingFaceRegistryRow(
                id=registry_id,
                url="https://huggingface.co",
                token="test-token",
            )
            db_sess.add(hf_registry)
            await db_sess.flush()

            # Create artifact registry meta row
            artifact_registry = ArtifactRegistryRow(
                registry_id=registry_id,
                name="test-huggingface-registry",
                type=ArtifactRegistryType.HUGGINGFACE.value,
            )
            db_sess.add(artifact_registry)
            await db_sess.flush()

        yield registry_id

    @pytest.fixture
    async def sample_registries_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample HuggingFace registries with predictable names for ordering tests"""
        registry_ids = []
        names = ["alpha-registry", "beta-registry", "gamma-registry", "delta-registry"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                registry_id = uuid.uuid4()

                hf_registry = HuggingFaceRegistryRow(
                    id=registry_id,
                    url=f"https://huggingface.co/{name}",
                    token=None,
                )
                db_sess.add(hf_registry)
                await db_sess.flush()

                artifact_registry = ArtifactRegistryRow(
                    registry_id=registry_id,
                    name=name,
                    type=ArtifactRegistryType.HUGGINGFACE.value,
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
        """Create 25 sample HuggingFace registries for pagination testing"""
        registry_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                registry_id = uuid.uuid4()

                hf_registry = HuggingFaceRegistryRow(
                    id=registry_id,
                    url=f"https://huggingface.co/registry-{i:02d}",
                    token=None,
                )
                db_sess.add(hf_registry)
                await db_sess.flush()

                artifact_registry = ArtifactRegistryRow(
                    registry_id=registry_id,
                    name=f"hf-registry-{i:02d}",
                    type=ArtifactRegistryType.HUGGINGFACE.value,
                )
                db_sess.add(artifact_registry)
                registry_ids.append(registry_id)
            await db_sess.flush()

        yield registry_ids

    @pytest.fixture
    async def huggingface_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[HuggingFaceRepository, None]:
        """Create HuggingFaceRepository instance with database"""
        repo = HuggingFaceRepository(db=db_with_cleanup)
        yield repo

    # =========================================================================
    # Tests - Get by ID
    # =========================================================================

    async def test_get_registry_data_by_id(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registry_id: uuid.UUID,
    ) -> None:
        """Test retrieving HuggingFace registry by ID"""
        retrieved_registry = await huggingface_repository.get_registry_data_by_id(
            sample_registry_id
        )

        assert retrieved_registry is not None
        assert retrieved_registry.id == sample_registry_id
        assert retrieved_registry.name == "test-huggingface-registry"
        assert retrieved_registry.url == "https://huggingface.co"

    async def test_get_registry_data_by_id_not_found(
        self,
        huggingface_repository: HuggingFaceRepository,
    ) -> None:
        """Test retrieving non-existent HuggingFace registry raises error"""
        with pytest.raises(ArtifactRegistryNotFoundError):
            await huggingface_repository.get_registry_data_by_id(uuid.uuid4())

    # =========================================================================
    # Tests - Get by Name
    # =========================================================================

    async def test_get_registry_data_by_name(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registry_id: uuid.UUID,
    ) -> None:
        """Test retrieving HuggingFace registry by name"""
        retrieved_registry = await huggingface_repository.get_registry_data_by_name(
            "test-huggingface-registry"
        )

        assert retrieved_registry is not None
        assert retrieved_registry.id == sample_registry_id
        assert retrieved_registry.name == "test-huggingface-registry"

    async def test_get_registry_data_by_name_not_found(
        self,
        huggingface_repository: HuggingFaceRepository,
    ) -> None:
        """Test retrieving non-existent HuggingFace registry by name raises error"""
        with pytest.raises(ArtifactRegistryNotFoundError):
            await huggingface_repository.get_registry_data_by_name("non-existent-registry")

    # =========================================================================
    # Tests - Get Multiple
    # =========================================================================

    async def test_get_registries_by_ids(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test retrieving multiple HuggingFace registries by IDs"""
        registry_ids = sample_registries_for_ordering[:2]
        retrieved_registries = await huggingface_repository.get_registries_by_ids(registry_ids)

        assert len(retrieved_registries) == 2
        retrieved_ids = [r.id for r in retrieved_registries]
        for registry_id in registry_ids:
            assert registry_id in retrieved_ids

    async def test_get_registries_by_ids_empty(
        self,
        huggingface_repository: HuggingFaceRepository,
    ) -> None:
        """Test retrieving multiple HuggingFace registries with empty list returns empty"""
        retrieved_registries = await huggingface_repository.get_registries_by_ids([])

        assert len(retrieved_registries) == 0

    # =========================================================================
    # Tests - List
    # =========================================================================

    async def test_list_registries(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test listing all HuggingFace registries"""
        registries = await huggingface_repository.list_registries()

        assert len(registries) == 4
        registry_ids = [r.id for r in registries]
        for expected_id in sample_registries_for_ordering:
            assert expected_id in registry_ids

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_registries_offset_pagination_first_page(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: HuggingFaceRegistryRow.url.like("%huggingface.co/registry-%"),
            ],
            orders=[],
        )

        result = await huggingface_repository.search_registries(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_registries_offset_pagination_second_page(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: HuggingFaceRegistryRow.url.like("%huggingface.co/registry-%"),
            ],
            orders=[],
        )

        result = await huggingface_repository.search_registries(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_registries_offset_pagination_last_page(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: HuggingFaceRegistryRow.url.like("%huggingface.co/registry-%"),
            ],
            orders=[],
        )

        result = await huggingface_repository.search_registries(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_registries_order_by_url_ascending(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching HuggingFace registries ordered by url ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: HuggingFaceRegistryRow.url.in_([
                    "https://huggingface.co/alpha-registry",
                    "https://huggingface.co/beta-registry",
                    "https://huggingface.co/gamma-registry",
                    "https://huggingface.co/delta-registry",
                ]),
            ],
            orders=[HuggingFaceRegistryRow.url.asc()],
        )

        result = await huggingface_repository.search_registries(querier=querier)

        result_urls = [registry.url for registry in result.items]
        assert result_urls == sorted(result_urls)

    async def test_search_registries_order_by_url_descending(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching HuggingFace registries ordered by url descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: HuggingFaceRegistryRow.url.in_([
                    "https://huggingface.co/alpha-registry",
                    "https://huggingface.co/beta-registry",
                    "https://huggingface.co/gamma-registry",
                    "https://huggingface.co/delta-registry",
                ]),
            ],
            orders=[HuggingFaceRegistryRow.url.desc()],
        )

        result = await huggingface_repository.search_registries(querier=querier)

        result_urls = [registry.url for registry in result.items]
        assert result_urls == sorted(result_urls, reverse=True)

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_registries_with_pagination_filter_and_order(
        self,
        huggingface_repository: HuggingFaceRepository,
        sample_registries_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching HuggingFace registries with pagination, filter, and ordering combined"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=5),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: HuggingFaceRegistryRow.url.like("%huggingface.co/registry-%"),
            ],
            orders=[HuggingFaceRegistryRow.url.asc()],
        )

        result = await huggingface_repository.search_registries(querier=querier)

        # Total matching registries: 25, so total_count should be 25
        assert result.total_count == 25
        # With limit=5, offset=5, we get 5 items
        assert len(result.items) == 5

        # Verify ordering is ascending
        result_urls = [registry.url for registry in result.items]
        assert result_urls == sorted(result_urls)
