from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp
import yarl
from dateutil.tz import tzutc

from ai.backend.common.auth.utils import generate_signature
from ai.backend.logging import BraceStyleAdapter

_HASH_TYPE = "sha256"

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ManagerHTTPClientArgs:
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str


# TODO: Remove this and reconstruct to request storage proxy directly.
class ManagerHTTPClient:
    """
    HTTP client for communicating with Backend.AI Manager APIs from storage services.
    """

    _name: str
    _endpoint: str
    _access_key: str
    _secret_key: str
    _api_version: str

    def __init__(self, registry_data: ManagerHTTPClientArgs):
        self._name = registry_data.name
        self._endpoint = registry_data.endpoint
        self._access_key = registry_data.access_key
        self._secret_key = registry_data.secret_key
        self._api_version = registry_data.api_version

    def _build_header(self, method: str, rel_url: str) -> Mapping[str, str]:
        date = datetime.now(tzutc())
        hdrs, _ = generate_signature(
            method=method,
            version=self._api_version,
            endpoint=yarl.URL(self._endpoint),
            date=date,
            rel_url=rel_url,
            content_type="application/json",
            access_key=self._access_key,
            secret_key=self._secret_key,
            hash_type=_HASH_TYPE,
        )

        return {
            "User-Agent": "Backend.AI Manager facing storage-proxy client",
            "Content-Type": "application/json",
            "X-BackendAI-Version": self._api_version,
            "Date": date.isoformat(),
            **hdrs,
        }

    async def _request(self, method: str, rel_url: str, **kwargs) -> Any:
        header = self._build_header(method=method, rel_url=rel_url)
        url = yarl.URL(self._endpoint) / rel_url.lstrip("/")
        async with aiohttp.ClientSession() as session:
            async with session.request(method, str(url), headers=header, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def _request_stream(self, method: str, rel_url: str, **kwargs) -> AsyncIterator[bytes]:
        headers = self._build_header(method=method, rel_url=rel_url)
        url = yarl.URL(self._endpoint) / rel_url.lstrip("/")

        async with aiohttp.ClientSession() as session:
            async with session.request(method, str(url), headers=headers, **kwargs) as response:
                response.raise_for_status()

                # Stream the response content in chunks
                chunk_size = 8192  # 8KB chunks
                async for chunk in response.content.iter_chunked(chunk_size):
                    if chunk:
                        yield chunk

    async def download_vfs_file_streaming(
        self, storage_name: str, filepath: str
    ) -> AsyncIterator[bytes]:
        """
        Download a directory from VFS storage via manager API streaming.

        Args:
            storage_name: Name of the VFS storage
            filepath: Path to the file to download

        Yields:
            Chunks of file content as bytes
        """
        rel_url = f"/vfs-storages/{storage_name}/download"
        request_body = {"filepath": filepath}
        async for chunk in self._request_stream("POST", rel_url, json=request_body):
            yield chunk
