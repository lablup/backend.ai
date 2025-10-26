"""Cache source for app_config repository operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Optional

from glide import Batch

from ai.backend.common.json import dump_json, load_json
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.valkey_client.valkey_cache import ValkeyCache
from ai.backend.manager.data.app_config.types import MergedAppConfig
from ai.backend.manager.models.app_config import AppConfigScopeType
from ai.backend.manager.repositories.utils import suppress_with_log

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigCacheSource:
    """
    Cache source for app config operations.
    Handles all Redis/Valkey cache operations for app configurations.
    """

    _valkey_cache: ValkeyCache
    _cache_ttl: int

    def __init__(self, valkey_cache: ValkeyCache, cache_ttl: int = 300) -> None:
        """
        Initialize cache source.

        Args:
            valkey_cache: Valkey cache client for caching
            cache_ttl: Cache TTL in seconds (default: 5 minutes)
        """
        self._valkey_cache = valkey_cache
        self._cache_ttl = cache_ttl

    def _get_merged_config_cache_key(self, user_id: str) -> str:
        """Generate cache key for merged config."""
        return f"app_config:merged:{user_id}"

    def _get_domain_users_set_key(self, domain_name: str) -> str:
        """Generate Redis Set key for tracking users in a domain."""
        return f"app_config:domain:{domain_name}:users"

    async def get_merged_config(self, user_id: str) -> Optional[Mapping[str, Any]]:
        """
        Get merged configuration from cache.

        Returns:
            Cached config if exists, None if not in cache
        """
        with suppress_with_log([Exception], "Failed to get merged config from cache"):
            cache_key = self._get_merged_config_cache_key(user_id)
            cached_value = await self._valkey_cache.client.get(cache_key)
            if cached_value:
                log.trace("Cache hit for merged config: {}", user_id)
                return load_json(cached_value)
            log.trace("Cache miss for merged config: {}", user_id)
        return None

    async def set_merged_config(
        self,
        merged_config: MergedAppConfig,
    ) -> None:
        """
        Set merged configuration in cache.

        Also tracks this user_id in the domain's users Set for efficient invalidation.

        Args:
            merged_config: MergedAppConfig containing user_id, domain_name, and config
        """
        with suppress_with_log([Exception], "Failed to set merged config in cache"):
            # Use batch to set both the config and add user to domain set
            batch = Batch(is_atomic=False)

            # Cache the merged config
            cache_key = self._get_merged_config_cache_key(merged_config.user_id)
            batch.set(cache_key, dump_json(merged_config.merged_config))
            batch.expire(cache_key, self._cache_ttl)

            # Add user_id to domain's users Set
            domain_users_key = self._get_domain_users_set_key(merged_config.domain_name)
            batch.sadd(domain_users_key, [merged_config.user_id])
            batch.expire(domain_users_key, self._cache_ttl)

            # Execute batch
            await self._valkey_cache.client.exec(batch, raise_on_error=True)

            log.trace(
                "Cached merged config for user {} in domain {}",
                merged_config.user_id,
                merged_config.domain_name,
            )

    async def invalidate_config(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> None:
        """
        Invalidate cache for a specific config.

        When a config is updated:
        - Domain config change: Invalidate all users in that domain
        - User config change: Invalidate only that user
        """
        with suppress_with_log([Exception], "Failed to invalidate config cache"):
            match scope_type:
                case AppConfigScopeType.DOMAIN:
                    # Get all user_ids in this domain
                    domain_users_key = self._get_domain_users_set_key(scope_id)
                    user_ids_result = await self._valkey_cache.client.smembers(domain_users_key)
                    user_ids = list(user_ids_result) if user_ids_result else []

                    if user_ids:
                        # Invalidate all users' merged configs using batch
                        batch = Batch(is_atomic=False)
                        cache_keys = [
                            self._get_merged_config_cache_key(str(uid)) for uid in user_ids
                        ]
                        for key in cache_keys:
                            batch.delete([key])

                        # Clean up the domain users Set
                        batch.delete([domain_users_key])

                        # Execute batch
                        await self._valkey_cache.client.exec(batch, raise_on_error=True)

                        log.trace(
                            "Invalidated {} user configs for domain: {}",
                            len(user_ids),
                            scope_id,
                        )
                    else:
                        # Just clean up the domain users Set if no users
                        await self._valkey_cache.client.delete([domain_users_key])

                case AppConfigScopeType.USER:
                    # For user-level config, only invalidate that user's merged config
                    cache_key = self._get_merged_config_cache_key(scope_id)
                    await self._valkey_cache.client.delete([cache_key])
                    log.trace("Invalidated merged config for user: {}", scope_id)

                case _:
                    # PROJECT or other future scope types
                    log.trace("No cache invalidation needed for scope type: {}", scope_type)

            log.trace("Invalidated config cache: {}:{}", scope_type.value, scope_id)
