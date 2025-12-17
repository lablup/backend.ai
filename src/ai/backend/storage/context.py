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
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.health_checker.probe import HealthProbe
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.logging import BraceStyleAdapter

from .client.manager import ManagerHTTPClientPool
from .config.unified import StorageProxyUnifiedConfig
from .context_types import ArtifactVerifierContext
from .errors import InvalidVolumeError
from .plugin import (
    StorageArtifactVerifierPluginContext,
)
from .services.service import VolumeService
from .storages.storage_pool import StoragePool
from .types import VolumeInfo
from .volumes.abc import AbstractVolume
from .volumes.cephfs import CephFSVolume
from .volumes.ddn import EXAScalerFSVolume
from .volumes.dellemc import DellEMCOneFSVolume
from .volumes.gpfs import GPFSVolume
from .volumes.hammerspace.volume.base import BaseHammerspaceVolume
from .volumes.hammerspace.volume.extended import HammerspaceVolume
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
    BaseHammerspaceVolume.name: BaseHammerspaceVolume,
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
    manager_client_pool: ManagerHTTPClientPool
    valkey_artifact_client: ValkeyArtifactDownloadTrackingClient
    health_probe: HealthProbe

    # volume backend states
    backends: MutableMapping[str, type[AbstractVolume]]
    volumes: MutableMapping[str, AbstractVolume]
    artifact_verifier_ctx: ArtifactVerifierContext

    async def init_storage_artifact_verifier_plugin(self) -> None:
        plugin_ctx = StorageArtifactVerifierPluginContext(self.etcd, self.local_config.model_dump())
        await plugin_ctx.init()
        plugins = {}
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            log.info("Loading artifact verifier storage plugin: {0}", plugin_name)
            plugins[plugin_name] = plugin_instance
        self.artifact_verifier_ctx.load_verifiers(plugins)

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

    async def shutdown_manager_http_clients(self) -> None:
        """Close all manager HTTP client sessions."""
        await self.manager_client_pool.cleanup()
