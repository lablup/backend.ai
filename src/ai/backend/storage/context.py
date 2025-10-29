from __future__ import annotations

import logging
from collections.abc import MutableMapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import (
    AsyncIterator,
    Final,
    Mapping,
)

import aiohttp_cors

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.logging import BraceStyleAdapter

from .config.unified import StorageProxyUnifiedConfig
from .exception import InvalidVolumeError
from .services.service import VolumeService
from .storages.storage_pool import StoragePool
from .types import VolumeInfo
from .volumes.abc import AbstractVolume
from .volumes.cephfs import CephFSVolume
from .volumes.ddn import EXAScalerFSVolume
from .volumes.dellemc import DellEMCOneFSVolume
from .volumes.gpfs import GPFSVolume
from .volumes.hammerspace.simple_volume import HammerspaceSimpleVolume
from .volumes.hammerspace.volume import HammerspaceVolume
from .volumes.netapp import NetAppVolume
from .volumes.noop import NoopVolume
from .volumes.pool import VolumePool
from .volumes.purestorage import FlashBladeVolume
from .volumes.vast import VASTVolume
from .volumes.vfs import BaseVolume
from .volumes.weka import WekaVolume
from .volumes.xfs import XfsVolume
from .watcher import WatcherClient

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "storage-proxy"

DEFAULT_BACKENDS: Mapping[str, type[AbstractVolume]] = {
    FlashBladeVolume.name: FlashBladeVolume,
    BaseVolume.name: BaseVolume,
    XfsVolume.name: XfsVolume,
    NetAppVolume.name: NetAppVolume,
    # NOTE: Dell EMC has two different storage: PowerStore and PowerScale (OneFS).
    #       We support the latter only for now.
    DellEMCOneFSVolume.name: DellEMCOneFSVolume,
    WekaVolume.name: WekaVolume,
    GPFSVolume.name: GPFSVolume,  # IBM SpectrumScale or GPFS
    "spectrumscale": GPFSVolume,  # IBM SpectrumScale or GPFS
    CephFSVolume.name: CephFSVolume,
    VASTVolume.name: VASTVolume,
    EXAScalerFSVolume.name: EXAScalerFSVolume,
    NoopVolume.name: NoopVolume,
    HammerspaceVolume.name: HammerspaceVolume,
    HammerspaceSimpleVolume.name: HammerspaceSimpleVolume,
}


class ServiceContext:
    volume_service: VolumeService

    def __init__(
        self,
        service: VolumeService,
    ) -> None:
        self.volume_service = service


@dataclass(slots=True)
class RootContext:
    # configuration context
    pid: int
    pidx: int
    node_id: str
    local_config: StorageProxyUnifiedConfig
    etcd: AsyncEtcd

    # internal services
    volume_pool: VolumePool
    storage_pool: StoragePool
    event_producer: EventProducer
    event_dispatcher: EventDispatcher
    watcher: WatcherClient | None
    metric_registry: CommonMetricRegistry
    background_task_manager: BackgroundTaskManager
    cors_options: Mapping[str, aiohttp_cors.ResourceOptions]

    # volume backend states
    backends: MutableMapping[str, type[AbstractVolume]]
    volumes: MutableMapping[str, AbstractVolume]

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {name: info.to_dataclass() for name, info in self.local_config.volume.items()}

    @asynccontextmanager
    async def get_volume(self, name: str) -> AsyncIterator[AbstractVolume]:
        if name in self.volumes:
            yield self.volumes[name]
        else:
            try:
                volume_config = self.local_config.volume[name]
            except KeyError:
                raise InvalidVolumeError(name)
            volume_cls: type[AbstractVolume] = self.backends[volume_config.backend]
            volume_obj = volume_cls(
                local_config=self.local_config.model_dump(by_alias=True),
                mount_path=Path(volume_config.path),
                options=volume_config.options or {},
                etcd=self.etcd,
                event_dispatcher=self.event_dispatcher,
                event_producer=self.event_producer,
                watcher=self.watcher,
            )

            await volume_obj.init()
            self.volumes[name] = volume_obj

            yield volume_obj

    async def shutdown_volumes(self) -> None:
        for volume in self.volumes.values():
            await volume.shutdown()
