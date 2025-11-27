from __future__ import annotations

import dataclasses
import logging
import uuid
from typing import Optional, Self

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.data.storage.types import (
    ArtifactStorageType,
    ObjectStorageStatefulData,
    VFSStorageStatefulData,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    BackoffStrategy,
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Resilience instance for valkey_artifact_storages layer
valkey_artifact_storages_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_ARTIFACT_STORAGES)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)

_DEFAULT_CACHE_EXPIRATION = 60 * 60  # 1 hour


class ValkeyArtifactStorageClient:
    """
    Client for caching artifact storage information using Valkey.

    This client caches storage data like object storage and VFS storage configurations
    using keys in the format: artifact_storages.{type}.{storage_name}
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
    ) -> Self:
        """
        Create a ValkeyArtifactStorageClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name of the client.
        :return: An instance of ValkeyArtifactStorageClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_artifact_storages_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeyArtifactStorageClient connection.
        """
        if self._closed:
            log.debug("ValkeyArtifactStorageClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    async def ping(self) -> None:
        """Ping the Valkey server to check connection health."""
        await self._client.ping()

    def _make_storage_key(self, storage_type: ArtifactStorageType, storage_name: str) -> str:
        """
        Generate a cache key for artifact storage.

        :param storage_type: The type of storage.
        :param storage_name: The name of the storage.
        :return: The formatted cache key.
        """
        return f"artifact_storages.{storage_type.value}.{storage_name}"

    @valkey_artifact_storages_resilience.apply()
    async def set_object_storage(
        self,
        storage_name: str,
        storage_data: ObjectStorageStatefulData,
        expiration: int = _DEFAULT_CACHE_EXPIRATION,
    ) -> None:
        """
        Cache object storage data.

        :param storage_name: The name of the object storage.
        :param storage_data: The storage data to cache.
        :param expiration: The cache expiration time in seconds.
        """
        key = self._make_storage_key(ArtifactStorageType.OBJECT_STORAGE, storage_name)
        value = dump_json_str(dataclasses.asdict(storage_data))
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expiration),
        )
        log.debug("Cached object storage data for {}", storage_name)

    @valkey_artifact_storages_resilience.apply()
    async def get_object_storage(
        self,
        storage_name: str,
    ) -> Optional[ObjectStorageStatefulData]:
        """
        Get cached object storage data.

        :param storage_name: The name of the object storage.
        :return: The cached storage data or None if not found.
        """
        key = self._make_storage_key(ArtifactStorageType.OBJECT_STORAGE, storage_name)
        value = await self._client.client.get(key)
        if value is None:
            log.debug("Cache miss for object storage {}", storage_name)
            return None

        json_value = value.decode()
        data = load_json(json_value)
        # Convert UUID string back to UUID object
        if "id" in data and isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        return ObjectStorageStatefulData(**data)

    @valkey_artifact_storages_resilience.apply()
    async def delete_object_storage(
        self,
        storage_name: str,
    ) -> bool:
        """
        Delete cached object storage data.

        :param storage_name: The name of the object storage.
        :return: True if the key was deleted, False otherwise.
        """
        key = self._make_storage_key(ArtifactStorageType.OBJECT_STORAGE, storage_name)
        result = await self._client.client.delete([key])
        deleted = result > 0
        if deleted:
            log.debug("Deleted cached object storage data for {}", storage_name)
        return deleted

    @valkey_artifact_storages_resilience.apply()
    async def set_vfs_storage(
        self,
        storage_name: str,
        storage_data: VFSStorageStatefulData,
        expiration: int = _DEFAULT_CACHE_EXPIRATION,
    ) -> None:
        """
        Cache VFS storage data.

        :param storage_name: The name of the VFS storage.
        :param storage_data: The storage data to cache.
        :param expiration: The cache expiration time in seconds.
        """
        key = self._make_storage_key(ArtifactStorageType.VFS_STORAGE, storage_name)
        # Convert Path to string for JSON serialization
        data_dict = dataclasses.asdict(storage_data)
        data_dict["base_path"] = str(data_dict["base_path"])
        value = dump_json_str(data_dict)
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expiration),
        )
        log.debug("Cached VFS storage data for {}", storage_name)

    @valkey_artifact_storages_resilience.apply()
    async def get_vfs_storage(
        self,
        storage_name: str,
    ) -> Optional[VFSStorageStatefulData]:
        """
        Get cached VFS storage data.

        :param storage_name: The name of the VFS storage.
        :return: The cached storage data or None if not found.
        """
        key = self._make_storage_key(ArtifactStorageType.VFS_STORAGE, storage_name)
        value = await self._client.client.get(key)
        if value is None:
            log.debug("Cache miss for VFS storage {}", storage_name)
            return None

        json_value = value.decode()
        data = load_json(json_value)
        # Convert UUID string back to UUID object and string back to Path
        if "id" in data and isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        if "base_path" in data and isinstance(data["base_path"], str):
            from pathlib import Path

            data["base_path"] = Path(data["base_path"])
        return VFSStorageStatefulData(**data)

    @valkey_artifact_storages_resilience.apply()
    async def delete_vfs_storage(
        self,
        storage_name: str,
    ) -> bool:
        """
        Delete cached VFS storage data.

        :param storage_name: The name of the VFS storage.
        :return: True if the key was deleted, False otherwise.
        """
        key = self._make_storage_key(ArtifactStorageType.VFS_STORAGE, storage_name)
        result = await self._client.client.delete([key])
        deleted = result > 0
        if deleted:
            log.debug("Deleted cached VFS storage data for {}", storage_name)
        return deleted

    @valkey_artifact_storages_resilience.apply()
    async def flush_database(self) -> None:
        """
        Flush all keys in the current database.
        """
        await self._client.client.flushdb()
