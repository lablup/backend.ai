from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.artifact.request import (
    CancelImportTaskRequest,
    CleanupRevisionsRequest,
    ImportArtifactsRequest,
)
from ai.backend.common.dto.manager.artifact.response import (
    CancelImportTaskResponse,
    GetRevisionDownloadProgressResponse,
    GetRevisionReadmeResponse,
)
from ai.backend.common.dto.manager.artifact_registry.request import (
    OffsetPaginationInput,
    PaginationInput,
    SearchArtifactsRequest,
)
from ai.backend.common.dto.manager.artifact_registry.response import (
    SearchArtifactsResponse,
)

from .conftest import RevisionFactory, RevisionFixtureData

STORAGE_XFAIL_REASON = (
    "Artifact revision import/cleanup requires storage-proxy interaction "
    "(file download/upload/delete) which is not available in component test environment."
)


class TestArtifactRevisionScanPhase:
    """Verify scanned artifacts are discoverable via search (scan phase of lifecycle)."""

    async def test_scanned_artifact_appears_in_search(
        self,
        admin_registry: BackendAIClientRegistry,
        target_revision: RevisionFixtureData,
    ) -> None:
        result = await admin_registry.artifact_registry.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=100),
                ),
            ),
        )
        assert isinstance(result, SearchArtifactsResponse)
        artifact_ids = {a.id for a in result.artifacts}
        assert target_revision.artifact_id in artifact_ids


class TestArtifactRevisionImportPhase:
    """Test import operations (most require storage-proxy)."""

    @pytest.mark.xfail(strict=True, reason=STORAGE_XFAIL_REASON)
    async def test_import_artifact_revision(
        self,
        admin_registry: BackendAIClientRegistry,
        target_revision: RevisionFixtureData,
    ) -> None:
        await admin_registry.artifact.import_artifacts(
            ImportArtifactsRequest(
                artifact_revision_ids=[target_revision.artifact_revision_id],
            ),
        )

    async def test_cancel_import_task(
        self,
        admin_registry: BackendAIClientRegistry,
        target_revision: RevisionFixtureData,
    ) -> None:
        result = await admin_registry.artifact.cancel_import_task(
            CancelImportTaskRequest(
                artifact_revision_id=target_revision.artifact_revision_id,
            ),
        )
        assert isinstance(result, CancelImportTaskResponse)


class TestArtifactRevisionQueryPhase:
    """Test revision query operations that work without storage."""

    async def test_get_revision_readme(
        self,
        admin_registry: BackendAIClientRegistry,
        target_revision: RevisionFixtureData,
    ) -> None:
        result = await admin_registry.artifact.get_revision_readme(
            target_revision.artifact_revision_id,
        )
        assert isinstance(result, GetRevisionReadmeResponse)

    async def test_get_download_progress(
        self,
        admin_registry: BackendAIClientRegistry,
        target_revision: RevisionFixtureData,
    ) -> None:
        result = await admin_registry.artifact.get_revision_download_progress(
            target_revision.artifact_revision_id,
        )
        assert isinstance(result, GetRevisionDownloadProgressResponse)


class TestArtifactRevisionCleanupPhase:
    """Test cleanup operations (requires storage-proxy)."""

    @pytest.mark.xfail(strict=True, reason=STORAGE_XFAIL_REASON)
    async def test_cleanup_revisions(
        self,
        admin_registry: BackendAIClientRegistry,
        target_revision: RevisionFixtureData,
    ) -> None:
        await admin_registry.artifact.cleanup_revisions(
            CleanupRevisionsRequest(
                artifact_revision_ids=[target_revision.artifact_revision_id],
            ),
        )


class TestArtifactRevisionLifecycleMultiple:
    """Test lifecycle with multiple revisions."""

    async def test_multiple_revisions_appear_in_search(
        self,
        admin_registry: BackendAIClientRegistry,
        revision_factory: RevisionFactory,
    ) -> None:
        """Create multiple artifacts and verify they all appear in search."""
        rev1 = await revision_factory(name="lifecycle-model-1")
        rev2 = await revision_factory(name="lifecycle-model-2")

        result = await admin_registry.artifact_registry.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=100),
                ),
            ),
        )
        artifact_ids = {a.id for a in result.artifacts}
        assert rev1.artifact_id in artifact_ids
        assert rev2.artifact_id in artifact_ids
