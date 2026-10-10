"""V2 REST SDK client for the VFolder resource."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import aiohttp
from aiotusclient import client as tus
from yarl import URL

from ai.backend.client.config import DEFAULT_CHUNK_SIZE
from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.client.v2.exceptions import map_status_to_exception
from ai.backend.common.dto.manager.v2.vfolder.request import (
    BulkDeleteVFoldersInput,
    BulkPurgeVFoldersInput,
    CloneVFolderInput,
    CreateDownloadSessionInput,
    CreateUploadSessionInput,
    CreateVFolderInput,
    CreateVFolderInScopeInput,
    DeleteFilesInput,
    DeployVFolderInput,
    ListFilesInput,
    MkdirInput,
    MoveFileInput,
    PurgeVFolderInput,
    SearchVFoldersInput,
    SetVFolderMountPolicyInput,
    UnsetVFolderMountPolicyInput,
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
    RestoreVFolderPayload,
    SearchVFoldersPayload,
    SetVFolderMountPolicyPayload,
    UnsetVFolderMountPolicyPayload,
    VFolderMountPoliciesPayload,
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

    async def create_in_project(
        self,
        project_id: UUID,
        request: CreateVFolderInScopeInput,
    ) -> CreateVFolderPayload:
        """Create a vfolder owned by ``project_id``."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/{project_id}/create",
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

    async def upload_file(
        self,
        vfolder_id: UUID,
        file_path: Path,
        *,
        dst_path: str | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        """Create an upload session and stream the file to it over TUS."""
        request = CreateUploadSessionInput(
            path=dst_path or file_path.name, size=file_path.stat().st_size
        )
        session = await self.create_upload_session(vfolder_id, request)
        url = URL(session.url).with_query({"token": session.token})
        with file_path.open("rb") as stream:
            uploader = tus.TusClient().async_uploader(
                file_stream=stream,
                url=str(url),
                upload_checksum=False,
                chunk_size=chunk_size,
            )
            await uploader.upload()

    async def download_file(
        self,
        vfolder_id: UUID,
        path: str,
        dest: Path,
        *,
        archive: bool = False,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        """Create a download session and stream its content into ``dest``."""
        request = CreateDownloadSessionInput(path=path, archive=archive)
        session = await self.create_download_session(vfolder_id, request)
        url = URL(session.url).with_query({"token": session.token})
        # ponytail: one GET, no resume; add Range retries if large downloads flake.
        async with aiohttp.ClientSession() as http, http.get(url) as resp:
            if resp.status >= 400:
                raise map_status_to_exception(resp.status, resp.reason or "", await resp.text())
            with dest.open("wb") as f:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    f.write(chunk)

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

    async def purge(
        self,
        vfolder_id: UUID,
        request: PurgeVFolderInput | None = None,
    ) -> PurgeVFolderPayload:
        """Permanently delete a vfolder, optionally cascading linked model cards."""
        if request is None:
            request = PurgeVFolderInput()
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/purge",
            request=request,
            response_model=PurgeVFolderPayload,
        )

    async def restore(self, vfolder_id: UUID) -> RestoreVFolderPayload:
        """Restore a trashed vfolder."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{vfolder_id}/restore",
            response_model=RestoreVFolderPayload,
        )

    async def set_mount_policy(
        self, vfolder_id: UUID, request: SetVFolderMountPolicyInput
    ) -> SetVFolderMountPolicyPayload:
        """Set the mount level one user gets on the vfolder."""
        return await self._client.typed_request(
            "PUT",
            f"{_PATH}/{vfolder_id}/mount-policies",
            request=request,
            response_model=SetVFolderMountPolicyPayload,
        )

    async def unset_mount_policy(
        self, vfolder_id: UUID, request: UnsetVFolderMountPolicyInput
    ) -> UnsetVFolderMountPolicyPayload:
        """Take back the mount level one user was given on the vfolder."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{vfolder_id}/mount-policies/{request.user_id}",
            response_model=UnsetVFolderMountPolicyPayload,
        )

    async def list_mount_policies(self, vfolder_id: UUID) -> VFolderMountPoliciesPayload:
        """The mount levels set on the vfolder, one row per user."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{vfolder_id}/mount-policies",
            response_model=VFolderMountPoliciesPayload,
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
