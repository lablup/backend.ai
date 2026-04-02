"""V2 REST SDK client for the VFolder resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateUploadSessionInput,
    CreateVFolderInput,
    SearchVFoldersInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CreateUploadSessionPayload,
    CreateVFolderPayload,
    SearchVFoldersPayload,
)

_PATH = "/v2/vfolders"


class V2VFolderClient(BaseDomainClient):
    """SDK client for ``/v2/vfolders`` endpoints."""

    async def project_search(
        self,
        project_id: UUID,
        request: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search vfolders within a project."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/{project_id}/search",
            request=request,
            response_model=SearchVFoldersPayload,
        )

    async def create(self, request: CreateVFolderInput) -> CreateVFolderPayload:
        """Create a new vfolder."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateVFolderPayload,
        )

    async def create_upload_session(
        self,
        vfolder_id: UUID,
        request: CreateUploadSessionInput,
    ) -> CreateUploadSessionPayload:
        """Create an upload session for a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/upload-session",
            request=request,
            response_model=CreateUploadSessionPayload,
        )
