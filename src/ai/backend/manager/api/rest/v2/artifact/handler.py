"""REST v2 handler for the artifact domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactsInput,
    DeleteArtifactsInput,
    RestoreArtifactsInput,
    UpdateArtifactInput,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    ApproveRevisionPayload,
    CancelImportTaskPayload,
    CleanupRevisionsPayload,
    RejectRevisionPayload,
    RestoreArtifactsGQLPayload,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import ArtifactIdPathParam, RevisionIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.artifact import ArtifactAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ArtifactHandler:
    """REST v2 handler for artifact operations."""

    def __init__(self, *, adapter: ArtifactAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchArtifactsInput],
    ) -> APIResponse:
        """Search artifacts with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[ArtifactIdPathParam],
    ) -> APIResponse:
        """Get a single artifact by ID."""
        result = await self._adapter.get(path.parsed.artifact_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[ArtifactIdPathParam],
        body: BodyParam[UpdateArtifactInput],
    ) -> APIResponse:
        """Update artifact metadata."""
        result = await self._adapter.update(body.parsed, path.parsed.artifact_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        body: BodyParam[DeleteArtifactsInput],
    ) -> APIResponse:
        """Delete multiple artifacts by ID."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def restore(
        self,
        body: BodyParam[RestoreArtifactsInput],
    ) -> APIResponse:
        """Restore previously deleted artifacts."""
        artifacts = await self._adapter.restore(body.parsed.artifact_ids)
        result = RestoreArtifactsGQLPayload(artifacts=artifacts)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_revision(
        self,
        path: PathParam[RevisionIdPathParam],
    ) -> APIResponse:
        """Get a single artifact revision by ID."""
        result = await self._adapter.get_revision(path.parsed.revision_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def approve_revision(
        self,
        path: PathParam[RevisionIdPathParam],
    ) -> APIResponse:
        """Approve an artifact revision."""
        revision = await self._adapter.approve_revision(path.parsed.revision_id)
        result = ApproveRevisionPayload(artifact_revision=revision)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def reject_revision(
        self,
        path: PathParam[RevisionIdPathParam],
    ) -> APIResponse:
        """Reject an artifact revision."""
        revision = await self._adapter.reject_revision(path.parsed.revision_id)
        result = RejectRevisionPayload(artifact_revision=revision)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def cancel_import(
        self,
        path: PathParam[RevisionIdPathParam],
    ) -> APIResponse:
        """Cancel an in-progress artifact import."""
        revision = await self._adapter.cancel_import(path.parsed.revision_id)
        result = CancelImportTaskPayload(artifact_revision=revision)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def cleanup_revision(
        self,
        path: PathParam[RevisionIdPathParam],
    ) -> APIResponse:
        """Clean up stored artifact revision data."""
        revision = await self._adapter.cleanup_revision(path.parsed.revision_id)
        result = CleanupRevisionsPayload(artifact_revisions=[revision])
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
