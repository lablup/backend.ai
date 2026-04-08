"""REST v2 handlers for the VFolder domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
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
from ai.backend.manager.api.rest.v2.path_params import ProjectIdPathParam, VFolderIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.vfolder import VFolderAdapter


class V2VFolderHandler:
    """REST v2 handler for VFolder endpoints."""

    def __init__(self, *, adapter: VFolderAdapter) -> None:
        self._adapter = adapter

    async def my_search(
        self,
        body: BodyParam[SearchVFoldersInput],
    ) -> APIResponse:
        """Search vfolders owned by the current user."""
        result = await self._adapter.my_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def project_search(
        self,
        path: PathParam[ProjectIdPathParam],
        body: BodyParam[SearchVFoldersInput],
    ) -> APIResponse:
        """Search vfolders within a project."""
        result = await self._adapter.project_search(path.parsed.project_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def create(
        self,
        body: BodyParam[CreateVFolderInput],
    ) -> APIResponse:
        """Create a new vfolder."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def create_upload_session(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[CreateUploadSessionInput],
    ) -> APIResponse:
        """Create an upload session for a vfolder."""
        result = await self._adapter.create_upload_session(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchVFoldersInput],
    ) -> APIResponse:
        """Search all vfolders (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[VFolderIdPathParam],
    ) -> APIResponse:
        """Get a vfolder by ID."""
        result = await self._adapter.get(path.parsed.vfolder_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        path: PathParam[VFolderIdPathParam],
    ) -> APIResponse:
        """Soft-delete a vfolder."""
        result = await self._adapter.delete(path.parsed.vfolder_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[VFolderIdPathParam],
    ) -> APIResponse:
        """Permanently delete a vfolder."""
        result = await self._adapter.purge(path.parsed.vfolder_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def deploy(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[DeployVFolderInput],
    ) -> APIResponse:
        """Deploy a deployment directly from a model VFolder."""
        result = await self._adapter.deploy(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def list_files(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[ListFilesInput],
    ) -> APIResponse:
        """List files in a vfolder."""
        result = await self._adapter.list_files(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def mkdir(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[MkdirInput],
    ) -> APIResponse:
        """Create a directory in a vfolder."""
        result = await self._adapter.mkdir(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def move_file(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[MoveFileInput],
    ) -> APIResponse:
        """Move a file within a vfolder."""
        result = await self._adapter.move_file(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_files(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[DeleteFilesInput],
    ) -> APIResponse:
        """Delete files in a vfolder."""
        result = await self._adapter.delete_files(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def create_download_session(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[CreateDownloadSessionInput],
    ) -> APIResponse:
        """Create a download session for a vfolder."""
        result = await self._adapter.create_download_session(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def clone(
        self,
        path: PathParam[VFolderIdPathParam],
        body: BodyParam[CloneVFolderInput],
    ) -> APIResponse:
        """Clone a vfolder."""
        result = await self._adapter.clone(path.parsed.vfolder_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def bulk_delete(
        self,
        body: BodyParam[BulkDeleteVFoldersInput],
    ) -> APIResponse:
        """Soft-delete multiple vfolders."""
        result = await self._adapter.bulk_delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_purge(
        self,
        body: BodyParam[BulkPurgeVFoldersInput],
    ) -> APIResponse:
        """Permanently purge multiple vfolders."""
        result = await self._adapter.bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
