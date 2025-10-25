"""Cache source for app_config repository operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Optional

from glide import Batch, ExpirySet, ExpiryType

from ai.backend.common.json import dump_json, load_json
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.valkey_client.valkey_cache import ValkeyCache
from ai.backend.manager.data.app_config.types import MergedAppConfig
from ai.backend.manager.models.app_config import AppConfigScopeType
from ai.backend.manager.repositories.utils import suppress_with_log

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

count = 0


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
            global count
            count += 1
            if cached_value:
                log.debug("Cache hit for merged config: {}, hit count: {}", user_id, count)
                return load_json(cached_value)
            log.debug("Cache miss for merged config: {}", user_id)
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
            batch.set(
                cache_key,
                dump_json(merged_config.merged_config),
                expiry=ExpirySet(ExpiryType.SEC, self._cache_ttl),
            )

            # Add user_id to domain's users Set
            domain_users_key = self._get_domain_users_set_key(merged_config.domain_name)
            batch.sadd(domain_users_key, [merged_config.user_id])
            batch.expire(domain_users_key, self._cache_ttl)

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
        - Domain config change: Delete the domain users Set and use pattern matching to find all user configs
        - User config change: Invalidate only that user
        """
        with suppress_with_log([Exception], "Failed to invalidate config cache"):
            match scope_type:
                case AppConfigScopeType.DOMAIN:
                    domain_users_key = self._get_domain_users_set_key(scope_id)
                    user_ids = await self._valkey_cache.client.smembers(domain_users_key)
                    if not user_ids:
                        log.debug(
                            "No users found for domain: {}, skipping cache invalidation", scope_id
                        )
                        return
                    keys_to_delete: list[str | bytes] = [
                        self._get_merged_config_cache_key(user_id.decode()) for user_id in user_ids
                    ]
                    keys_to_delete.append(domain_users_key)
                    remove_count = await self._valkey_cache.client.delete(keys_to_delete)
                    log.debug(
                        "Invalidated {} merged config caches for domain: {}",
                        remove_count,
                        scope_id,
                    )
                case AppConfigScopeType.USER:
                    # For user-level config, only invalidate that user's merged config
                    cache_key = self._get_merged_config_cache_key(scope_id)
                    await self._valkey_cache.client.delete([cache_key])
                    log.debug("Invalidated merged config for user: {}", scope_id)

                case _:
                    # PROJECT or other future scope types
                    log.debug("No cache invalidation needed for scope type: {}", scope_type)

            log.trace("Invalidated config cache: {}:{}", scope_type.value, scope_id)
