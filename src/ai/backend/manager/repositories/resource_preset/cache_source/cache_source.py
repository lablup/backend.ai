"""Cache source for resource preset repository operations."""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.types import AccessKey
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.resource_preset.types import ResourcePresetData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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

    async def get_preset_by_id(self, preset_id: UUID) -> Optional[ResourcePresetData]:
        """
        Get a preset from cache by ID.
        Returns None if not in cache.
        """
        data = await self._valkey_stat.get_resource_preset_by_id(str(preset_id))
        if data:
            return ResourcePresetData.from_cache(load_json(data))
        return None

    async def get_preset_by_name(self, name: str) -> Optional[ResourcePresetData]:
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
        self, scaling_group: Optional[str] = None
    ) -> Optional[list[ResourcePresetData]]:
        """
        Get cached preset list for a scaling group.
        """
        data = await self._valkey_stat.get_resource_preset_list(scaling_group)
        if data:
            items = load_json(data)
            return [ResourcePresetData.from_cache(item) for item in items]
        return None

    async def set_preset_list(
        self, presets: list[ResourcePresetData], scaling_group: Optional[str] = None
    ) -> None:
        """
        Cache a list of presets for a scaling group.
        """
        serialized = dump_json([p.to_cache() for p in presets])
        await self._valkey_stat.set_resource_preset_list(
            scaling_group, serialized, expire_sec=CACHE_TTL
        )

    async def get_check_presets_data(
        self,
        access_key: AccessKey,
        group: str,
        domain: str,
        scaling_group: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Get cached check presets data as JSON string.
        Returns the raw JSON string to avoid complex deserialization.
        """
        data = await self._valkey_stat.get_resource_preset_check_data(
            str(access_key), group, domain, scaling_group
        )
        return data

    async def set_check_presets_data(
        self,
        access_key: AccessKey,
        group: str,
        domain: str,
        scaling_group: Optional[str],
        data: bytes,
    ) -> None:
        """
        Cache check presets data as JSON string.
        Takes pre-serialized JSON string to avoid double serialization.
        """
        await self._valkey_stat.set_resource_preset_check_data(
            str(access_key), group, domain, scaling_group, data, expire_sec=CACHE_TTL
        )

    async def invalidate_preset(
        self, preset_id: Optional[UUID] = None, name: Optional[str] = None
    ) -> None:
        """
        Invalidate a cached preset.
        Note: Since we can't scan for patterns, we only delete the specific keys we know.
        Check presets and lists will expire naturally with TTL.
        """
        await self._valkey_stat.delete_resource_preset(str(preset_id) if preset_id else None, name)

    async def invalidate_all_presets(self) -> None:
        """
        Invalidate all cached presets by deleting all preset-related cache keys.
        This ensures immediate cache invalidation rather than waiting for TTL expiration.
        """
        await self._valkey_stat.invalidate_all_resource_presets()
