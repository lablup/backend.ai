from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import AgentId, ImageCanonical, ImageID
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
