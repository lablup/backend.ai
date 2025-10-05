from __future__ import annotations

import logging
from datetime import datetime

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentCacheSource:
    """
    Cache source for agent-related operations.
    Uses simple JSON serialization with short TTL for caching.
    """

    _valkey_image: ValkeyImageClient
    _valkey_live: ValkeyLiveClient

    def __init__(self, valkey_image: ValkeyImageClient, valkey_live: ValkeyLiveClient) -> None:
        self._valkey_image = valkey_image
        self._valkey_live = valkey_live

    async def set_agent_to_images(self, agent_id: AgentId, image_canonicals: list[str]) -> None:
        await self._valkey_image.add_agent_to_images(agent_id, image_canonicals)

    async def update_agent_last_seen(self, agent_id: AgentId, time: datetime) -> None:
        await self._valkey_live.update_agent_last_seen(agent_id, time.timestamp())

    async def remove_agent_last_seen(self, agent_id: AgentId) -> None:
        await self._valkey_live.remove_agent_last_seen(agent_id)

    async def remove_agent_from_all_images(self, agent_id: AgentId) -> None:
        await self._valkey_image.remove_agent_from_all_images(agent_id)

    async def remove_agent_from_images(
        self, agent_id: AgentId, image_canonicals: list[str]
    ) -> None:
        await self._valkey_image.remove_agent_from_images(agent_id, image_canonicals)
