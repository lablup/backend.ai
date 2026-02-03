from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_volume_stats import ValkeyVolumeStatsClient
from ai.backend.logging import BraceStyleAdapter

from .types import CachedFSPerfMetricData, VolumeStatsObserverOptions

if TYPE_CHECKING:
    from ai.backend.storage.volumes.pool import VolumePool


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VolumeState:
    """
    Volume stats state lookup.

    Provides access to cached volume performance metrics with fallback
    to direct API calls when cache is unavailable.
    """

    _volume_pool: VolumePool
    _valkey_client: ValkeyVolumeStatsClient
    _options: VolumeStatsObserverOptions

    def __init__(
        self,
        volume_pool: VolumePool,
        valkey_client: ValkeyVolumeStatsClient,
        options: VolumeStatsObserverOptions,
    ) -> None:
        self._volume_pool = volume_pool
        self._valkey_client = valkey_client
        self._options = options

    async def get_performance_metric(
        self,
        volume_name: str,
    ) -> CachedFSPerfMetricData:
        """
        Get performance metric for a volume.

        1. Try Redis cache lookup
        2. On cache miss or Redis failure, call external API directly
        3. Store external API result in Redis (suppress failures)
        """
        # Try cache first
        cached = await self._get_from_cache(volume_name)
        if cached is not None:
            log.debug("Cache hit for volume stats: {}", volume_name)
            return cached

        # Fallback to direct API call
        log.debug("Cache miss for volume stats: {}, calling API", volume_name)
        return await self._fetch_and_cache(volume_name)

    async def _get_from_cache(self, volume_name: str) -> CachedFSPerfMetricData | None:
        """Try to get cached metric from Redis."""
        try:
            data_bytes = await self._valkey_client.get_volume_stats(volume_name)
            if data_bytes is None:
                return None
            return CachedFSPerfMetricData.model_validate_json(data_bytes)
        except Exception as e:
            log.warning("Failed to get volume stats from cache for {}: {}", volume_name, e)
            return None

    async def _fetch_and_cache(self, volume_name: str) -> CachedFSPerfMetricData:
        """Fetch metric from volume API and store in cache."""
        now = datetime.now(UTC)

        async with self._volume_pool.get_volume_by_name(volume_name) as volume:
            metric = await volume.get_performance_metric()
        cached = CachedFSPerfMetricData.from_metric(
            volume_name=volume_name,
            metric=metric,
            observed_at=now,
        )
        # Store in cache (suppress failures)
        await self._store_in_cache(cached)
        return cached

    async def _store_in_cache(self, cached: CachedFSPerfMetricData) -> None:
        """Store cached metric in Redis with TTL."""
        try:
            await self._valkey_client.set_volume_stats(
                volume_name=cached.volume_name,
                data=cached.model_dump_json(),
                ttl_seconds=int(self._options.cache_ttl),
            )
        except Exception as e:
            log.warning("Failed to store volume stats in cache for {}: {}", cached.volume_name, e)
