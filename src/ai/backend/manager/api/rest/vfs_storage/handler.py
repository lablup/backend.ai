"""VFS storage handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from http import HTTPStatus
from pathlib import Path
from typing import Final, cast, override

from aiohttp import ClientResponse

from ai.backend.common.api_handlers import APIResponse, APIStreamResponse, BodyParam, PathParam
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
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.response import (
    GetVFSStorageResponse,
    ListVFSStorageResponse,
    VFSStorage,
)
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.list import ListVFSStorageAction

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFSDirectoryDownloadProxyStreamReader(StreamReader):
    """StreamReader implementation for VFS file downloads from storage proxy."""

    def __init__(
        self,
        storage_proxy_client: StorageProxyManagerFacingClient,
        storage_name: str,
        req: VFSDownloadFileReq,
        filepath: str,
    ) -> None:
        self._storage_proxy_client = storage_proxy_client
        self._storage_name = storage_name
        self._req = req
        self._filepath = filepath

    @override
    def content_type(self) -> str | None:
        return "application/x-tar"

    @override
    async def read(self) -> AsyncIterator[bytes]:
        """Stream file content from storage proxy."""
        async with self._storage_proxy_client.download_vfs_file_streaming(
            self._storage_name, self._req
        ) as resp:
            resp.raise_for_status()
            async for chunk in self._stream_content(resp):
                yield chunk

    async def _stream_content(self, resp: object) -> AsyncIterator[bytes]:
        """Stream content directly without saving."""
        typed_resp = cast(ClientResponse, resp)
        chunk_size = 8192  # 8KB chunks
        bytes_streamed = 0

        async for chunk in typed_resp.content.iter_chunked(chunk_size):
            if chunk:
                bytes_streamed += len(chunk)
                yield chunk

        log.debug("Successfully streamed {}: {} bytes", self._filepath, bytes_streamed)


class VFSStorageHandler:
    """VFS storage API handler with constructor-injected dependencies."""

    async def download_file(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSDownloadFileReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIStreamResponse:
        """Download artifact directory from VFS storage via storage proxy streaming."""
        req = body.parsed
        filepath = req.filepath
        storage_name = path.parsed.storage_name

        log.info("Download request for file: {} from storage: {}", filepath, storage_name)

        vfs_processors = processors_ctx.processors.vfs_storage
        action_result = await vfs_processors.get.wait_for_complete(
            GetVFSStorageAction(storage_name=storage_name)
        )

        manager_client = vfs_processors.get_manager_facing_client(action_result.result.host)

        stream_reader = VFSDirectoryDownloadProxyStreamReader(
            storage_proxy_client=manager_client,
            storage_name=storage_name,
            req=req,
            filepath=filepath,
        )

        filename = Path(filepath).name
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

    async def get_storage(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get VFS storage information by storage name."""
        storage_name = path.parsed.storage_name

        log.info("Get storage request for storage: {}", storage_name)

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

    async def list_storages(
        self,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """List all VFS storages."""
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

    async def list_files(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSListFilesReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """List files recursively in a VFS storage directory via storage proxy."""
        req = body.parsed
        directory = req.directory
        storage_name = path.parsed.storage_name

        log.info("List files request for directory: {} from storage: {}", directory, storage_name)

        vfs_processors = processors_ctx.processors.vfs_storage
        action_result = await vfs_processors.get.wait_for_complete(
            GetVFSStorageAction(storage_name=storage_name)
        )

        manager_client = vfs_processors.get_manager_facing_client(action_result.result.host)

        response_data = await manager_client.list_vfs_files(storage_name, req)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=response_data)
