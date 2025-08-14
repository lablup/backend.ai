from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import Optional, Self, cast

from glide import (
    Batch,
    ExpirySet,
    ExpiryType,
)

from ai.backend.common.bgtask.types import (
    BackgroundTaskMetadata,
    BackgroundTaskMetadataTTL,
    ServerType,
    TaskID,
)
from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.defs import REDIS_BGTASK_DB
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_bgtask client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_BGTASK)

_KEY_PREFIX = "bgtask"
_TASK_KEY_PREFIX = f"{_KEY_PREFIX}:task"  # bgtask:task:{task_id}
_SERVER_TYPE_KEY_PREFIX = f"{_KEY_PREFIX}:server_group"  # bgtask:server_group:{group}
_SERVER_KEY_PREFIX = f"{_KEY_PREFIX}:server"  # bgtask:server:{server_id}
_DEFAULT_TASK_METADATA_EXPIRATION = 86400  # 24 hours default expiration
_DEFAULT_EXPIRATION = 86400  # 24 hours default expiration


class ValkeyBgtaskClient:
    """
    Client for background task management operations using Valkey/Glide.
    Provides task-specific methods instead of generic Redis operations.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int = REDIS_BGTASK_DB,
        human_readable_name: str = "bgtask",
    ) -> Self:
        """
        Create a ValkeyBgtaskClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name for the client.
        """
        client = create_valkey_client(
            valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client)

    async def close(self) -> None:
        """Close the client connection."""
        if not self._closed:
            await self._client.disconnect()
            self._closed = True

    def _server_type_key(self, server_type: ServerType) -> str:
        """Key for server type task set"""
        return f"{_SERVER_TYPE_KEY_PREFIX}:{server_type}"

    def _server_id_key(self, server_id: str) -> str:
        """Key for server-specific task set"""
        return f"{_SERVER_KEY_PREFIX}:{server_id}"

    def _task_metadata_key(self, task_id: TaskID) -> str:
        """Key for individual task metadata"""
        return f"{_TASK_KEY_PREFIX}:{task_id}"

    # Task metadata operations
    @valkey_decorator()
    async def save_task_metadata(self, metadata: BackgroundTaskMetadata) -> None:
        """Save task metadata with TTL"""
        batch = self._create_batch()
        key = self._task_metadata_key(metadata.task_id)
        value = metadata.to_json()
        batch.set(key, value, expiry=ExpirySet(ExpiryType.SEC, _DEFAULT_TASK_METADATA_EXPIRATION))

        for server_type in metadata.server_types:
            server_type_key = self._server_type_key(server_type)
            batch.sadd(server_type_key, [metadata.task_id.bytes])

        server_id_key = self._server_id_key(metadata.server_id)
        batch.sadd(server_id_key, [metadata.task_id.bytes])
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def get_task_metadata(self, task_id: TaskID) -> Optional[BackgroundTaskMetadataTTL]:
        """Get task metadata by ID"""
        batch = self._create_batch()
        key = self._task_metadata_key(task_id)
        batch.get(key)
        batch.ttl(key)
        results = await self._client.client.exec(batch, raise_on_error=True)
        if results is None:
            return None
        data, ttl_seconds = results
        if data is None:
            return None
        data = cast(bytes, data)
        ttl_seconds = cast(int, ttl_seconds)
        ttl_seconds = ttl_seconds if ttl_seconds >= 0 else _DEFAULT_TASK_METADATA_EXPIRATION
        matadata = BackgroundTaskMetadata.from_json(data)
        return BackgroundTaskMetadataTTL(matadata, ttl_seconds)

    @valkey_decorator()
    async def get_task_metadata_batch(
        self, task_ids: Sequence[TaskID]
    ) -> dict[TaskID, BackgroundTaskMetadataTTL]:
        """Get task metadata"""
        task_metadata_dict: dict[TaskID, BackgroundTaskMetadataTTL] = {}
        batch = self._create_batch()
        keys = [self._task_metadata_key(task_id) for task_id in task_ids]
        for key in keys:
            batch.get(key)
            batch.ttl(key)
        raw_results = await self._client.client.exec(batch, raise_on_error=True)
        if raw_results is None:
            return task_metadata_dict
        results = cast(list[tuple[Optional[bytes], int]], raw_results)
        for data, ttl_seconds in results:
            if data is None:
                continue
            data = cast(bytes, data)
            ttl_seconds = ttl_seconds if ttl_seconds >= 0 else _DEFAULT_TASK_METADATA_EXPIRATION
            metadata = BackgroundTaskMetadata.from_json(data)
            task_metadata_dict[metadata.task_id] = BackgroundTaskMetadataTTL(metadata, ttl_seconds)
        return task_metadata_dict

    @valkey_decorator()
    async def delete_task(self, metadata: BackgroundTaskMetadata) -> None:
        """Delete task metadata"""
        batch = self._create_batch()
        key = self._task_metadata_key(metadata.task_id)
        batch.delete([key])

        for server_type in metadata.server_types:
            server_type_key = self._server_type_key(server_type)
            batch.srem(server_type_key, [metadata.task_id.bytes])

        server_id_key = self._server_id_key(metadata.server_id)
        batch.srem(server_id_key, [metadata.task_id.bytes])
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def get_task_ids_by_server_type(self, server_type: ServerType) -> set[TaskID]:
        """Get task IDs for a specific server type"""
        group_key = self._server_type_key(server_type)
        raw_task_ids = await self._client.client.smembers(group_key)
        return {TaskID.from_encoded(raw_id) for raw_id in raw_task_ids}

    @valkey_decorator()
    async def get_task_ids_by_server_id(self, server_id: str) -> set[TaskID]:
        """Get task IDs for a specific server ID"""
        server_key = self._server_id_key(server_id)
        raw_task_ids = await self._client.client.smembers(server_key)
        return {TaskID.from_encoded(raw_id) for raw_id in raw_task_ids}

    @valkey_decorator()
    async def set_heartbeats(self, task_ids: Iterable[TaskID]) -> None:
        """Set heartbeat data with TTL"""
        batch = self._create_batch()
        keys = [self._task_metadata_key(task_id) for task_id in task_ids]
        for key in keys:
            batch.expire(key, _DEFAULT_TASK_METADATA_EXPIRATION)
        await self._client.client.exec(batch, raise_on_error=True)

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch object for batch operations.

        :param is_atomic: Whether the batch should be atomic (transaction-like).
        :return: A Batch object.
        """
        return Batch(is_atomic=is_atomic)
