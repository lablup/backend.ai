from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.storage.client.manager import ManagerHTTPClientPool
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.dependencies.infrastructure.redis import StorageProxyValkeyClients
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.volumes.abc import AbstractVolume
from ai.backend.storage.volumes.pool import VolumePool
from ai.backend.storage.watcher import WatcherClient

from .bgtask import BackgroundTaskManagerInput, BackgroundTaskManagerProvider
from .manager_client_pool import ManagerClientPoolProvider
from .storage_pool import StoragePoolInput, StoragePoolProvider
from .volume_pool import VolumePoolInput, VolumePoolProvider
from .volume_stats import VolumeStatsInput, VolumeStatsProvider, VolumeStatsResources
from .watcher import WatcherInput, WatcherProvider


@dataclass
class StorageComposerInput:
    """Input for Storage composer."""

    local_config: StorageProxyUnifiedConfig
    pidx: int
    etcd: AsyncEtcd
    valkey: StorageProxyValkeyClients
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    backends: Mapping[str, type[AbstractVolume]]


@dataclass
class StorageResources:
    """All storage resources for storage proxy."""

    storage_pool: StoragePool
    volume_pool: VolumePool
    background_task_manager: BackgroundTaskManager
    watcher: WatcherClient | None
    volume_stats: VolumeStatsResources
    manager_client_pool: ManagerHTTPClientPool


class StorageComposer(DependencyComposer[StorageComposerInput, StorageResources]):
    """Composer for storage layer dependencies."""

    @property
    @override
    def stage_name(self) -> str:
        return "storage"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: StorageComposerInput,
    ) -> AsyncIterator[StorageResources]:
        """Compose all storage dependencies."""
        local_config = setup_input.local_config

        storage_pool = await stack.enter_dependency(
            StoragePoolProvider(),
            StoragePoolInput(local_config=local_config, pidx=setup_input.pidx),
        )
        volume_pool = await stack.enter_dependency(
            VolumePoolProvider(),
            VolumePoolInput(
                local_config=local_config,
                etcd=setup_input.etcd,
                event_dispatcher=setup_input.event_dispatcher,
                event_producer=setup_input.event_producer,
                backends=setup_input.backends,
            ),
        )
        background_task_manager = await stack.enter_dependency(
            BackgroundTaskManagerProvider(),
            BackgroundTaskManagerInput(
                event_producer=setup_input.event_producer,
                valkey_bgtask=setup_input.valkey.bgtask,
                volume_pool=volume_pool,
                server_id=local_config.storage_proxy.node_id,
            ),
        )
        watcher = await stack.enter_dependency(
            WatcherProvider(),
            WatcherInput(local_config=local_config, pidx=setup_input.pidx),
        )
        volume_stats = await stack.enter_dependency(
            VolumeStatsProvider(),
            VolumeStatsInput(
                local_config=local_config,
                volume_pool=volume_pool,
                valkey_volume_stats=setup_input.valkey.volume_stats,
            ),
        )
        manager_client_pool = await stack.enter_dependency(
            ManagerClientPoolProvider(),
            local_config,
        )

        yield StorageResources(
            storage_pool=storage_pool,
            volume_pool=volume_pool,
            background_task_manager=background_task_manager,
            watcher=watcher,
            volume_stats=volume_stats,
            manager_client_pool=manager_client_pool,
        )
