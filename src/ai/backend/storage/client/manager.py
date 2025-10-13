from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import aiohttp

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ManagerHTTPClient:
    """
    HTTP client for communicating with Backend.AI Manager APIs from storage services.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key

    async def download_vfs_file_streaming(
        self, storage_name: str, filepath: str
    ) -> AsyncIterator[bytes]:
        """
        Download a file from VFS storage via manager API streaming.

        Args:
            storage_name: Name of the VFS storage
            filepath: Path to the file to download

        Yields:
            Chunks of file content as bytes
        """
        url = f"{self.endpoint}/vfs-storage/{storage_name}/download"

        # Create request body
        request_body = {"filepath": filepath}

        # Basic headers - in a real implementation you'd add authentication
        headers = {
            "Content-Type": "application/json",
        }

        # TODO: Add proper authentication headers using access_key/secret_key

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=request_body) as response:
                    response.raise_for_status()

                    # Stream the response content in chunks
                    chunk_size = 8192  # 8KB chunks
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if chunk:
                            yield chunk

            except aiohttp.ClientError as e:
                log.error(f"HTTP error downloading VFS file {filepath}: {str(e)}")
                raise
            except Exception as e:
                log.error(f"Unexpected error downloading VFS file {filepath}: {str(e)}")
                raise
