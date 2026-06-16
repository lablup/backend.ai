"""Cache source for AppConfigFragment merged-view reads.

The hot path is `AppConfigFragmentRepository.app_config(user_id, name)`,
the per-`(user, name)` deep-merge of every contributing fragment ordered
by `rank` (low → high). Each merged value gets cached under
`app_config:merged:{user_id}:{name}` with a TTL, and is invalidated
whenever a contributing fragment changes.

Membership indexes let invalidation work without `SCAN`:

- ``app_config:user_keys:{user_id}`` — set of `(user_id, name)` cache
  keys this user currently has cached. Per-user invalidation pops the
  set in one `SMEMBERS` + `DEL`.
- ``app_config:domain_users:{domain_name}`` — set of `user_id`s
  currently observed in this domain. Per-domain invalidation expands
  to a per-user invalidation for each member.

Cache failures never break a request — every public method is wrapped
in `suppress_with_log` so any Valkey error falls through to the DB.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from typing import Any, cast

from glide import Batch, ExpirySet, ExpiryType

from ai.backend.common.json import dump_json, load_json
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.valkey_client.valkey_cache import ValkeyCache
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import AppConfigScopeType
from ai.backend.manager.repositories.utils import suppress_with_log

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigFragmentCacheSource:
    """Valkey-backed cache for the per-`(user, name)` merged AppConfig view."""

    _valkey_cache: ValkeyCache
    _cache_ttl: int

    def __init__(self, valkey_cache: ValkeyCache, cache_ttl: int = 600) -> None:
        """Args:
        valkey_cache: Manager-side Valkey cache client.
        cache_ttl: TTL in seconds (default: 10 minutes).
        """
        self._valkey_cache = valkey_cache
        self._cache_ttl = cache_ttl

    # ── Key derivation ─────────────────────────────────────────────

    @staticmethod
    def _merged_key(user_id: uuid.UUID | str, name: str) -> str:
        return f"app_config:merged:{user_id}:{name}"

    @staticmethod
    def _user_keys_set(user_id: uuid.UUID | str) -> str:
        return f"app_config:user_keys:{user_id}"

    @staticmethod
    def _domain_users_set(domain_name: str) -> str:
        return f"app_config:domain_users:{domain_name}"

    # ── Read ───────────────────────────────────────────────────────

    async def get_merged_config(
        self,
        user_id: uuid.UUID,
        name: str,
    ) -> Mapping[str, Any] | None:
        """Return the cached `config` payload, or `None` on miss / failure.

        Only the merged `config` mapping is cached — `fragments` are
        cheap to recompute when needed and would bloat the cache.
        """
        with suppress_with_log([Exception], "Failed to read merged config from cache"):
            cache_key = self._merged_key(user_id, name)
            async with self._valkey_cache.client() as conn:
                cached_value = await conn.get(cache_key)
            if cached_value:
                log.debug("Cache hit for merged config: {} {}", user_id, name)
                return cast(Mapping[str, Any] | None, load_json(cached_value))
            log.debug("Cache miss for merged config: {} {}", user_id, name)
        return None

    # ── Write ──────────────────────────────────────────────────────

    async def set_merged_config(
        self,
        merged: AppConfigData,
        domain_name: str | None = None,
    ) -> None:
        """Cache the merged `config` payload + index it for invalidation.

        Indexes the cache key in the user's key set; if `domain_name`
        is supplied, also adds the user to the domain's user set so
        domain-level invalidation can cascade.
        """
        if merged.config is None:
            # Nothing useful to cache — leave as miss-on-next-read.
            return
        with suppress_with_log([Exception], "Failed to write merged config to cache"):
            user_id = str(merged.user_id)
            cache_key = self._merged_key(user_id, merged.name)

            batch = Batch(is_atomic=False)
            batch.set(
                cache_key,
                dump_json(merged.config),
                expiry=ExpirySet(ExpiryType.SEC, self._cache_ttl),
            )
            user_keys = self._user_keys_set(user_id)
            batch.sadd(user_keys, [cache_key])
            batch.expire(user_keys, self._cache_ttl)
            if domain_name is not None:
                domain_users = self._domain_users_set(domain_name)
                batch.sadd(domain_users, [user_id])
                batch.expire(domain_users, self._cache_ttl)

            async with self._valkey_cache.client() as conn:
                await conn.exec(batch, raise_on_error=True)

            log.trace(
                "Cached merged config for user {} name {} (domain={})",
                user_id,
                merged.name,
                domain_name,
            )

    # ── Invalidate ────────────────────────────────────────────────

    async def invalidate_for_scope(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> None:
        """Invalidate every cached merged view affected by a fragment write.

        `scope_id` is the user UUID for `USER`, the domain name for
        `DOMAIN` / `DOMAIN_USER_DEFAULTS`, or the literal `"public"`
        for `PUBLIC`. `PUBLIC` invalidation is intentionally not
        wired here — its blast radius is the whole cache; rely on TTL
        for now (admin-only, low-frequency operation).
        """
        with suppress_with_log([Exception], "Failed to invalidate merged-config cache"):
            match scope_type:
                case AppConfigScopeType.USER:
                    await self._invalidate_user(scope_id)
                case AppConfigScopeType.DOMAIN | AppConfigScopeType.DOMAIN_USER_DEFAULTS:
                    await self._invalidate_domain(scope_id)
                case AppConfigScopeType.PUBLIC:
                    log.debug(
                        "PUBLIC-scope invalidation not wired; relying on TTL ({}s)",
                        self._cache_ttl,
                    )

    async def invalidate_for_user(self, user_id: uuid.UUID | str) -> None:
        """Drop every cached merged view owned by `user_id`.

        Convenience wrapper used by self-service bulk writes that
        always operate on the caller's `USER` row.
        """
        with suppress_with_log([Exception], "Failed to invalidate user merged-config cache"):
            await self._invalidate_user(str(user_id))

    async def _invalidate_user(self, user_id: str) -> None:
        user_keys = self._user_keys_set(user_id)
        async with self._valkey_cache.client() as conn:
            cached_keys = await conn.smembers(user_keys)
        if not cached_keys:
            log.debug("No cached keys for user {}, skipping invalidation", user_id)
            return
        keys_to_delete: list[str | bytes] = list(cached_keys)
        keys_to_delete.append(user_keys)
        async with self._valkey_cache.client() as conn:
            removed = await conn.delete(keys_to_delete)
        log.debug("Invalidated {} merged-config keys for user {}", removed, user_id)

    async def _invalidate_domain(self, domain_name: str) -> None:
        domain_users = self._domain_users_set(domain_name)
        async with self._valkey_cache.client() as conn:
            user_ids = await conn.smembers(domain_users)
        if not user_ids:
            log.debug(
                "No tracked users for domain {}, skipping cache invalidation",
                domain_name,
            )
            return
        for raw in user_ids:
            user_id = raw.decode() if isinstance(raw, bytes) else str(raw)
            await self._invalidate_user(user_id)
        async with self._valkey_cache.client() as conn:
            await conn.delete([domain_users])
        log.debug(
            "Invalidated merged-config caches for {} users in domain {}",
            len(user_ids),
            domain_name,
        )
