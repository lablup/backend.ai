"""V2 REST SDK client for the artifact resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactsInput,
    DeleteArtifactsInput,
    PartialBulkDeleteArtifactsInput,
    PartialBulkRestoreArtifactsInput,
    PartialBulkUpdateArtifactsInput,
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
    DeleteArtifactPayload,
    DeleteArtifactsPayload,
    RejectRevisionPayload,
    RestoreArtifactPayload,
    RestoreArtifactsGQLPayload,
    UpdateArtifactPayload,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload

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

    async def delete(self, artifact_id: UUID) -> DeleteArtifactPayload:
        """Soft-delete an artifact."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{artifact_id}/delete",
            response_model=DeleteArtifactPayload,
        )

    async def restore(self, artifact_id: UUID) -> RestoreArtifactPayload:
        """Restore a soft-deleted artifact."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{artifact_id}/restore",
            response_model=RestoreArtifactPayload,
        )

    async def partial_bulk_update(
        self, request: PartialBulkUpdateArtifactsInput
    ) -> PartialBulkPayload[ArtifactNode]:
        """Update several artifacts, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[ArtifactNode],
        )

    async def partial_bulk_delete(
        self, request: PartialBulkDeleteArtifactsInput
    ) -> PartialBulkPayload[ArtifactNode]:
        """Soft-delete several artifacts, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-delete",
            request=request,
            response_model=PartialBulkPayload[ArtifactNode],
        )

    async def partial_bulk_restore(
        self, request: PartialBulkRestoreArtifactsInput
    ) -> PartialBulkPayload[ArtifactNode]:
        """Restore several soft-deleted artifacts, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-restore",
            request=request,
            response_model=PartialBulkPayload[ArtifactNode],
        )

    async def delete_artifacts(
        self,
        request: DeleteArtifactsInput,
    ) -> DeleteArtifactsPayload:
        """Deprecated. Use :meth:`partial_bulk_delete`."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteArtifactsPayload,
        )

    async def restore_artifacts(
        self,
        request: RestoreArtifactsInput,
    ) -> RestoreArtifactsGQLPayload:
        """Deprecated. Use :meth:`partial_bulk_restore`."""
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
