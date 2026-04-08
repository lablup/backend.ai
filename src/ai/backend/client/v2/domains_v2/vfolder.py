"""V2 REST SDK client for the VFolder resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.vfolder.request import (
    BulkDeleteVFoldersInput,
    BulkPurgeVFoldersInput,
    CloneVFolderInput,
    CreateDownloadSessionInput,
    CreateUploadSessionInput,
    CreateVFolderInput,
    DeleteFilesInput,
    DeployVFolderInput,
    ListFilesInput,
    MkdirInput,
    MoveFileInput,
    SearchVFoldersInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    BulkDeleteVFoldersPayload,
    BulkPurgeVFoldersPayload,
    CloneVFolderPayload,
    CreateDownloadSessionPayload,
    CreateUploadSessionPayload,
    CreateVFolderPayload,
    DeleteFilesPayload,
    DeleteVFolderPayload,
    DeployVFolderPayload,
    ListFilesPayload,
    MkdirPayload,
    MoveFilePayload,
    PurgeVFolderPayload,
    SearchVFoldersPayload,
    VFolderNode,
)

_PATH = "/v2/vfolders"


class V2VFolderClient(BaseDomainClient):
    """SDK client for ``/v2/vfolders`` endpoints."""

    async def my_search(
        self,
        request: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search vfolders owned by the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=SearchVFoldersPayload,
        )

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

    async def admin_search(
        self,
        request: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search all vfolders (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchVFoldersPayload,
        )

    async def get(self, vfolder_id: UUID) -> VFolderNode:
        """Get a vfolder by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{vfolder_id}",
            response_model=VFolderNode,
        )

    async def delete(self, vfolder_id: UUID) -> DeleteVFolderPayload:
        """Soft-delete a vfolder."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{vfolder_id}",
            response_model=DeleteVFolderPayload,
        )

    async def purge(self, vfolder_id: UUID) -> PurgeVFolderPayload:
        """Permanently delete a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/purge",
            response_model=PurgeVFolderPayload,
        )

    async def deploy(
        self,
        vfolder_id: UUID,
        request: DeployVFolderInput,
    ) -> DeployVFolderPayload:
        """Deploy a deployment directly from a model VFolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/deploy",
            request=request,
            response_model=DeployVFolderPayload,
        )

    async def list_files(
        self,
        vfolder_id: UUID,
        request: ListFilesInput,
    ) -> ListFilesPayload:
        """List files in a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/files/list",
            request=request,
            response_model=ListFilesPayload,
        )

    async def mkdir(
        self,
        vfolder_id: UUID,
        request: MkdirInput,
    ) -> MkdirPayload:
        """Create a directory in a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/files/mkdir",
            request=request,
            response_model=MkdirPayload,
        )

    async def move_file(
        self,
        vfolder_id: UUID,
        request: MoveFileInput,
    ) -> MoveFilePayload:
        """Move a file within a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/files/move",
            request=request,
            response_model=MoveFilePayload,
        )

    async def delete_files(
        self,
        vfolder_id: UUID,
        request: DeleteFilesInput,
    ) -> DeleteFilesPayload:
        """Delete files in a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/files/delete",
            request=request,
            response_model=DeleteFilesPayload,
        )

    async def create_download_session(
        self,
        vfolder_id: UUID,
        request: CreateDownloadSessionInput,
    ) -> CreateDownloadSessionPayload:
        """Create a download session for a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/download-session",
            request=request,
            response_model=CreateDownloadSessionPayload,
        )

    async def clone(
        self,
        vfolder_id: UUID,
        request: CloneVFolderInput,
    ) -> CloneVFolderPayload:
        """Clone a vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/clone",
            request=request,
            response_model=CloneVFolderPayload,
        )

    async def bulk_delete(
        self,
        request: BulkDeleteVFoldersInput,
    ) -> BulkDeleteVFoldersPayload:
        """Soft-delete multiple vfolders."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=BulkDeleteVFoldersPayload,
        )

    async def bulk_purge(
        self,
        request: BulkPurgeVFoldersInput,
    ) -> BulkPurgeVFoldersPayload:
        """Permanently purge multiple vfolders."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/purge",
            request=request,
            response_model=BulkPurgeVFoldersPayload,
        )
