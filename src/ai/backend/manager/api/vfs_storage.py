from __future__ import annotations

import logging
import mimetypes
from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import (
    APIStreamResponse,
    BodyParam,
    PathParam,
    stream_api_handler,
)
from ai.backend.common.dto.base import BaseResponseModel
from ai.backend.common.dto.storage.request import VFSDownloadFileReq, VFSStorageAPIPathParams
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import ProcessorsCtx

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFSDownloadResponse(BaseResponseModel):
    """Response model for VFS download operations."""

    message: str
    storage_name: str
    file_path: str


class VFSErrorResponse(BaseResponseModel):
    """Error response model for VFS operations."""

    error: str


class APIHandler:
    @auth_required_for_method
    @stream_api_handler
    async def download_file(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSDownloadFileReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIStreamResponse:
        """
        Download a file from VFS storage via storage proxy streaming.

        Args:
            path: Path parameters including storage name
            body: Request body with file path
            processors_ctx: Processing context

        Returns:
            APIStreamResponse: Streaming file content
        """
        req = body.parsed
        filepath = req.filepath
        storage_name = path.parsed.storage_name

        try:
            # 1. Get storage_manager from proper context ✅
            storage_manager = processors_ctx.storage_manager

            # TODO: 2. Map storage_name to proxy_name based on VFS storage configuration
            # For now, we'll use the first available proxy
            proxy_name = next(iter(storage_manager._manager_facing_clients.keys()))

            # 3. Get the manager_client using storage_manager ✅
            manager_client = storage_manager.get_manager_facing_client(proxy_name)

            # 4. Use the client to stream download from storage proxy ✅
            async with manager_client.download_vfs_file_streaming(storage_name, req) as resp:
                if resp.status != HTTPStatus.OK:
                    error_text = await resp.text()
                    log.error(f"Storage proxy VFS download failed: {error_text}")
                    raise Exception(f"Storage proxy VFS download failed: {error_text}")

                # Determine content type
                content_type = resp.headers.get("Content-Type", "application/octet-stream")
                if not content_type or content_type == "application/octet-stream":
                    guessed_type, _ = mimetypes.guess_type(filepath)
                    content_type = guessed_type or "application/octet-stream"

                # Create a streaming response that reads from storage proxy response
                async def stream_generator():
                    chunk_size = 8192  # 8KB chunks
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        yield chunk

                return APIStreamResponse(
                    body=stream_generator(),
                    status=HTTPStatus.OK,
                    headers={
                        "Content-Type": content_type,
                    },
                )

        except Exception as e:
            log.error(f"Unexpected error downloading VFS file '{filepath}': {str(e)}")

            # For streaming responses, we can't return an APIResponse error
            # Instead, we need to return an error stream
            async def error_generator():
                error_msg = f"Error downloading file: {str(e)}"
                yield error_msg.encode("utf-8")

            return APIStreamResponse(
                body=error_generator(),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                headers={
                    "Content-Type": "text/plain",
                },
            )


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    """Initialize VFS storage API handlers."""
    app = web.Application()
    app["api_versions"] = (1,)
    app["prefix"] = "vfs-storage"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = APIHandler()

    cors.add(app.router.add_route("POST", "/{storage_name}/download", api_handler.download_file))

    return app, []
