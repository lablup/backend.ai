from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp
import yarl
from dateutil.tz import tzutc

from ai.backend.common.auth.utils import generate_signature
from ai.backend.common.dto.storage.response import (
    GetVerificationResultResponse,
    VFSListFilesResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import ReservoirClientConfig, ReservoirConfig
from ai.backend.storage.errors import RegistryNotFoundError, ReservoirStorageConfigInvalidError

_HASH_TYPE = "sha256"

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ManagerHTTPClientArgs:
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str
    client_config: ReservoirClientConfig


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
    _session: aiohttp.ClientSession

    def __init__(self, registry_data: ManagerHTTPClientArgs):
        self._name = registry_data.name
        self._endpoint = registry_data.endpoint
        self._access_key = registry_data.access_key
        self._secret_key = registry_data.secret_key
        self._api_version = registry_data.api_version
        timeout = aiohttp.ClientTimeout(
            total=registry_data.client_config.timeout_total,
            connect=registry_data.client_config.timeout_connect,
            sock_connect=registry_data.client_config.timeout_sock_connect,
            sock_read=registry_data.client_config.timeout_sock_read,
        )
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self) -> None:
        """Close the HTTP client session."""
        await self._session.close()

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
        async with self._session.request(method, str(url), headers=header, **kwargs) as response:
            response.raise_for_status()
            return await response.json()

    async def _request_stream(self, method: str, rel_url: str, **kwargs) -> AsyncIterator[bytes]:
        headers = self._build_header(method=method, rel_url=rel_url)
        url = yarl.URL(self._endpoint) / rel_url.lstrip("/")

        async with self._session.request(method, str(url), headers=headers, **kwargs) as response:
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

    async def list_vfs_files(self, storage_name: str, directory: str) -> VFSListFilesResponse:
        """
        List files recursively in a VFS storage directory.

        Args:
            storage_name: Name of the VFS storage
            directory: Directory path to list files from (empty string for root)

        Returns:
            Response containing list of files with metadata
        """
        rel_url = f"/vfs-storages/{storage_name}/files"
        request_body = {"directory": directory}
        resp = await self._request("GET", rel_url, json=request_body)
        return VFSListFilesResponse.model_validate(resp)

    async def get_verification_result(
        self, artifact_revision_id: uuid.UUID
    ) -> GetVerificationResultResponse:
        """
        Get verification result for an artifact revision from the remote manager.

        Args:
            artifact_revision_id: The artifact revision ID to get verification result for

        Returns:
            GetVerificationResultResponse containing the verification result
        """
        rel_url = f"/artifacts/revisions/{artifact_revision_id}/verification-result"
        resp = await self._request("GET", rel_url)
        return GetVerificationResultResponse.model_validate(resp)


class ManagerHTTPClientPool:
    """Pool for managing ManagerHTTPClient instances per registry."""

    _registry_configs: dict[str, ReservoirConfig]
    _client_config: ReservoirClientConfig
    _clients: dict[str, ManagerHTTPClient]

    def __init__(
        self,
        registry_configs: dict[str, ReservoirConfig],
        client_config: ReservoirClientConfig,
    ) -> None:
        self._registry_configs = registry_configs
        self._client_config = client_config
        self._clients = {}

    @property
    def registry_configs(self) -> dict[str, ReservoirConfig]:
        return self._registry_configs

    def get_or_create(self, registry_name: str) -> ManagerHTTPClient:
        """
        Get or create a ManagerHTTPClient for the given registry.

        Args:
            registry_name: Name of the Reservoir registry

        Returns:
            ManagerHTTPClient instance

        Raises:
            RegistryNotFoundError: If registry configuration is not found
            ReservoirStorageConfigInvalidError: If manager connection config is incomplete
        """
        # Return cached client if exists
        if registry_name in self._clients:
            return self._clients[registry_name]

        # Validate registry configuration
        registry_config = self._registry_configs.get(registry_name)
        if not registry_config or not registry_config.endpoint:
            raise RegistryNotFoundError(
                extra_msg=f"Registry configuration not found for: {registry_name}"
            )

        if (
            not registry_config.manager_endpoint
            or not registry_config.manager_access_key
            or not registry_config.manager_secret_key
            or not registry_config.manager_api_version
        ):
            raise ReservoirStorageConfigInvalidError(
                extra_msg=f"Manager connection configuration incomplete for registry: {registry_name}"
            )

        # Create and cache new client
        manager_client = ManagerHTTPClient(
            ManagerHTTPClientArgs(
                name=registry_name,
                endpoint=registry_config.manager_endpoint,
                access_key=registry_config.manager_access_key,
                secret_key=registry_config.manager_secret_key,
                api_version=registry_config.manager_api_version,
                client_config=self._client_config,
            )
        )
        self._clients[registry_name] = manager_client
        return manager_client

    async def cleanup(self) -> None:
        """Close all manager HTTP client sessions."""
        for client in self._clients.values():
            await client.cleanup()
        self._clients.clear()
