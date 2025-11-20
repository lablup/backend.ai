from __future__ import annotations

import logging

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.data.image.types import InstalledImageInfo
from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentStatefulSource:
    """
    Stateful source for agent-related operations.
    Uses simple JSON serialization with short TTL for caching.
    """

    _valkey_image: ValkeyImageClient

    def __init__(
        self,
        valkey_image: ValkeyImageClient,
    ) -> None:
        self._valkey_image = valkey_image

    async def read_agent_installed_images(self, agent_id: AgentId) -> list[InstalledImageInfo]:
        """Read installed images for the given agent IDs."""
        return await self._valkey_image.get_agent_installed_images(agent_id)
