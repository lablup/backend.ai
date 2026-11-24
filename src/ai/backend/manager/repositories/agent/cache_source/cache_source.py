from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.agent.types import GPUDeviceAllocation
from ai.backend.common.types import AgentId, ImageCanonical, ImageID
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


class AgentCacheSource:
    """
    Cache source for agent-related operations.
    Uses simple JSON serialization with short TTL for caching.
    """

    _valkey_image: ValkeyImageClient
    _valkey_live: ValkeyLiveClient
    _valkey_stat: ValkeyStatClient

    def __init__(
        self,
        valkey_image: ValkeyImageClient,
        valkey_live: ValkeyLiveClient,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        self._valkey_image = valkey_image
        self._valkey_live = valkey_live
        self._valkey_stat = valkey_stat

    async def set_agent_to_images(self, agent_id: AgentId, image_ids: list[ImageID]) -> None:
        await self._valkey_image.add_agent_to_images(agent_id, image_ids)

    async def update_agent_last_seen(self, agent_id: AgentId, time: datetime) -> None:
        await self._valkey_live.update_agent_last_seen(agent_id, time.timestamp())

    async def remove_agent_last_seen(self, agent_id: AgentId) -> None:
        await self._valkey_live.remove_agent_last_seen(agent_id)

    async def remove_agent_from_all_images(self, agent_id: AgentId) -> None:
        await self._valkey_image.remove_agent_from_all_images(agent_id)

    async def remove_agent_from_images(self, agent_id: AgentId, image_ids: list[ImageID]) -> None:
        await self._valkey_image.remove_agent_from_images(agent_id, image_ids)

    # For compatibility with redis key made with image canonical strings
    # Use remove_agent_from_images instead of this if possible
    async def remove_agent_from_images_by_canonicals(
        self, agent_id: AgentId, image_canonicals: list[ImageCanonical]
    ) -> None:
        await self._valkey_image.remove_agent_from_images_by_canonicals(agent_id, image_canonicals)

    async def update_gpu_alloc_map(self, agent_id: AgentId, alloc_map: Mapping[str, Any]) -> None:
        """Update GPU allocation map in cache."""
        await self._valkey_stat.set_gpu_allocation_map(str(agent_id), alloc_map)

    async def update_gpu_devices(
        self, agent_id: AgentId, gpu_devices: Sequence[GPUDeviceAllocation]
    ) -> None:
        """Update the scanned GPU devices in cache."""
        await self._valkey_stat.set_gpu_devices(agent_id, gpu_devices)

    async def read_gpu_devices(
        self, agent_ids: Sequence[AgentId]
    ) -> Mapping[AgentId, list[GPUDeviceAllocation]]:
        """The scanned GPU devices of each agent; an agent without a scan result is absent."""
        cached = await self._valkey_stat.get_gpu_devices_batch(agent_ids)
        return {
            agent_id: gpu_devices
            for agent_id, gpu_devices in zip(agent_ids, cached, strict=True)
            if gpu_devices is not None
        }
