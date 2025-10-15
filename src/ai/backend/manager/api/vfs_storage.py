from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from http import HTTPStatus
from typing import Iterable, Optional, Tuple, cast, override

import aiohttp_cors
from aiohttp import ClientResponse, web

from ai.backend.common.api_handlers import (
    APIResponse,
    APIStreamResponse,
    BodyParam,
    PathParam,
    api_handler,
    stream_api_handler,
)
from ai.backend.common.dto.storage.request import (
    VFSDownloadFileReq,
    VFSListFilesReq,
    VFSStorageAPIPathParams,
)
from ai.backend.common.types import StreamReader
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.dto.context import ProcessorsCtx, StorageSessionManagerCtx
from ai.backend.manager.dto.response import (
    GetVFSStorageResponse,
    ListVFSStorageResponse,
    VFSStorage,
)
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.list import ListVFSStorageAction

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFSDirectoryDownloadProxyStreamReader(StreamReader):
    """StreamReader implementation for VFS file downloads from storage proxy."""

    def __init__(
        self,
        storage_proxy_client: StorageProxyManagerFacingClient,
        storage_name: str,
        req: VFSDownloadFileReq,
        filepath: str,
    ):
        self._storage_proxy_client = storage_proxy_client
        self._storage_name = storage_name
        self._req = req
        self._filepath = filepath

    @override
    def content_type(self) -> Optional[str]:
        return "application/x-tar"

    @override
    async def read(self) -> AsyncIterator[bytes]:
        """Stream file content from storage proxy."""
        # Use the context manager to get response from storage proxy
        async with self._storage_proxy_client.download_vfs_file_streaming(
            self._storage_name, self._req
        ) as resp:
            resp.raise_for_status()

            # Stream content directly
            async for chunk in self._stream_content(resp):
                yield chunk

    async def _stream_content(self, resp: ClientResponse) -> AsyncIterator[bytes]:
        """Stream content directly without saving."""
        chunk_size = 8192  # 8KB chunks
        bytes_streamed = 0

        async for chunk in resp.content.iter_chunked(chunk_size):
            if chunk:
                bytes_streamed += len(chunk)
                yield chunk

        log.debug(f"Successfully streamed {self._filepath}: {bytes_streamed} bytes")


class APIHandler:
    @auth_required_for_method
    @stream_api_handler
    async def download_file(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSDownloadFileReq],
        storage_session_manager_ctx: StorageSessionManagerCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIStreamResponse:
        """
        Download artifact directory from VFS storage via storage proxy streaming.

        Args:
            path: Path parameters including storage name
            body: Request body with file path

        Returns:
            APIStreamResponse with StreamReader body
        """
        req = body.parsed
        filepath = req.filepath
        storage_name = path.parsed.storage_name

        log.info(f"Download request for file: {filepath} from storage: {storage_name}")

        # Get storage manager from context
        storage_manager = storage_session_manager_ctx.storage_manager
        action_result = await processors_ctx.processors.vfs_storage.get.wait_for_complete(
            GetVFSStorageAction(storage_name=storage_name)
        )

        # Get the manager client for the proxy
        manager_client = storage_manager.get_manager_facing_client(action_result.result.host)

        # Create stream reader for the download
        stream_reader = VFSDirectoryDownloadProxyStreamReader(
            storage_proxy_client=manager_client,
            storage_name=storage_name,
            req=req,
            filepath=filepath,
        )

        # Prepare response headers
        filename = os.path.basename(filepath)
        content_type = cast(str, stream_reader.content_type())
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        }

        return APIStreamResponse(
            body=stream_reader,
            status=HTTPStatus.OK,
            headers=headers,
        )

    @auth_required_for_method
    @api_handler
    async def get_storage(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """
        Get VFS storage information by storage name.

        Args:
            path: Path parameters including storage name

        Returns:
            APIResponse with storage information
        """
        storage_name = path.parsed.storage_name

        log.info(f"Get storage request for storage: {storage_name}")

        processors = processors_ctx.processors

        action_result = await processors.vfs_storage.get.wait_for_complete(
            GetVFSStorageAction(storage_name=storage_name)
        )

        storage_data = action_result.result
        response = GetVFSStorageResponse(
            storage=VFSStorage(
                name=storage_data.name,
                host=storage_data.host,
                base_path=str(storage_data.base_path),
            )
        )

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=response)

    @auth_required_for_method
    @api_handler
    async def list_storages(
        self,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """
        List all VFS storages.

        Returns:
            APIResponse with storage information
        """
        log.info("List all VFS storages.")

        processors = processors_ctx.processors

        action_result = await processors.vfs_storage.list_storages.wait_for_complete(
            ListVFSStorageAction()
        )

        storage_data = action_result
        response = ListVFSStorageResponse(
            storages=[
                VFSStorage(
                    name=data.name,
                    host=data.host,
                    base_path=str(data.base_path),
                )
                for data in storage_data.data
            ]
        )

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=response)

    @auth_required_for_method
    @api_handler
    async def list_files(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSListFilesReq],
        storage_session_manager_ctx: StorageSessionManagerCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """
        List files recursively in a VFS storage directory via storage proxy.

        Args:
            path: Path parameters including storage name
            body: Request body with directory path

        Returns:
            APIResponse with list of files
        """
        req = body.parsed
        directory = req.directory
        storage_name = path.parsed.storage_name

        log.info(f"List files request for directory: {directory} from storage: {storage_name}")

        # Get storage manager from context
        storage_manager = storage_session_manager_ctx.storage_manager
        action_result = await processors_ctx.processors.vfs_storage.get.wait_for_complete(
            GetVFSStorageAction(storage_name=storage_name)
        )

        # Get the manager client for the proxy
        manager_client = storage_manager.get_manager_facing_client(action_result.result.host)

        # Call storage proxy list files API
        response_data = await manager_client.list_vfs_files(storage_name, req)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=response_data)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    """Initialize VFS storage API handlers."""
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "vfs-storages"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()

    cors.add(app.router.add_route("POST", "/{storage_name}/download", api_handler.download_file))
    cors.add(app.router.add_route("GET", "/{storage_name}/files", api_handler.list_files))
    cors.add(app.router.add_route("GET", "/{storage_name}", api_handler.get_storage))
    cors.add(app.router.add_route("GET", "/", api_handler.list_storages))
    return app, []
