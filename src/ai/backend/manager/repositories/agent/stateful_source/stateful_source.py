from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
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
    _valkey_stat: ValkeyStatClient

    def __init__(
        self,
        valkey_image: ValkeyImageClient,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        self._valkey_image = valkey_image
        self._valkey_stat = valkey_stat

    async def read_agent_installed_images(self, agent_id: AgentId) -> list[InstalledImageInfo]:
        """Read installed images for the given agent IDs."""
        return await self._valkey_image.get_agent_installed_images(agent_id)

    async def read_agent_container_counts(self, agent_ids: Sequence[AgentId]) -> Sequence[int]:
        """Read container count for the given agent IDs.

        Returns counts in the same order as the input agent_ids.
        """
        agent_id_list = [str(agent_id) for agent_id in agent_ids]
        return await self._valkey_stat.get_agent_container_counts_batch(agent_id_list)
