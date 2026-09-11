from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.valkey_volume_stats import ValkeyVolumeStatsClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.runner.types import Runner
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.volumes.pool import VolumePool
from ai.backend.storage.volumes.stats import (
    VolumeState,
    VolumeStatsObserver,
    VolumeStatsObserverOptions,
)


@dataclass
class VolumeStatsInput:
    """Input required for the volume stats setup."""

    local_config: StorageProxyUnifiedConfig
    volume_pool: VolumePool
    valkey_volume_stats: ValkeyVolumeStatsClient


@dataclass
class VolumeStatsResources:
    """Container for volume stats resources."""

    observer: VolumeStatsObserver
    state: VolumeState


class VolumeStatsProvider(NonMonitorableDependencyProvider[VolumeStatsInput, VolumeStatsResources]):
    """Provider for the volume stats observer loop and its cached state."""

    @property
    @override
    def stage_name(self) -> str:
        return "volume-stats"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: VolumeStatsInput) -> AsyncIterator[VolumeStatsResources]:
        volume_stats_config = setup_input.local_config.storage_proxy.volume_stats
        options = VolumeStatsObserverOptions(
            observe_interval=volume_stats_config.observe_interval,
            timeout_per_volume=volume_stats_config.observe_timeout,
            cache_ttl=volume_stats_config.cache_ttl,
        )
        observer = VolumeStatsObserver(
            volume_pool=setup_input.volume_pool,
            valkey_client=setup_input.valkey_volume_stats,
            options=options,
        )
        runner = Runner(resources=[])
        await runner.register_observer(observer)
        await runner.start()
        state = VolumeState(
            volume_pool=setup_input.volume_pool,
            valkey_client=setup_input.valkey_volume_stats,
            options=options,
        )
        try:
            yield VolumeStatsResources(observer=observer, state=state)
        finally:
            await runner.close()
