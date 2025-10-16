from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.valkey_client.valkey_image.client import ValkeyImageClient

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageStatefulSource:
    """
    Source for stateful image-related operations.
    Uses simple JSON serialization with short TTL for caching.
    """

    _valkey_image: ValkeyImageClient

    def __init__(self, valkey_image: ValkeyImageClient) -> None:
        self._valkey_image = valkey_image

    async def list_agents_with_image(self, image_id: UUID) -> set[str]:
        return await self._valkey_image.get_agents_for_image(image_id)

    async def list_agents_with_images(self, image_ids: list[UUID]) -> list[set[str]]:
        return await self._valkey_image.get_agents_for_images(image_ids)
