from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_bgtask import ValkeyBgtaskClient
from ai.backend.logging import BraceStyleAdapter

from .defs import (
    DEFAULT_TTL_SECONDS,
    SERVER_GROUP_KEY_PREFIX,
    SERVER_KEY_PREFIX,
    TASK_KEY_PREFIX,
)
from .types import (
    BackgroundTaskMetadata,
    ServerType,
)


@dataclass
class BackgroundTaskRegistryArgs:
    """Arguments for TaskRegistry initialization"""

    valkey_client: ValkeyBgtaskClient


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BackgroundTaskRegistry:
    """Manages background task metadata and tracking in key-value store"""

    _valkey: ValkeyBgtaskClient

    def __init__(self, args: BackgroundTaskRegistryArgs) -> None:
        self._valkey = args.valkey_client

    def _server_group_key(self, server_type: ServerType) -> str:
        """Key for server type task set"""
        return f"{SERVER_GROUP_KEY_PREFIX}:{server_type}"

    def _server_id_key(self, server_id: str) -> str:
        """Key for server-specific task set"""
        return f"{SERVER_KEY_PREFIX}:{server_id}"

    def _task_metadata_key(self, task_id: uuid.UUID) -> str:
        """Key for individual task metadata"""
        return f"{TASK_KEY_PREFIX}:{task_id}"

    async def save_task(self, metadata: BackgroundTaskMetadata) -> None:
        """Save task metadata to store"""
        task_key = self._task_metadata_key(metadata.task_id)

        # Store task metadata as JSON
        await self._valkey.save_task(task_key, metadata.to_json(), metadata.ttl_seconds)
        await self._valkey.set_ttl(task_key, metadata.ttl_seconds)

        # Add to server type set if specified
        group_key = self._server_group_key(metadata.server_type)
        await self._valkey.add_to_set(group_key, [str(metadata.task_id)])
        await self._valkey.set_ttl(group_key, metadata.ttl_seconds)

        # Add to server-specific set if specified
        server_key = self._server_id_key(metadata.server_id)
        await self._valkey.add_to_set(server_key, [str(metadata.task_id)])
        await self._valkey.set_ttl(server_key, metadata.ttl_seconds)

        log.debug(
            "Registered task {} (task: {}, server_id: {}, server_type: {})",
            metadata.task_id,
            metadata.task_name,
            metadata.server_id,
            metadata.server_type,
        )

    async def get_task(self, task_id: uuid.UUID) -> Optional[BackgroundTaskMetadata]:
        """Retrieve task metadata from store"""
        task_key = self._task_metadata_key(task_id)
        data = await self._valkey.get_task(task_key)

        if not data:
            return None

        return BackgroundTaskMetadata.from_json(data)

    async def update_task(self, metadata: BackgroundTaskMetadata) -> None:
        """Update existing task metadata"""
        task_key = self._task_metadata_key(metadata.task_id)

        # Update metadata
        await self._valkey.save_task(task_key, metadata.to_json(), metadata.ttl_seconds)

        log.debug(
            "Updated task {} status: {}, retry: {}/{}",
            metadata.task_id,
            metadata.status,
            metadata.retry_count,
            metadata.max_retries,
        )

    async def delete_task(self, task_id: uuid.UUID) -> None:
        """Remove task from store and all associated sets"""
        task_key = f"{TASK_KEY_PREFIX}:{task_id}"

        # Get metadata first to know which sets to clean
        metadata = await self.get_task(task_id)

        if metadata:
            # Remove from server type set
            if metadata.server_type:
                group_key = self._server_group_key(metadata.server_type)
                await self._valkey.remove_from_set(group_key, [str(task_id)])

            # Remove from server-specific set
            if metadata.server_id:
                server_key = self._server_id_key(metadata.server_id)
                await self._valkey.remove_from_set(server_key, [str(task_id)])

        # Remove task metadata
        await self._valkey.delete_task([task_key])

        log.debug("Removed task {}", task_id)

    async def get_server_tasks(self, server_id: str) -> set[uuid.UUID]:
        """Get all tasks assigned to a specific server"""
        server_key = self._server_id_key(server_id)
        task_ids = await self._valkey.get_set_members(server_key)

        if not task_ids:
            return set()

        return {uuid.UUID(tid) for tid in task_ids}

    async def get_server_type_tasks(self, server_type: ServerType) -> set[uuid.UUID]:
        """Get all tasks assigned to a server type (e.g., all manager tasks)"""
        group_key = self._server_group_key(server_type)
        task_ids = await self._valkey.get_set_members(group_key)

        if not task_ids:
            return set()

        return {uuid.UUID(tid) for tid in task_ids}

    async def update_heartbeat(
        self, task_id: uuid.UUID, ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> None:
        """Update task heartbeat timestamp"""
        task_key = self._task_metadata_key(task_id)
        task = await self.get_task(task_id)
        if task is None:
            log.warning("Cannot update heartbeat for non-existent task {}", task_id)
            return
        task.updated_at = time.time()
        await self._valkey.save_task(task_key, task.to_json(), ttl_seconds)
        await self._valkey.set_ttl(task_key, ttl_seconds)
