from __future__ import annotations

import asyncio
import logging
import mimetypes
import os
import tarfile
import tempfile
from collections.abc import AsyncIterator
from http import HTTPStatus
from pathlib import Path
from typing import Iterable, Optional, Tuple

import aiofiles
import aiofiles.os
import aiohttp
import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import (
    APIStreamResponse,
    BodyParam,
    PathParam,
    stream_api_handler,
)
from ai.backend.common.dto.storage.request import VFSDownloadFileReq, VFSStorageAPIPathParams
from ai.backend.common.types import StreamReader
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.dto.context import StorageSessionManagerCtx

from .auth import auth_required_for_method
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFSFileDownloadClientStreamReader(StreamReader):
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
        self._content_type: Optional[str] = None
        self._guessed_content_type: Optional[str] = None
        self._temp_file: Optional[Path] = None

        # Guess content type from filepath
        guessed_type, _ = mimetypes.guess_type(filepath)
        self._guessed_content_type = guessed_type

    def content_type(self) -> Optional[str]:
        """Return the content type for this download."""
        # Return actual content type from response if available,
        # otherwise return guessed type
        return self._content_type or self._guessed_content_type or "application/octet-stream"

    async def read(self) -> AsyncIterator[bytes]:
        """Stream file content from storage proxy."""
        try:
            # Use the context manager to get response from storage proxy
            async with self._storage_proxy_client.download_vfs_file_streaming(
                self._storage_name, self._req
            ) as resp:
                # Check response status
                if resp.status != 200:
                    error_text = await resp.text()
                    log.error(
                        f"Storage proxy error for {self._filepath}: {resp.status} - {error_text}"
                    )
                    yield f"Error: Storage proxy returned {resp.status}: {error_text}".encode(
                        "utf-8"
                    )
                    return

                # Get actual content type from response
                self._content_type = resp.headers.get("Content-Type", self._guessed_content_type)

                # Check if this is a tar file
                is_tar_file = (
                    self._filepath.endswith(".tar") or self._content_type == "application/x-tar"
                )

                if is_tar_file:
                    # Stream to temp file first, then extract
                    yield await self._download_and_extract_tar(resp)
                else:
                    # Normal streaming without extraction
                    async for chunk in self._stream_content(resp):
                        yield chunk

        except Exception as e:
            # Error setting up the connection
            log.error(f"Failed to initialize streaming for {self._filepath}: {e}", exc_info=True)
            yield f"Error: Failed to download file: {str(e)}".encode("utf-8")

    async def _stream_content(self, resp) -> AsyncIterator[bytes]:
        """Stream content directly without saving."""
        chunk_size = 8192  # 8KB chunks
        bytes_streamed = 0

        try:
            async for chunk in resp.content.iter_chunked(chunk_size):
                if chunk:
                    bytes_streamed += len(chunk)
                    yield chunk

            log.debug(f"Successfully streamed {self._filepath}: {bytes_streamed} bytes")

        except (
            aiohttp.ClientPayloadError,
            aiohttp.ClientConnectionError,
            ConnectionResetError,
            BrokenPipeError,
        ) as e:
            # Client disconnected during streaming - this is expected behavior
            log.debug(
                f"Client disconnected while streaming {self._filepath}: {type(e).__name__}: {e}"
            )
            return

        except Exception as e:
            # Unexpected error during streaming
            log.error(f"Unexpected error streaming {self._filepath}: {e}", exc_info=True)
            raise

    async def _download_and_extract_tar(self, resp) -> bytes:
        """Download tar file to temp location and extract it to temp directory."""
        loop = asyncio.get_running_loop()

        try:
            # Get system temp directory (works on macOS and Linux)
            temp_dir = Path(tempfile.gettempdir())

            # Create temporary file for the tar archive
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".tar", dir=temp_dir
            ) as temp_file:
                self._temp_file = Path(temp_file.name)
                log.debug(f"Downloading tar to temp file: {self._temp_file}")

                # Download entire tar file to temp location
                chunk_size = 8192
                bytes_downloaded = 0

                async with aiofiles.open(self._temp_file, "wb") as f:
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        if chunk:
                            await f.write(chunk)
                            bytes_downloaded += len(chunk)

                log.debug(f"Downloaded {bytes_downloaded} bytes to {self._temp_file}")

                # Extract tar archive to the directory of filepath
                extract_dir = Path(self._filepath).parent

                # Extract tar archive in executor to avoid blocking
                await loop.run_in_executor(
                    None, self._extract_tar_archive, str(self._temp_file), str(extract_dir)
                )

                # Return success message as bytes
                return f"Successfully extracted tar archive to {extract_dir}".encode("utf-8")

        finally:
            # Clean up temp file
            if self._temp_file and self._temp_file.exists():
                try:
                    await aiofiles.os.remove(self._temp_file)
                    log.debug(f"Cleaned up temp file: {self._temp_file}")
                except Exception as e:
                    log.warning(f"Failed to remove temp file {self._temp_file}: {e}")

    def _extract_tar_archive(self, tar_path: str, target_dir: str) -> None:
        """Extract tar archive to target directory."""
        try:
            log.debug(f"Extracting tar archive: {tar_path} -> {target_dir}")

            # Ensure target directory exists
            Path(target_dir).mkdir(parents=True, exist_ok=True)

            with tarfile.open(tar_path, "r") as tar:
                # Extract all files to target directory
                tar.extractall(path=target_dir)

            log.debug(f"Tar archive extracted successfully to: {target_dir}")
        except Exception as e:
            log.error(f"Failed to extract tar archive: {e}")
            raise


