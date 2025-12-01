from __future__ import annotations

import logging
import uuid
from typing import Optional, Self, TypeVar

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.data.storage.types import (
    ArtifactStorageStatefulData,
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

_EXPIRATION = 60 * 60 * 24  # 24 hours

T = TypeVar("T", bound=ArtifactStorageStatefulData)


class ValkeyArtifactStorageClient:
    """
    Client for caching artifact storage information using Valkey.

    This client uses Redis hash structure for better scalability:
    - Hash key: artifact_storages.{type}
    - Hash field: {storage_id}
    - Hash value: JSON serialized storage data

    This allows efficient operations like HGETALL to retrieve all storages of a type.
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

    def _make_hash_key(self, storage_type: ArtifactStorageType) -> str:
        """
        Generate a hash key for artifact storage type.

        :param storage_type: The type of storage.
        :return: The formatted hash key.
        """
        return f"artifact_storages.{storage_type.value}"

    async def _set_storage(
        self,
        storage_type: ArtifactStorageType,
        storage_id: uuid.UUID,
        storage_data: ArtifactStorageStatefulData,
    ) -> None:
        """
        Generic method to cache storage data using hash structure.

        :param storage_type: The type of storage.
        :param storage_id: The UUID of the storage.
        :param storage_data: The storage data to cache.
        """
        hash_key = self._make_hash_key(storage_type)
        field = str(storage_id)
        value = dump_json_str(storage_data.to_dict())
        await self._client.client.hset(hash_key, {field: value})
        await self._client.client.expire(hash_key, _EXPIRATION)
        log.debug("Cached {} data for storage_id={}", storage_type.value, storage_id)

    async def _get_storage(
        self,
        storage_type: ArtifactStorageType,
        storage_id: uuid.UUID,
        data_class: type[T],
    ) -> Optional[T]:
        """
        Generic method to get cached storage data using hash structure.

        :param storage_type: The type of storage.
        :param storage_id: The UUID of the storage.
        :param data_class: The data class to deserialize into.
        :return: The cached storage data or None if not found.
        """
        hash_key = self._make_hash_key(storage_type)
        field = str(storage_id)
        value = await self._client.client.hget(hash_key, field)
        if value is None:
            log.debug("Cache miss for {} with storage_id={}", storage_type.value, storage_id)
            return None

        json_value = value.decode()
        data = load_json(json_value)
        return data_class.from_dict(data)

    async def _delete_storage(
        self,
        storage_type: ArtifactStorageType,
        storage_id: uuid.UUID,
    ) -> bool:
        """
        Generic method to delete cached storage data using hash structure.

        :param storage_type: The type of storage.
        :param storage_id: The UUID of the storage.
        :return: True if the field was deleted, False otherwise.
        """
        hash_key = self._make_hash_key(storage_type)
        field = str(storage_id)
        result = await self._client.client.hdel(hash_key, [field])
        deleted = result > 0
        if deleted:
            log.debug("Deleted cached {} data for storage_id={}", storage_type.value, storage_id)
        return deleted

    async def _get_all_storages(
        self,
        storage_type: ArtifactStorageType,
        data_class: type[T],
    ) -> dict[uuid.UUID, T]:
        """
        Get all cached storages of a specific type.

        :param storage_type: The type of storage.
        :param data_class: The data class to deserialize into.
        :return: Dictionary mapping storage IDs to storage data.
        """
        hash_key = self._make_hash_key(storage_type)
        all_values = await self._client.client.hgetall(hash_key)
        if not all_values:
            return {}

        result: dict[uuid.UUID, T] = {}
        for field_bytes, value_bytes in all_values.items():
            storage_id = uuid.UUID(field_bytes.decode())
            json_value = value_bytes.decode()
            data = load_json(json_value)
            result[storage_id] = data_class.from_dict(data)

        log.debug("Retrieved {} cached {} entries", len(result), storage_type.value)
        return result

    @valkey_artifact_storages_resilience.apply()
    async def set_object_storage(
        self,
        storage_id: uuid.UUID,
        storage_data: ObjectStorageStatefulData,
    ) -> None:
        """
        Cache object storage data.

        :param storage_id: The UUID of the object storage.
        :param storage_data: The storage data to cache.
        """
        await self._set_storage(ArtifactStorageType.OBJECT_STORAGE, storage_id, storage_data)

    @valkey_artifact_storages_resilience.apply()
    async def get_object_storage(
        self,
        storage_id: uuid.UUID,
    ) -> Optional[ObjectStorageStatefulData]:
        """
        Get cached object storage data.

        :param storage_id: The UUID of the object storage.
        :return: The cached storage data or None if not found.
        """
        return await self._get_storage(
            ArtifactStorageType.OBJECT_STORAGE, storage_id, ObjectStorageStatefulData
        )

    @valkey_artifact_storages_resilience.apply()
    async def get_all_object_storages(self) -> dict[uuid.UUID, ObjectStorageStatefulData]:
        """
        Get all cached object storage data.

        :return: Dictionary mapping storage IDs to storage data.
        """
        return await self._get_all_storages(
            ArtifactStorageType.OBJECT_STORAGE, ObjectStorageStatefulData
        )

    @valkey_artifact_storages_resilience.apply()
    async def delete_object_storage(
        self,
        storage_id: uuid.UUID,
    ) -> bool:
        """
        Delete cached object storage data.

        :param storage_id: The UUID of the object storage.
        :return: True if the field was deleted, False otherwise.
        """
        return await self._delete_storage(ArtifactStorageType.OBJECT_STORAGE, storage_id)

    @valkey_artifact_storages_resilience.apply()
    async def set_vfs_storage(
        self,
        storage_id: uuid.UUID,
        storage_data: VFSStorageStatefulData,
    ) -> None:
        """
        Cache VFS storage data.

        :param storage_id: The UUID of the VFS storage.
        :param storage_data: The storage data to cache.
        """
        await self._set_storage(ArtifactStorageType.VFS_STORAGE, storage_id, storage_data)

    @valkey_artifact_storages_resilience.apply()
    async def get_vfs_storage(
        self,
        storage_id: uuid.UUID,
    ) -> Optional[VFSStorageStatefulData]:
        """
        Get cached VFS storage data.

        :param storage_id: The UUID of the VFS storage.
        :return: The cached storage data or None if not found.
        """
        return await self._get_storage(
            ArtifactStorageType.VFS_STORAGE, storage_id, VFSStorageStatefulData
        )

    @valkey_artifact_storages_resilience.apply()
    async def get_all_vfs_storages(self) -> dict[uuid.UUID, VFSStorageStatefulData]:
        """
        Get all cached VFS storage data.

        :return: Dictionary mapping storage IDs to storage data.
        """
        return await self._get_all_storages(ArtifactStorageType.VFS_STORAGE, VFSStorageStatefulData)

    @valkey_artifact_storages_resilience.apply()
    async def delete_vfs_storage(
        self,
        storage_id: uuid.UUID,
    ) -> bool:
        """
        Delete cached VFS storage data.

        :param storage_id: The UUID of the VFS storage.
        :return: True if the field was deleted, False otherwise.
        """
        return await self._delete_storage(ArtifactStorageType.VFS_STORAGE, storage_id)

    @valkey_artifact_storages_resilience.apply()
    async def flush_database(self) -> None:
        """
        Flush all keys in the current database.
        """
        await self._client.client.flushdb()
