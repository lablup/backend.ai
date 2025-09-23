from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    APIStreamResponse,
    BodyParam,
    PathParam,
    api_handler,
    stream_api_handler,
)
from ai.backend.common.dto.storage.context import MultipartUploadCtx
from ai.backend.common.dto.storage.request import (
    VFSDeleteFileReq,
    VFSDownloadFileReq,
    VFSGetFileMetaReq,
    VFSStorageAPIPathParams,
    VFSUploadFileReq,
)
from ai.backend.common.dto.storage.response import (
    VFSDeleteResponse,
    VFSUploadResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.types import MultipartFileUploadStreamReader

from ....services.storages.vfs_storage import VFSStorageService
from ....utils import log_client_api_entry

if TYPE_CHECKING:
    from ....context import RootContext

_DEFAULT_CONTENT_TYPE: Final[str] = "application/octet-stream"

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFSStorageAPIHandler:
    """
    HTTP API handler for VFS storage operations.
    Provides endpoints similar to object storage but for filesystem-based storage.
    """

    _vfs_service: VFSStorageService

    def __init__(
        self,
        vfs_service: VFSStorageService,
    ) -> None:
        self._vfs_service = vfs_service

    @api_handler
    async def upload_file(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSUploadFileReq],
        multipart_ctx: MultipartUploadCtx,
    ) -> APIResponse:
        """
        Upload a file to VFS storage using multipart form data.

        The file should be uploaded as a multipart form with a 'file' field.
        Supports streaming upload to handle large files efficiently.
        """
        req = body.parsed
        filepath = req.filepath
        content_type = req.content_type
        file_reader = multipart_ctx.file_reader
        storage_name = path.parsed.storage_name

        await log_client_api_entry(log, "upload_file", req)

        upload_stream = MultipartFileUploadStreamReader(file_reader, content_type)
        await self._vfs_service.stream_upload(storage_name, filepath, upload_stream)

        return APIResponse.build(
            status_code=HTTPStatus.CREATED,
            response_model=VFSUploadResponse(
                filepath=filepath,
            ),
        )

    @stream_api_handler
    async def download_file(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSDownloadFileReq],
    ) -> APIStreamResponse:
        """
        Download a file from VFS storage using streaming.
        Streams file content directly to the client without loading into memory.
        """
        req = body.parsed
        filepath = req.filepath
        storage_name = path.parsed.storage_name

        await log_client_api_entry(log, "download_file", req)
        file_stream = await self._vfs_service.stream_download(storage_name, filepath)

        # Get file metadata for content type
        try:
            meta = await self._vfs_service.get_file_meta(storage_name, filepath)
            content_type = meta.content_type or _DEFAULT_CONTENT_TYPE
        except Exception:
            content_type = _DEFAULT_CONTENT_TYPE

        return APIStreamResponse(
            body=file_stream,
            status=HTTPStatus.OK,
            headers={
                "Content-Type": content_type,
            },
        )

    @api_handler
    async def get_file_meta(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSGetFileMetaReq],
    ) -> APIResponse:
        """
        Get metadata information about a file in VFS storage.
        Returns file size, content type, modification time, and other metadata.
        """
        req = body.parsed
        filepath = req.filepath
        storage_name = path.parsed.storage_name

        await log_client_api_entry(log, "get_file_meta", req)

        response = await self._vfs_service.get_file_meta(storage_name, filepath)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def delete_file(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSDeleteFileReq],
    ) -> APIResponse:
        """
        Delete a file or directory from VFS storage.
        Supports recursive deletion for directories.
        """
        req = body.parsed
        filepath = req.filepath
        storage_name = path.parsed.storage_name

        await log_client_api_entry(log, "delete_file", req)

        await self._vfs_service.delete_file(storage_name, filepath)

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=VFSDeleteResponse(
                filepath=filepath,
            ),
        )


def create_app(ctx: RootContext) -> web.Application:
    """
    Create the VFS storage API application with all routes configured.

    Args:
        ctx: Root context containing storage pool and configuration

    Returns:
        Configured aiohttp Application for VFS storage API
    """
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/storages/vfs"

    vfs_service = VFSStorageService(ctx.storage_pool)
    api_handler = VFSStorageAPIHandler(
        vfs_service=vfs_service,
    )

    # File operations
    app.router.add_route("GET", "/{storage_name}/meta", api_handler.get_file_meta)
    app.router.add_route("DELETE", "/{storage_name}", api_handler.delete_file)
    app.router.add_route("POST", "/{storage_name}/upload", api_handler.upload_file)
    app.router.add_route("POST", "/{storage_name}/download", api_handler.download_file)

    return app
