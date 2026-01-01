"""
Tests for ArtifactRepository functionality.
Tests the repository layer with real database operations.
Only artifact-related tests. Revision tests are in artifact_revision/test_artifact_revision_repository.py
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactType,
)
from ai.backend.manager.errors.artifact import (
    ArtifactNotFoundError,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.artifact.updaters import ArtifactUpdaterSpec
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.types import TriState
from ai.backend.testutils.db import with_tables


class TestArtifactRepository:
    """Test cases for ArtifactRepository (artifact-only operations)"""

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
                ArtifactRow,
                ArtifactRevisionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def test_registry_id(self) -> uuid.UUID:
        """Return a test registry UUID (no actual registry row needed due to no FK constraint)"""
        return uuid.uuid4()

    @pytest.fixture
    async def sample_artifact_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample artifact directly in DB and return its ID"""
        artifact_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            artifact = ArtifactRow(
                id=artifact_id,
                name="microsoft/DialoGPT-medium",
                type=ArtifactType.MODEL,
                registry_id=test_registry_id,
                registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                source_registry_id=test_registry_id,
                source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                description="A conversational AI model",
                readonly=True,
                availability=ArtifactAvailability.ALIVE.value,
            )
            db_sess.add(artifact)
            await db_sess.flush()

        yield artifact_id

    @pytest.fixture
    async def sample_artifacts_for_filtering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: uuid.UUID,
    ) -> AsyncGenerator[dict[ArtifactType, uuid.UUID], None]:
        """Create sample artifacts with different types for filter testing"""
        artifact_map: dict[ArtifactType, uuid.UUID] = {}
        types = [ArtifactType.MODEL, ArtifactType.PACKAGE]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, artifact_type in enumerate(types):
                artifact_id = uuid.uuid4()
                artifact = ArtifactRow(
                    id=artifact_id,
                    name=f"type-test-{artifact_type.value}-{i}",
                    type=artifact_type,
                    registry_id=test_registry_id,
                    registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    source_registry_id=test_registry_id,
                    source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    description=f"Artifact of type {artifact_type.value}",
                    readonly=True,
                    availability=ArtifactAvailability.ALIVE.value,
                )
                db_sess.add(artifact)
                artifact_map[artifact_type] = artifact_id
            await db_sess.flush()

        yield artifact_map

    @pytest.fixture
    async def sample_artifacts_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample artifacts with predictable names for ordering tests"""
        artifact_ids = []
        names = ["alpha-model", "beta-model", "gamma-model", "delta-model"]

        async with db_with_cleanup.begin_session() as db_sess:
            for name in names:
                artifact_id = uuid.uuid4()
                artifact = ArtifactRow(
                    id=artifact_id,
                    name=name,
                    type=ArtifactType.MODEL,
                    registry_id=test_registry_id,
                    registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    source_registry_id=test_registry_id,
                    source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    description=f"Model named {name}",
                    readonly=True,
                    availability=ArtifactAvailability.ALIVE.value,
                )
                db_sess.add(artifact)
                artifact_ids.append(artifact_id)
            await db_sess.flush()

        yield artifact_ids

    @pytest.fixture
    async def sample_artifacts_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 sample artifacts for pagination testing"""
        artifact_ids = []
        now = datetime.now(timezone.utc)

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                artifact_id = uuid.uuid4()
                artifact = ArtifactRow(
                    id=artifact_id,
                    name=f"model-{i:02d}/test-model",
                    type=ArtifactType.MODEL,
                    registry_id=test_registry_id,
                    registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    source_registry_id=test_registry_id,
                    source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    description=f"Test model {i}",
                    readonly=True,
                    availability=ArtifactAvailability.ALIVE.value,
                    scanned_at=now,
                    updated_at=now,
                )
                db_sess.add(artifact)
                artifact_ids.append(artifact_id)
            await db_sess.flush()

        yield artifact_ids

    @pytest.fixture
    async def sample_artifacts_for_combined_query(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_registry_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample artifacts for combined pagination, filter, and ordering tests"""
        artifact_ids = []
        # Create 10 ALIVE MODEL artifacts and 5 DELETED MODEL artifacts
        names = [f"model-{chr(ord('a') + i)}" for i in range(15)]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, name in enumerate(names):
                artifact_id = uuid.uuid4()
                artifact = ArtifactRow(
                    id=artifact_id,
                    name=name,
                    type=ArtifactType.MODEL,
                    registry_id=test_registry_id,
                    registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    source_registry_id=test_registry_id,
                    source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    description=f"Model {name}",
                    readonly=True,
                    availability=(
                        ArtifactAvailability.ALIVE.value
                        if i < 10
                        else ArtifactAvailability.DELETED.value
                    ),
                )
                db_sess.add(artifact)
                artifact_ids.append(artifact_id)
            await db_sess.flush()

        yield artifact_ids

    @pytest.fixture
    async def artifact_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ArtifactRepository, None]:
        """Create ArtifactRepository instance with database"""
        repo = ArtifactRepository(db=db_with_cleanup)
        yield repo

    # =========================================================================
    # Tests - Get
    # =========================================================================

    async def test_get_artifact_by_id(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
    ) -> None:
        """Test retrieving artifact by ID"""
        retrieved_artifact = await artifact_repository.get_artifact_by_id(sample_artifact_id)

        assert retrieved_artifact is not None
        assert retrieved_artifact.id == sample_artifact_id
        assert retrieved_artifact.name == "microsoft/DialoGPT-medium"

    async def test_get_artifact_by_id_not_found(
        self,
        artifact_repository: ArtifactRepository,
    ) -> None:
        """Test retrieving non-existent artifact raises error"""
        with pytest.raises(ArtifactNotFoundError):
            await artifact_repository.get_artifact_by_id(uuid.uuid4())

    # =========================================================================
    # Tests - Update
    # =========================================================================

    async def test_update_artifact(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
    ) -> None:
        """Test updating artifact"""
        updater = Updater[ArtifactRow](
            spec=ArtifactUpdaterSpec(
                description=TriState.update("Updated description"),
            ),
            pk_value=sample_artifact_id,
        )

        updated_artifact = await artifact_repository.update_artifact(updater)

        assert updated_artifact is not None
        assert updated_artifact.description == "Updated description"

    # =========================================================================
    # Tests - Delete/Restore
    # =========================================================================

    async def test_delete_artifacts(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
    ) -> None:
        """Test deleting artifact (soft delete)"""
        deleted_artifacts = await artifact_repository.delete_artifacts([sample_artifact_id])

        assert len(deleted_artifacts) == 1
        assert deleted_artifacts[0].availability == ArtifactAvailability.DELETED

        # Verify artifact is marked as deleted
        artifact = await artifact_repository.get_artifact_by_id(sample_artifact_id)
        assert artifact.availability == ArtifactAvailability.DELETED

    async def test_restore_artifacts(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
    ) -> None:
        """Test restoring deleted artifact"""
        # First delete the artifact
        await artifact_repository.delete_artifacts([sample_artifact_id])

        # Then restore it
        restored_artifacts = await artifact_repository.restore_artifacts([sample_artifact_id])

        assert len(restored_artifacts) == 1
        assert restored_artifacts[0].availability == ArtifactAvailability.ALIVE

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_artifacts_filter_by_type(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifacts_for_filtering: dict[ArtifactType, uuid.UUID],
    ) -> None:
        """Test searching artifacts filtered by type returns only matching artifacts"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRow.type == ArtifactType.MODEL,
            ],
            orders=[],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        result_artifact_ids = [artifact.id for artifact in result.items]
        assert sample_artifacts_for_filtering[ArtifactType.MODEL] in result_artifact_ids
        assert sample_artifacts_for_filtering[ArtifactType.PACKAGE] not in result_artifact_ids

    async def test_search_artifacts_filter_by_availability(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
    ) -> None:
        """Test searching artifacts filtered by availability returns only ALIVE artifacts"""
        # First delete the artifact
        await artifact_repository.delete_artifacts([sample_artifact_id])

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRow.availability == ArtifactAvailability.ALIVE.value,
            ],
            orders=[],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        result_artifact_ids = [artifact.id for artifact in result.items]
        assert sample_artifact_id not in result_artifact_ids

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_artifacts_order_by_name_ascending(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifacts_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching artifacts ordered by name ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ArtifactRow.name.asc()],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        result_names = [artifact.name for artifact in result.items]
        assert result_names == sorted(result_names)
        assert result_names[0] == "alpha-model"
        assert result_names[-1] == "gamma-model"

    async def test_search_artifacts_order_by_name_descending(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifacts_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching artifacts ordered by name descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ArtifactRow.name.desc()],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        result_names = [artifact.name for artifact in result.items]
        assert result_names == sorted(result_names, reverse=True)
        assert result_names[0] == "gamma-model"
        assert result_names[-1] == "alpha-model"

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_artifacts_offset_pagination_first_page(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifacts_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_artifacts_offset_pagination_second_page(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifacts_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_artifacts_offset_pagination_last_page(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifacts_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_artifacts_with_pagination_filter_and_order(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifacts_for_combined_query: list[uuid.UUID],
    ) -> None:
        """Test searching artifacts with pagination, filter condition, and ordering combined"""
        # Filter: only ALIVE artifacts
        # Order: by name descending
        # Pagination: limit 3, offset 2
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=3, offset=2),
            conditions=[
                lambda: ArtifactRow.availability == ArtifactAvailability.ALIVE.value,
            ],
            orders=[ArtifactRow.name.desc()],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        # Total ALIVE artifacts: 10, so total_count should be 10
        assert result.total_count == 10
        # With limit=3, offset=2, we get items at indices 2, 3, 4 of sorted results
        assert len(result.items) == 3

        # Verify ordering is descending
        result_names = [artifact.name for artifact in result.items]
        assert result_names == sorted(result_names, reverse=True)

        # Verify all returned items are ALIVE
        for artifact in result.items:
            assert artifact.availability == ArtifactAvailability.ALIVE
