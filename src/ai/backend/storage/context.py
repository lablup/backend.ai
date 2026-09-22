from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import (
    Final,
)

import aiohttp_cors

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_tus.client import (
    ValkeyTusClient,
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
from .plugin import (
    StorageArtifactVerifierPluginContext,
)
from .services.service import VolumeService
from .storages.storage_pool import StoragePool
from .types import VolumeInfo
from .volumes.abc import AbstractVolume
from .volumes.pool import VolumePool
from .volumes.stats import VolumeState, VolumeStatsObserver
from .watcher import WatcherClient

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "storage-proxy"


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
    valkey_tus_client: ValkeyTusClient
    health_probe: HealthProbe
    volume_stats_observer: VolumeStatsObserver
    volume_stats_state: VolumeState

    # volume backend states
    backends: MutableMapping[str, type[AbstractVolume]]
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
