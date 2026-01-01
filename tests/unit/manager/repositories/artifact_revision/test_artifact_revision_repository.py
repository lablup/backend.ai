"""
Tests for ArtifactRepository artifact revision functionality.
Tests the repository layer with real database operations for artifact revisions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.errors.artifact import (
    ArtifactRevisionNotFoundError,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.testutils.db import with_tables


class TestArtifactRevisionRepository:
    """Test cases for ArtifactRepository artifact revision methods"""

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
                # FK dependency order: parents first
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
    async def sample_revision_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_artifact_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create sample artifact revision directly in DB and return its ID"""
        revision_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            revision = ArtifactRevisionRow(
                id=revision_id,
                artifact_id=sample_artifact_id,
                version="main",
                readme="# DialoGPT-medium\n\nA conversational AI model.",
                size=1024000,
                status=ArtifactStatus.AVAILABLE.value,
            )
            db_sess.add(revision)
            await db_sess.flush()

        yield revision_id

    @pytest.fixture
    async def sample_revisions_for_filtering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_artifact_id: uuid.UUID,
    ) -> AsyncGenerator[dict[ArtifactStatus, uuid.UUID], None]:
        """Create sample revisions with different statuses for filter testing"""
        revision_map: dict[ArtifactStatus, uuid.UUID] = {}
        statuses = [
            ArtifactStatus.AVAILABLE,
            ArtifactStatus.SCANNED,
            ArtifactStatus.PULLING,
            ArtifactStatus.NEEDS_APPROVAL,
        ]

        async with db_with_cleanup.begin_session() as db_sess:
            for i, status in enumerate(statuses):
                revision_id = uuid.uuid4()
                revision = ArtifactRevisionRow(
                    id=revision_id,
                    artifact_id=sample_artifact_id,
                    version=f"status-test-v{i}",
                    readme=f"# Revision with status {status.value}",
                    size=1024000 + i * 1000,
                    status=status.value,
                )
                db_sess.add(revision)
                revision_map[status] = revision_id
            await db_sess.flush()

        yield revision_map

    @pytest.fixture
    async def sample_revisions_for_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_artifact_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample revisions with predictable versions for ordering tests"""
        revision_ids = []
        versions = ["v1.0.0", "v2.0.0", "v3.0.0", "v0.1.0"]

        async with db_with_cleanup.begin_session() as db_sess:
            for version in versions:
                revision_id = uuid.uuid4()
                revision = ArtifactRevisionRow(
                    id=revision_id,
                    artifact_id=sample_artifact_id,
                    version=version,
                    readme=f"# Version {version}",
                    size=1024000,
                    status=ArtifactStatus.AVAILABLE.value,
                )
                db_sess.add(revision)
                revision_ids.append(revision_id)
            await db_sess.flush()

        yield revision_ids

    @pytest.fixture
    async def sample_revisions_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_artifact_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 sample revisions for pagination testing"""
        revision_ids = []
        now = datetime.now(timezone.utc)

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                revision_id = uuid.uuid4()
                revision = ArtifactRevisionRow(
                    id=revision_id,
                    artifact_id=sample_artifact_id,
                    version=f"v{i:02d}",
                    readme=f"# Version {i}",
                    size=1024000 + i * 1000,
                    status=ArtifactStatus.AVAILABLE.value,
                    created_at=now,
                    updated_at=now,
                )
                db_sess.add(revision)
                revision_ids.append(revision_id)
            await db_sess.flush()

        yield revision_ids

    @pytest.fixture
    async def sample_revisions_for_combined_query(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_artifact_id: uuid.UUID,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample revisions for combined pagination, filter, and ordering tests"""
        revision_ids = []
        # Create 8 AVAILABLE revisions and 4 SCANNED revisions
        statuses = [ArtifactStatus.AVAILABLE] * 8 + [ArtifactStatus.SCANNED] * 4

        async with db_with_cleanup.begin_session() as db_sess:
            for i, status in enumerate(statuses):
                revision_id = uuid.uuid4()
                revision = ArtifactRevisionRow(
                    id=revision_id,
                    artifact_id=sample_artifact_id,
                    version=f"v{i:02d}.0.0",
                    readme=f"# Version {i}",
                    size=1024000 + i * 10000,
                    status=status.value,
                )
                db_sess.add(revision)
                revision_ids.append(revision_id)
            await db_sess.flush()

        yield revision_ids

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

    async def test_get_artifact_revision_by_id_not_found(
        self,
        artifact_repository: ArtifactRepository,
    ) -> None:
        """Test retrieving non-existent artifact revision raises error"""
        with pytest.raises(ArtifactRevisionNotFoundError):
            await artifact_repository.get_artifact_revision_by_id(uuid.uuid4())

    async def test_get_artifact_revision(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test retrieving artifact revision by artifact_id and version"""
        revision = await artifact_repository.get_artifact_revision(sample_artifact_id, "main")

        assert revision is not None
        assert revision.id == sample_revision_id
        assert revision.artifact_id == sample_artifact_id
        assert revision.version == "main"

    # =========================================================================
    # Tests - List
    # =========================================================================

    async def test_list_artifact_revisions(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test listing artifact revisions"""
        revisions = await artifact_repository.list_artifact_revisions(sample_artifact_id)

        assert len(revisions) == 1
        assert revisions[0].id == sample_revision_id

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_artifact_revisions_filter_by_status(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_filtering: dict[ArtifactStatus, uuid.UUID],
    ) -> None:
        """Test searching artifact revisions filtered by status returns only matching revisions"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRevisionRow.status == ArtifactStatus.AVAILABLE.value,
            ],
            orders=[],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        result_revision_ids = [revision.id for revision in result.items]
        assert sample_revisions_for_filtering[ArtifactStatus.AVAILABLE] in result_revision_ids
        assert sample_revisions_for_filtering[ArtifactStatus.SCANNED] not in result_revision_ids
        assert sample_revisions_for_filtering[ArtifactStatus.PULLING] not in result_revision_ids

    async def test_search_artifact_revisions_filter_by_artifact_id(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test searching artifact revisions filtered by artifact_id returns only revisions of that artifact"""
        target_artifact_id = sample_artifact_id
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: ArtifactRevisionRow.artifact_id == target_artifact_id,
            ],
            orders=[],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        assert result.total_count == 1
        assert result.items[0].artifact_id == sample_artifact_id

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_artifact_revisions_order_by_version_ascending(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching artifact revisions ordered by version ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ArtifactRevisionRow.version.asc()],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        result_versions = [revision.version for revision in result.items]
        assert result_versions == sorted(result_versions)
        assert result_versions[0] == "v0.1.0"
        assert result_versions[-1] == "v3.0.0"

    async def test_search_artifact_revisions_order_by_version_descending(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching artifact revisions ordered by version descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ArtifactRevisionRow.version.desc()],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        result_versions = [revision.version for revision in result.items]
        assert result_versions == sorted(result_versions, reverse=True)
        assert result_versions[0] == "v3.0.0"
        assert result_versions[-1] == "v0.1.0"

    async def test_search_artifact_revisions_order_by_size(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching artifact revisions ordered by size descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[ArtifactRevisionRow.size.desc()],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        result_sizes = [revision.size for revision in result.items if revision.size is not None]
        assert result_sizes == sorted(result_sizes, reverse=True)

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_artifact_revisions_offset_pagination_first_page(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_artifact_revisions_offset_pagination_second_page(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_artifact_revisions_offset_pagination_last_page(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_artifact_revisions_with_pagination_filter_and_order(
        self,
        artifact_repository: ArtifactRepository,
        sample_revisions_for_combined_query: list[uuid.UUID],
    ) -> None:
        """Test searching artifact revisions with pagination, filter condition, and ordering combined"""
        # Filter: only AVAILABLE revisions
        # Order: by version descending
        # Pagination: limit 3, offset 2
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=3, offset=2),
            conditions=[
                lambda: ArtifactRevisionRow.status == ArtifactStatus.AVAILABLE.value,
            ],
            orders=[ArtifactRevisionRow.version.desc()],
        )

        result = await artifact_repository.search_artifact_revisions(querier=querier)

        # Total AVAILABLE revisions: 8, so total_count should be 8
        assert result.total_count == 8
        # With limit=3, offset=2, we get items at indices 2, 3, 4 of sorted results
        assert len(result.items) == 3

        # Verify ordering is descending
        result_versions = [revision.version for revision in result.items]
        assert result_versions == sorted(result_versions, reverse=True)

        # Verify all returned items are AVAILABLE
        for revision in result.items:
            assert revision.status == ArtifactStatus.AVAILABLE

    # =========================================================================
    # Tests - Update
    # =========================================================================

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

    async def test_update_artifact_revision_digest(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test updating artifact revision digest"""
        new_digest = "abc123def456"

        updated_revision_id = await artifact_repository.update_artifact_revision_digest(
            sample_revision_id, new_digest
        )

        assert updated_revision_id == sample_revision_id

        # Verify digest was updated
        revision = await artifact_repository.get_artifact_revision_by_id(sample_revision_id)
        assert revision.digest == new_digest

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

    # =========================================================================
    # Tests - Approve/Reject/Reset
    # =========================================================================

    async def test_approve_artifact_revision(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test approving artifact revision (changing status to AVAILABLE)"""
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

    async def test_reject_artifact_revision(
        self,
        artifact_repository: ArtifactRepository,
        sample_artifact_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test rejecting artifact revision (changing status to REJECTED)"""
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

    async def test_reset_artifact_revision_status(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test resetting artifact revision status to SCANNED"""
        # First change status to something other than SCANNED
        await artifact_repository.update_artifact_revision_status(
            sample_revision_id, ArtifactStatus.PULLING
        )

        # Reset the status
        reset_revision_id = await artifact_repository.reset_artifact_revision_status(
            sample_revision_id
        )

        assert reset_revision_id == sample_revision_id

        # Verify status was reset to SCANNED
        revision = await artifact_repository.get_artifact_revision_by_id(sample_revision_id)
        assert revision.status == ArtifactStatus.SCANNED

    async def test_get_artifact_revision_readme(
        self,
        artifact_repository: ArtifactRepository,
        sample_revision_id: uuid.UUID,
    ) -> None:
        """Test getting artifact revision readme"""
        readme = await artifact_repository.get_artifact_revision_readme(sample_revision_id)

        assert readme is not None
        assert "DialoGPT-medium" in readme
