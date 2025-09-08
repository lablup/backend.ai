"""Cache source for resource preset repository operations."""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.resource_preset.types import ResourcePresetData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourcePresetCacheSource:
    """
    Cache source for resource preset operations.
    Currently provides a minimal implementation that can be extended as needed.
    """

    _valkey_stat: ValkeyStatClient

    def __init__(self, valkey_stat: ValkeyStatClient) -> None:
        self._valkey_stat = valkey_stat

    async def get_preset_by_id(self, preset_id: UUID) -> Optional[ResourcePresetData]:
        """
        Try to get a preset from cache by ID.
        Returns None if not in cache.
        """
        # Currently no caching implementation
        # Can be extended to cache frequently accessed presets
        return None

    async def get_preset_by_name(self, name: str) -> Optional[ResourcePresetData]:
        """
        Try to get a preset from cache by name.
        Returns None if not in cache.
        """
        # Currently no caching implementation
        # Can be extended to cache frequently accessed presets
        return None

    async def set_preset(self, preset: ResourcePresetData) -> None:
        """
        Cache a preset.
        """
        # Currently no caching implementation
        # Can be extended to cache frequently accessed presets
        pass

    async def invalidate_preset(
        self, preset_id: Optional[UUID] = None, name: Optional[str] = None
    ) -> None:
        """
        Invalidate a cached preset.
        """
        # Currently no caching implementation
        # Will be needed when caching is implemented
        pass

    async def invalidate_all_presets(self) -> None:
        """
        Invalidate all cached presets.
        """
        # Currently no caching implementation
        # Will be needed when caching is implemented
        pass
