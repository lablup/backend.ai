from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.volumes.abc import AbstractVolume
from ai.backend.storage.volumes.pool import VolumePool
from ai.backend.storage.watcher import WatcherClient


@dataclass
class VolumePoolInput:
    """Input required for the volume pool setup."""

    local_config: StorageProxyUnifiedConfig
    etcd: AsyncEtcd
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    backends: Mapping[str, type[AbstractVolume]]
    watcher: WatcherClient | None


class VolumePoolProvider(NonMonitorableDependencyProvider[VolumePoolInput, VolumePool]):
    """Provider for the volume pool."""

    @property
    @override
    def stage_name(self) -> str:
        return "volume-pool"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: VolumePoolInput) -> AsyncIterator[VolumePool]:
        volume_pool = await VolumePool.create(
            local_config=setup_input.local_config,
            etcd=setup_input.etcd,
            event_dispatcher=setup_input.event_dispatcher,
            event_producer=setup_input.event_producer,
            backends=setup_input.backends,
            watcher=setup_input.watcher,
        )
        try:
            yield volume_pool
        finally:
            await volume_pool.shutdown()