class VFSErrorStreamReader(StreamReader):
    """StreamReader implementation for error responses."""

    def __init__(self, error_message: str, status_code: int = 500):
        self._error_message = error_message
        self._status_code = status_code

    def content_type(self) -> Optional[str]:
        """Return plain text content type for error messages."""
        return "text/plain; charset=utf-8"

    async def read(self) -> AsyncIterator[bytes]:
        """Yield error message as bytes."""
        yield self._error_message.encode("utf-8")


class APIHandler:
    @auth_required_for_method
    @stream_api_handler
    async def download_file(
        self,
        path: PathParam[VFSStorageAPIPathParams],
        body: BodyParam[VFSDownloadFileReq],
        storage_session_manager_ctx: StorageSessionManagerCtx,
    ) -> APIStreamResponse:
        """
        Download a file from VFS storage via storage proxy streaming.

        Args:
            path: Path parameters including storage name
            body: Request body with file path
            processors_ctx: Processing context

        Returns:
            APIStreamResponse with StreamReader body
        """
        req = body.parsed
        filepath = req.filepath
        storage_name = path.parsed.storage_name

        log.info(f"Download request for file: {filepath} from storage: {storage_name}")

        try:
            # Get storage manager from context
            storage_manager = storage_session_manager_ctx.storage_manager

            # TODO: Map storage_name to proxy_name based on VFS storage configuration
            # For now, use the first available proxy
            proxy_name = next(iter(storage_manager._manager_facing_clients.keys()))

            # Get the manager client for the proxy
            manager_client = storage_manager.get_manager_facing_client(proxy_name)

            # Create stream reader for the download
            stream_reader = VFSFileDownloadClientStreamReader(
                storage_proxy_client=manager_client,
                storage_name=storage_name,
                req=req,
                filepath=filepath,
            )

            # Prepare response headers
            filename = os.path.basename(filepath)
            headers = {
                "Content-Type": stream_reader.content_type(),
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            }

            return APIStreamResponse(
                body=stream_reader,
                status=HTTPStatus.OK,
                headers=headers,
            )

        except KeyError as e:
            error_msg = f"No storage proxy available: {str(e)}"
            log.error(error_msg)

            return APIStreamResponse(
                body=VFSErrorStreamReader(error_msg),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                headers={"Content-Type": "text/plain; charset=utf-8"},
            )

        except Exception as e:
            error_msg = f"Failed to initialize download for '{filepath}': {str(e)}"
            log.error(error_msg, exc_info=True)

            return APIStreamResponse(
                body=VFSErrorStreamReader(error_msg),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                headers={"Content-Type": "text/plain; charset=utf-8"},
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
