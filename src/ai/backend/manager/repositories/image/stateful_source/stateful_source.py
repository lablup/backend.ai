from __future__ import annotations

import logging
from collections.abc import Mapping

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.types import AgentId, ImageID
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageStatefulSource:
    """
    Source for stateful image-related operations.
    Uses simple JSON serialization with short TTL for caching.
    """

    _valkey_image: ValkeyImageClient

    def __init__(self, valkey_image: ValkeyImageClient) -> None:
        self._valkey_image = valkey_image

    async def list_agents_with_image(self, image_id: ImageID) -> set[AgentId]:
        return await self._valkey_image.get_agents_for_image(image_id)

    async def list_agents_with_images(
        self, image_ids: list[ImageID]
    ) -> Mapping[ImageID, set[AgentId]]:
        return await self._valkey_image.get_agents_for_images(image_ids)
