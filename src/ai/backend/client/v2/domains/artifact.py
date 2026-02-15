from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.artifact import (
    ApproveRevisionResponse,
    CancelImportTaskRequest,
    CancelImportTaskResponse,
    CleanupRevisionsRequest,
    CleanupRevisionsResponse,
    GetRevisionDownloadProgressResponse,
    GetRevisionReadmeResponse,
    GetRevisionVerificationResultResponse,
    ImportArtifactsRequest,
    ImportArtifactsResponse,
    RejectRevisionResponse,
    UpdateArtifactRequest,
    UpdateArtifactResponse,
)


class ArtifactClient(BaseDomainClient):
    API_PREFIX = "/artifacts"

    # ---------------------------------------------------------------------------
    # Artifact operations
    # ---------------------------------------------------------------------------

    async def import_artifacts(
        self,
        request: ImportArtifactsRequest,
    ) -> ImportArtifactsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/import",
            request=request,
            response_model=ImportArtifactsResponse,
        )

    async def update_artifact(
        self,
        artifact_id: uuid.UUID,
        request: UpdateArtifactRequest,
    ) -> UpdateArtifactResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{self.API_PREFIX}/{artifact_id}",
            request=request,
            response_model=UpdateArtifactResponse,
        )

    async def cancel_import_task(
        self,
        request: CancelImportTaskRequest,
    ) -> CancelImportTaskResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/task/cancel",
            request=request,
            response_model=CancelImportTaskResponse,
        )

    # ---------------------------------------------------------------------------
    # Revision operations
    # ---------------------------------------------------------------------------

    async def cleanup_revisions(
        self,
        request: CleanupRevisionsRequest,
    ) -> CleanupRevisionsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/revisions/cleanup",
            request=request,
            response_model=CleanupRevisionsResponse,
        )

    async def approve_revision(
        self,
        artifact_revision_id: uuid.UUID,
    ) -> ApproveRevisionResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/revisions/{artifact_revision_id}/approval",
            response_model=ApproveRevisionResponse,
        )

    async def reject_revision(
        self,
        artifact_revision_id: uuid.UUID,
    ) -> RejectRevisionResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/revisions/{artifact_revision_id}/rejection",
            response_model=RejectRevisionResponse,
        )

    # ---------------------------------------------------------------------------
    # Revision queries
    # ---------------------------------------------------------------------------

    async def get_revision_readme(
        self,
        artifact_revision_id: uuid.UUID,
    ) -> GetRevisionReadmeResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/revisions/{artifact_revision_id}/readme",
            response_model=GetRevisionReadmeResponse,
        )

    async def get_revision_verification_result(
        self,
        artifact_revision_id: uuid.UUID,
    ) -> GetRevisionVerificationResultResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/revisions/{artifact_revision_id}/verification-result",
            response_model=GetRevisionVerificationResultResponse,
        )

    async def get_revision_download_progress(
        self,
        artifact_revision_id: uuid.UUID,
    ) -> GetRevisionDownloadProgressResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/revisions/{artifact_revision_id}/download-progress",
            response_model=GetRevisionDownloadProgressResponse,
        )
