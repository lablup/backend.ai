"""V2 REST SDK client for the artifact resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactsInput,
    DeleteArtifactsInput,
    RestoreArtifactsInput,
    UpdateArtifactInput,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    AdminSearchArtifactsPayload,
    ApproveRevisionPayload,
    ArtifactNode,
    ArtifactRevisionNode,
    CancelImportTaskPayload,
    CleanupRevisionsPayload,
    DeleteArtifactsPayload,
    RejectRevisionPayload,
    RestoreArtifactsGQLPayload,
    UpdateArtifactPayload,
)

_PATH = "/v2/artifacts"


class V2ArtifactClient(BaseDomainClient):
    """SDK client for ``/v2/artifacts`` endpoints."""

    async def admin_search(
        self,
        request: AdminSearchArtifactsInput,
    ) -> AdminSearchArtifactsPayload:
        """Search artifacts with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchArtifactsPayload,
        )

    async def get(self, artifact_id: UUID) -> ArtifactNode:
        """Get a single artifact by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{artifact_id}",
            response_model=ArtifactNode,
        )

    async def update(
        self,
        artifact_id: UUID,
        request: UpdateArtifactInput,
    ) -> UpdateArtifactPayload:
        """Update artifact metadata."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{artifact_id}",
            request=request,
            response_model=UpdateArtifactPayload,
        )

    async def delete(
        self,
        request: DeleteArtifactsInput,
    ) -> DeleteArtifactsPayload:
        """Delete multiple artifacts by ID."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteArtifactsPayload,
        )

    async def restore(
        self,
        request: RestoreArtifactsInput,
    ) -> RestoreArtifactsGQLPayload:
        """Restore previously deleted artifacts."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/restore",
            request=request,
            response_model=RestoreArtifactsGQLPayload,
        )

    async def get_revision(self, revision_id: UUID) -> ArtifactRevisionNode:
        """Get a single artifact revision by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/revisions/{revision_id}",
            response_model=ArtifactRevisionNode,
        )

    async def approve_revision(self, revision_id: UUID) -> ApproveRevisionPayload:
        """Approve an artifact revision."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/revisions/{revision_id}/approve",
            response_model=ApproveRevisionPayload,
        )

    async def reject_revision(self, revision_id: UUID) -> RejectRevisionPayload:
        """Reject an artifact revision."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/revisions/{revision_id}/reject",
            response_model=RejectRevisionPayload,
        )

    async def cancel_import(self, revision_id: UUID) -> CancelImportTaskPayload:
        """Cancel an in-progress artifact import."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/revisions/{revision_id}/cancel-import",
            response_model=CancelImportTaskPayload,
        )

    async def cleanup_revision(self, revision_id: UUID) -> CleanupRevisionsPayload:
        """Clean up stored artifact revision data."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/revisions/{revision_id}/cleanup",
            response_model=CleanupRevisionsPayload,
        )
