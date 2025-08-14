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
    TTL_SECOND,
    BackgroundTaskMetadata,
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

    def _get_server_type_key(self, server_type: ServerType) -> str:
        """Get key for server type task set"""
        return f"{_SERVER_TYPE_KEY_PREFIX}:{server_type}"

    def _get_server_key(self, server_id: str) -> str:
        """Get key for server-specific task set"""
        return f"{_SERVER_KEY_PREFIX}:{server_id}"

    def _get_task_key(self, task_id: TaskID) -> str:
        """Get key for individual task metadata"""
        return f"{_TASK_KEY_PREFIX}:{task_id}"

    # Task metadata operations
    @valkey_decorator()
    async def register_task(self, metadata: BackgroundTaskMetadata) -> None:
        """
        Save background task metadata to Valkey with automatic expiration.

        This method performs three operations atomically:
        1. Stores the task metadata JSON with a 24-hour TTL
        2. Adds the task ID to server type sets for task discovery by type
        3. Adds the task ID to the server-specific set for server-level tracking

        Args:
            metadata: The background task metadata containing task ID, server info,
                    and task configuration

        Note:
            - Task metadata automatically expires after 24 hours unless refreshed
            - Tasks are indexed by both server type and server ID for efficient lookup
            - All operations are executed as an atomic batch to ensure consistency
        """
        batch = self._create_batch()
        key = self._get_task_key(metadata.task_id)
        value = metadata.to_json()
        batch.set(key, value, expiry=ExpirySet(ExpiryType.SEC, _DEFAULT_TASK_METADATA_EXPIRATION))

        for server_type in metadata.server_types:
            server_type_key = self._get_server_type_key(server_type)
            batch.sadd(server_type_key, [metadata.task_id.bytes])

        server_key = self._get_server_key(metadata.server_id)
        batch.sadd(server_key, [metadata.task_id.bytes])
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def get_task(
        self, task_id: TaskID
    ) -> Optional[tuple[BackgroundTaskMetadata, TTL_SECOND]]:
        """
        Retrieve background task metadata with remaining TTL information.

        Fetches both the task metadata and its remaining time-to-live in a single
        atomic operation to ensure consistency between data and expiration status.

        Args:
            task_id: Unique identifier of the background task

        Returns:
            The task metadata and TTL in seconds,
            or None if the task doesn't exist or has expired

        Note:
            - TTL is returned as seconds remaining until expiration
            - Expired tasks (TTL < 0) are treated as having default TTL for consistency
        """
        batch = self._create_batch()
        key = self._get_task_key(task_id)
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
        return (matadata, ttl_seconds)

    @valkey_decorator()
    async def get_tasks(
        self, task_ids: Sequence[TaskID]
    ) -> dict[TaskID, tuple[BackgroundTaskMetadata, TTL_SECOND]]:
        """
        Retrieve metadata for multiple background tasks in a single batch operation.

        Efficiently fetches metadata and TTL information for multiple tasks using
        pipelined commands to minimize network round-trips.

        Args:
            task_ids: Sequence of task IDs to retrieve metadata for

        Returns:
            Dictionary mapping task IDs to their metadata with TTL information.
            Missing or expired tasks are excluded from the result.

        Note:
            - Uses batch operations for optimal performance with large task sets
            - Non-existent tasks are silently omitted from the result
            - Results maintain order correspondence with input task IDs
        """
        task_metadata_dict: dict[TaskID, tuple[BackgroundTaskMetadata, TTL_SECOND]] = {}
        batch = self._create_batch()
        keys = [self._get_task_key(task_id) for task_id in task_ids]
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
            task_metadata_dict[metadata.task_id] = (metadata, ttl_seconds)
        return task_metadata_dict

    @valkey_decorator()
    async def unregister_task(self, metadata: BackgroundTaskMetadata) -> None:
        """
        Remove a background task and clean up all its references.

        Performs complete cleanup by:
        1. Deleting the task metadata key
        2. Removing task ID from all associated server type sets
        3. Removing task ID from the server-specific set

        Args:
            metadata: The task metadata containing the task ID and server associations
                    to be cleaned up

        Note:
            - All cleanup operations are atomic to prevent partial deletion
            - Removes task from all index sets to prevent orphaned references
            - Safe to call even if task is already deleted (idempotent)
        """
        batch = self._create_batch()
        key = self._get_task_key(metadata.task_id)
        batch.delete([key])

        for server_type in metadata.server_types:
            server_type_key = self._get_server_type_key(server_type)
            batch.srem(server_type_key, [metadata.task_id.bytes])

        server_key = self._get_server_key(metadata.server_id)
        batch.srem(server_key, [metadata.task_id.bytes])
        await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def list_tasks_by_server_type(self, server_type: ServerType) -> set[TaskID]:
        """
        Retrieve all task IDs associated with a specific server type.

        Useful for discovering tasks that can be handled by servers of a particular
        type (e.g., all tasks for GPU servers or CPU servers).

        Args:
            server_type: The server type to filter tasks by

        Returns:
            Set of task IDs registered for the specified server type.
            Returns empty set if no tasks exist for the type.

        Note:
            - Returns task IDs only; use get_tasks() to fetch details
            - Task IDs may reference expired tasks until cleanup occurs
        """
        group_key = self._get_server_type_key(server_type)
        raw_task_ids = await self._client.client.smembers(group_key)
        return {TaskID.from_encoded(raw_id) for raw_id in raw_task_ids}

    @valkey_decorator()
    async def list_tasks_by_server(self, server_id: str) -> set[TaskID]:
        """
        Retrieve all task IDs owned by a specific server instance.

        Useful for server-level task management, such as listing all tasks
        running on a particular server or cleaning up tasks when a server shuts down.

        Args:
            server_id: Unique identifier of the server instance

        Returns:
            Set of task IDs associated with the specified server.
            Returns empty set if no tasks exist for the server.

        Note:
            - Each task belongs to exactly one server at a time
            - Task IDs may reference expired tasks until cleanup occurs
        """
        server_key = self._get_server_key(server_id)
        raw_task_ids = await self._client.client.smembers(server_key)
        return {TaskID.from_encoded(raw_id) for raw_id in raw_task_ids}

    @valkey_decorator()
    async def refresh_tasks(self, task_ids: Iterable[TaskID]) -> None:
        """
        Refresh TTL for multiple tasks to indicate they are still active.

        Acts as a heartbeat mechanism by extending the expiration time of tasks,
        preventing them from being automatically deleted due to inactivity.
        Commonly used by task workers to signal ongoing processing.

        Args:
            task_ids: Collection of task IDs to refresh

        Note:
            - Resets TTL to 24 hours for all specified tasks
            - Tasks that don't exist are silently ignored
            - Batch operation for efficiency when updating multiple tasks
            - Should be called periodically for long-running tasks
        """
        batch = self._create_batch()
        keys = [self._get_task_key(task_id) for task_id in task_ids]
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
