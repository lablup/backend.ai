from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.artifact.request import (
    CancelImportTaskRequest,
    CleanupRevisionsRequest,
    ImportArtifactsRequest,
    UpdateArtifactRequest,
)
from ai.backend.common.dto.manager.artifact.response import (
    ApproveRevisionResponse,
    GetRevisionDownloadProgressResponse,
    GetRevisionReadmeResponse,
    GetRevisionVerificationResultResponse,
    RejectRevisionResponse,
    UpdateArtifactResponse,
)
from ai.backend.common.dto.manager.artifact_registry import (
    ArtifactFilterInput,
    OffsetPaginationInput,
    PaginationInput,
    SearchArtifactsRequest,
    SearchArtifactsResponse,
)
from ai.backend.common.dto.manager.query import StringFilter

from .conftest import ArtifactFixtureData

STORAGE_XFAIL_REASON = (
    "Artifact processor actions require storage-proxy interaction "
    "(file download/upload/delete) which is not available in component test environment."
)


class TestUpdateArtifact:
    async def test_admin_updates_artifact(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.update_artifact(
            target_artifact.artifact_id,
            UpdateArtifactRequest(readonly=True, description="Updated description"),
        )
        assert isinstance(result, UpdateArtifactResponse)
        assert result.artifact.id == target_artifact.artifact_id
        assert result.artifact.readonly is True
        assert result.artifact.description == "Updated description"

    async def test_update_nonexistent_artifact(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        fake_id = uuid.uuid4()
        with pytest.raises(Exception):
            await admin_registry.artifact.update_artifact(
                fake_id,
                UpdateArtifactRequest(readonly=True),
            )


class TestApproveRevision:
    @pytest.mark.xfail(strict=True, reason=STORAGE_XFAIL_REASON)
    async def test_admin_approves_revision(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.approve_revision(
            target_artifact.artifact_revision_id,
        )
        assert isinstance(result, ApproveRevisionResponse)


class TestRejectRevision:
    async def test_admin_rejects_revision(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.reject_revision(
            target_artifact.artifact_revision_id,
        )
        assert isinstance(result, RejectRevisionResponse)


class TestImportArtifacts:
    @pytest.mark.xfail(strict=True, reason=STORAGE_XFAIL_REASON)
    async def test_admin_imports_artifacts(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.import_artifacts(
            ImportArtifactsRequest(
                artifact_revision_ids=[target_artifact.artifact_revision_id],
            ),
        )
        assert result is not None


class TestCancelImportTask:
    async def test_admin_cancels_import_task(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.cancel_import_task(
            CancelImportTaskRequest(
                artifact_revision_id=target_artifact.artifact_revision_id,
            ),
        )
        assert result is not None


class TestCleanupRevisions:
    @pytest.mark.xfail(strict=True, reason=STORAGE_XFAIL_REASON)
    async def test_admin_cleans_up_revisions(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.cleanup_revisions(
            CleanupRevisionsRequest(
                artifact_revision_ids=[target_artifact.artifact_revision_id],
            ),
        )
        assert result is not None


class TestGetRevisionReadme:
    async def test_admin_gets_revision_readme(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.get_revision_readme(
            target_artifact.artifact_revision_id,
        )
        assert isinstance(result, GetRevisionReadmeResponse)


class TestGetRevisionVerificationResult:
    async def test_admin_gets_verification_result(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.get_revision_verification_result(
            target_artifact.artifact_revision_id,
        )
        assert isinstance(result, GetRevisionVerificationResultResponse)


class TestGetRevisionDownloadProgress:
    async def test_admin_gets_download_progress(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        result = await admin_registry.artifact.get_revision_download_progress(
            target_artifact.artifact_revision_id,
        )
        assert isinstance(result, GetRevisionDownloadProgressResponse)


class TestSearchArtifacts:
    async def test_search_artifacts_finds_existing_artifact(
        self,
        admin_registry: BackendAIClientRegistry,
        target_artifact: ArtifactFixtureData,
    ) -> None:
        """Search artifacts → seeded artifact appears in results."""
        result = await admin_registry.artifact_registry.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=20),
                ),
            ),
        )
        assert isinstance(result, SearchArtifactsResponse)
        assert len(result.artifacts) >= 1
        artifact_ids = [a.id for a in result.artifacts]
        assert target_artifact.artifact_id in artifact_ids

    async def test_search_artifacts_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search artifacts with non-matching filter → empty list."""
        result = await admin_registry.artifact_registry.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=20),
                ),
                filters=ArtifactFilterInput(
                    name_filter=StringFilter(
                        equals="nonexistent-artifact-name-that-will-never-match"
                    ),
                ),
            ),
        )
        assert isinstance(result, SearchArtifactsResponse)
        assert result.artifacts == []
