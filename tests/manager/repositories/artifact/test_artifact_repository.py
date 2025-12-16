"""
Tests for ArtifactRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.modifier import ArtifactModifier
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.errors.artifact import (
    ArtifactNotFoundError,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.types import TriState


class TestArtifactRepository:
    """Test cases for ArtifactRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans artifact data after each test"""
        yield database_engine

        # Cleanup all artifact data after test
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(ArtifactRevisionRow))
            await db_sess.execute(sa.delete(ArtifactRow))

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
        now = datetime.now(timezone.utc)

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
                scanned_at=now,
                updated_at=now,
            )
            db_sess.add(artifact)
            await db_sess.flush()

        yield artifact_id

    @pytest.fixture
    async def sample_revision_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_artifact_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample artifact revision directly in DB and return its ID"""
        revision_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        async with db_with_cleanup.begin_session() as db_sess:
            revision = ArtifactRevisionRow(
                id=revision_id,
                artifact_id=sample_artifact_id,
                version="main",
                readme="# DialoGPT-medium\n\nA conversational AI model.",
                size=1024000,
                status=ArtifactStatus.AVAILABLE.value,
                created_at=now,
                updated_at=now,
            )
            db_sess.add(revision)
            await db_sess.flush()

        yield revision_id

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
    async def artifact_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ArtifactRepository, None]:
        """Create ArtifactRepository instance with database"""
        repo = ArtifactRepository(db=db_with_cleanup)
        yield repo

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

    async def test_update_artifact(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
    ) -> None:
        """Test updating artifact"""
        modifier = ArtifactModifier(
            description=TriState.update("Updated description"),
        )

        updated_artifact = await artifact_repository.update_artifact(
            artifact_id=sample_artifact_id,
            modifier=modifier,
        )

        assert updated_artifact is not None
        assert updated_artifact.description == "Updated description"

    async def test_list_artifact_revisions(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test listing artifact revisions"""
        revisions = await artifact_repository.list_artifact_revisions(sample_artifact_id)

        assert len(revisions) >= 1
        revision_ids = [r.id for r in revisions]
        assert sample_revision_id in revision_ids

    async def test_get_artifact_revision_by_id(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test retrieving artifact revision by ID"""
        revision = await artifact_repository.get_artifact_revision_by_id(sample_revision_id)

        assert revision is not None
        assert revision.id == sample_revision_id
        assert revision.version == "main"

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

    async def test_search_artifacts(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
    ) -> None:
        """Test searching artifacts"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await artifact_repository.search_artifacts(querier=querier)

        assert len(result.items) >= 1
        assert result.total_count >= 1
        artifact_ids = [a.id for a in result.items]
        assert sample_artifact_id in artifact_ids

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

    async def test_update_artifact_revision_status(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test updating artifact revision status"""
        updated_revision_id = await artifact_repository.update_artifact_revision_status(
            sample_revision_id, ArtifactStatus.VERIFYING
        )

        assert updated_revision_id == sample_revision_id

        # Verify status was updated
        revision = await artifact_repository.get_artifact_revision_by_id(sample_revision_id)
        assert revision.status == ArtifactStatus.VERIFYING

    async def test_update_artifact_revision_bytesize(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test updating artifact revision byte size"""
        new_size = 2048000

        updated_revision_id = await artifact_repository.update_artifact_revision_bytesize(
            sample_revision_id, new_size
        )

        assert updated_revision_id == sample_revision_id

        # Verify size was updated
        revision = await artifact_repository.get_artifact_revision_by_id(sample_revision_id)
        assert revision.size == new_size

    async def test_approve_artifact(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test approving artifact (changing status to AVAILABLE)"""
        # First create a revision with NEEDS_APPROVAL status
        revision_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        async with db_with_cleanup.begin_session() as db_sess:
            revision = ArtifactRevisionRow(
                id=revision_id,
                artifact_id=sample_artifact_id,
                version="v1.0",
                readme="# Test model",
                size=512000,
                status=ArtifactStatus.NEEDS_APPROVAL.value,
                created_at=now,
                updated_at=now,
            )
            db_sess.add(revision)
            await db_sess.flush()

        # Approve the artifact
        approved_revision = await artifact_repository.approve_artifact(revision_id)

        assert approved_revision.status == ArtifactStatus.AVAILABLE

    async def test_reject_artifact(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test rejecting artifact (changing status to REJECTED)"""
        # First create a revision with NEEDS_APPROVAL status
        revision_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        async with db_with_cleanup.begin_session() as db_sess:
            revision = ArtifactRevisionRow(
                id=revision_id,
                artifact_id=sample_artifact_id,
                version="v2.0",
                readme="# Test model",
                size=512000,
                status=ArtifactStatus.NEEDS_APPROVAL.value,
                created_at=now,
                updated_at=now,
            )
            db_sess.add(revision)
            await db_sess.flush()

        # Reject the artifact
        rejected_revision = await artifact_repository.reject_artifact(revision_id)

        assert rejected_revision.status == ArtifactStatus.REJECTED

    async def test_get_artifact_revision_readme(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test getting artifact revision readme"""
        readme = await artifact_repository.get_artifact_revision_readme(sample_revision_id)

        assert readme is not None
        assert "DialoGPT-medium" in readme

    async def test_update_artifact_revision_readme(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test updating artifact revision readme"""
        new_readme = "# Updated Readme\n\nThis is updated content."

        updated_revision_id = await artifact_repository.update_artifact_revision_readme(
            sample_revision_id, new_readme
        )

        assert updated_revision_id == sample_revision_id

        # Verify readme was updated
        readme = await artifact_repository.get_artifact_revision_readme(sample_revision_id)
        assert readme == new_readme
