"""Cache source for resource preset repository operations."""

from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.json import dump_json, load_json
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.resource_preset.types import ResourcePresetData

log = StructuredLogger(logging.getLogger(__spec__.name))

# Cache TTL in seconds
CACHE_TTL = 60  # 1 minute


class ResourcePresetCacheSource:
    """
    Cache source for resource preset operations.
    Uses simple JSON serialization with short TTL for caching.
    """

    _valkey_stat: ValkeyStatClient

    def __init__(self, valkey_stat: ValkeyStatClient) -> None:
        self._valkey_stat = valkey_stat

    async def get_preset_by_id(self, preset_id: UUID) -> ResourcePresetData | None:
        """
        Get a preset from cache by ID.
        Returns None if not in cache.
        """
        data = await self._valkey_stat.get_resource_preset_by_id(str(preset_id))
        if data:
            return ResourcePresetData.from_cache(load_json(data))
        return None

    async def get_preset_by_name(self, name: str) -> ResourcePresetData | None:
        """
        Get a preset from cache by name.
        Returns None if not in cache.
        """
        data = await self._valkey_stat.get_resource_preset_by_name(name)
        if data:
            return ResourcePresetData.from_cache(load_json(data))
        return None

    async def set_preset(self, preset: ResourcePresetData) -> None:
        """
        Cache a preset by both ID and name.
        """
        serialized = dump_json(preset.to_cache())
        await self._valkey_stat.set_resource_preset_by_id_and_name(
            str(preset.id),
            preset.name,
            serialized,
            expire_sec=CACHE_TTL,
        )

    async def get_preset_list(
        self, resource_group: str | None = None
    ) -> list[ResourcePresetData] | None:
        """
        Get cached preset list for a scaling group.
        """
        data = await self._valkey_stat.get_resource_preset_list(resource_group)
        if data:
            items = load_json(data)
            return [ResourcePresetData.from_cache(item) for item in items]
        return None

    async def set_preset_list(
        self, presets: list[ResourcePresetData], resource_group: str | None = None
    ) -> None:
        """
        Cache a list of presets for a scaling group.
        """
        serialized = dump_json([p.to_cache() for p in presets])
        await self._valkey_stat.set_resource_preset_list(
            resource_group, serialized, expire_sec=CACHE_TTL
        )

    async def invalidate_preset(
        self, preset_id: UUID | None = None, name: str | None = None
    ) -> None:
        """
        Invalidate a cached preset.
        Note: Since we can't scan for patterns, we only delete the specific keys we know.
        Lists will expire naturally with TTL.
        """
        await self._valkey_stat.delete_resource_preset(str(preset_id) if preset_id else None, name)

    async def invalidate_all_presets(self) -> None:
        """
        Invalidate all cached presets by deleting all preset-related cache keys.
        This ensures immediate cache invalidation rather than waiting for TTL expiration.
        """
        await self._valkey_stat.invalidate_all_resource_presets()
