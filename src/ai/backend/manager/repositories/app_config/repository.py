"""Main repository for app_config operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.manager.clients.valkey_client.valkey_cache import ValkeyCache
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.models.app_config import AppConfigRow, AppConfigScopeType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec
from ai.backend.manager.repositories.base.creator import Creator

from .cache_source import AppConfigCacheSource
from .db_source import AppConfigDBSource


class AppConfigRepository:
    """
    Main repository for app config operations.
    Combines DB and cache sources for efficient configuration management.
    """

    _db_source: AppConfigDBSource
    _cache_source: AppConfigCacheSource

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
        cache_ttl: int = 600,
    ) -> None:
        """
        Initialize repository.

        Args:
            db: Database engine
            valkey_stat: Valkey client for caching
            cache_ttl: Cache TTL in seconds (default: 10 minutes)
        """
        self._db_source = AppConfigDBSource(db)
        valkey_cache = ValkeyCache(valkey_stat._client)
        self._cache_source = AppConfigCacheSource(valkey_cache, cache_ttl)

    async def get_config(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> Optional[AppConfigData]:
        """Get app configuration for a specific scope."""
        return await self._db_source.get_config(scope_type, scope_id)

    async def get_merged_config(
        self,
        user_id: str,
    ) -> Mapping[str, Any]:
        """
        Get merged configuration for a user.

        Tries cache first, falls back to DB on cache miss.

        Returns:
            Merged configuration dictionary
        """
        # Try cache first
        cached_config = await self._cache_source.get_merged_config(user_id)
        if cached_config is not None:
            return cached_config

        # Cache miss - fetch from DB
        merged_config = await self._db_source.get_merged_config(user_id)

        # Cache the result
        await self._cache_source.set_merged_config(merged_config)

        return merged_config.merged_config

    async def create_config(self, creator: Creator[AppConfigRow]) -> AppConfigData:
        """Create a new app configuration."""
        return await self._db_source.create_config(creator)

    async def upsert_config(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
        spec: AppConfigUpdaterSpec,
    ) -> AppConfigData:
        """
        Create or update app configuration.

        Invalidates cache after update.
        """
        result = await self._db_source.upsert_config(scope_type, scope_id, spec)
        await self._cache_source.invalidate_config(scope_type, scope_id)

        return result

    async def delete_config(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> bool:
        """
        Delete an app configuration.

        Invalidates cache after deletion.
        """
        result = await self._db_source.delete_config(scope_type, scope_id)
        await self._cache_source.invalidate_config(scope_type, scope_id)
        return result
