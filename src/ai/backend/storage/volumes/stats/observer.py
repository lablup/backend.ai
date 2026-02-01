from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, override

from ai.backend.common.clients.valkey_client.valkey_volume_stats import ValkeyVolumeStatsClient
from ai.backend.common.observer.types import AbstractObserver
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.metrics.volume_perf import VolumePerfMetricObserver
from ai.backend.storage.metrics.volume_stats import VolumeStatsMetricObserver

from .types import CachedFSPerfMetricData, VolumeStatsObserverOptions

if TYPE_CHECKING:
    from ai.backend.storage.volumes.pool import VolumePool


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VolumeStatsObserver(AbstractObserver):
    """
    Periodically observes performance metrics for all active volumes and stores in Redis.

    This observer is designed to be used with Runner, which manages the observation loop.
    """

    _volume_pool: VolumePool
    _valkey_client: ValkeyVolumeStatsClient
    _options: VolumeStatsObserverOptions
    _metric_observer: VolumeStatsMetricObserver
    _perf_metric_observer: VolumePerfMetricObserver

    def __init__(
        self,
        volume_pool: VolumePool,
        valkey_client: ValkeyVolumeStatsClient,
        options: VolumeStatsObserverOptions,
    ) -> None:
        self._volume_pool = volume_pool
        self._valkey_client = valkey_client
        self._options = options
        self._metric_observer = VolumeStatsMetricObserver.instance()
        self._perf_metric_observer = VolumePerfMetricObserver.instance()

    @property
    @override
    def name(self) -> str:
        return "volume_stats"

    @override
    def observe_interval(self) -> float:
        return self._options.observe_interval

    @classmethod
    @override
    def timeout(cls) -> float | None:
        return 30.0

    @override
    async def observe(self) -> None:
        """Observe metrics for all volumes."""
        volumes = self._volume_pool.list_volumes()
        if not volumes:
            log.debug("No volumes to observe")
            return

        tasks = [self._observe_single(volume_name) for volume_name in volumes.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)

    @override
    async def cleanup(self) -> None:
        """Clean up resources used by the observer."""
        pass

    async def _observe_single(self, volume_name: str) -> CachedFSPerfMetricData | None:
        """Observe metric for a single volume and store in Redis."""
        start_time = time.monotonic()
        now = datetime.now(UTC)

        try:
            async with self._volume_pool.get_volume_by_name(volume_name) as volume:
                metric = await asyncio.wait_for(
                    volume.get_performance_metric(),
                    timeout=self._options.timeout_per_volume,
                )

            cached = CachedFSPerfMetricData.from_metric(
                volume_name=volume_name,
                metric=metric,
                observed_at=now,
            )

            # Store in Redis
            await self._store_in_cache(cached)

            # Update Prometheus Gauges
            self._perf_metric_observer.update(
                volume=volume_name,
                iops_read=cached.iops_read,
                iops_write=cached.iops_write,
                io_bytes_read=cached.io_bytes_read,
                io_bytes_write=cached.io_bytes_write,
                io_usec_read=cached.io_usec_read,
                io_usec_write=cached.io_usec_write,
                observed_at=cached.observed_at,
            )

            duration = time.monotonic() - start_time
            self._metric_observer.observe(
                volume=volume_name,
                status="success",
                duration=duration,
            )
            log.debug("Observed volume stats for {}", volume_name)
            return cached
        except TimeoutError:
            duration = time.monotonic() - start_time
            self._metric_observer.observe(
                volume=volume_name,
                status="failure",
                duration=duration,
            )
            log.warning("Timeout observing volume stats for {}", volume_name)
            return None
        except Exception as e:
            duration = time.monotonic() - start_time
            self._metric_observer.observe(
                volume=volume_name,
                status="failure",
                duration=duration,
            )
            log.warning("Failed to observe volume stats for {}: {}", volume_name, e)
            return None

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
