from collections.abc import Iterable
from dataclasses import dataclass
from typing import override

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)

from ....bgtask.tasks.delete import VFolderDeleteTaskHandler
from ....volumes.pool import VolumePool


@dataclass
class BgtaskManagerSpec:
    volume_pool: VolumePool
    valkey_client: ValkeyBgtaskClient
    event_producer: EventProducer
    node_id: str
    tags: Iterable[str]


class BgtaskManagerSpecGenerator(ArgsSpecGenerator[BgtaskManagerSpec]):
    pass


@dataclass
class BgtaskManagerResult:
    bgtask_mgr: BackgroundTaskManager


class BgtaskManagerProvisioner(Provisioner[BgtaskManagerSpec, BgtaskManagerResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-bgtask"

    @override
    async def setup(self, spec: BgtaskManagerSpec) -> BgtaskManagerResult:
        registry = self._register_bgtask_handlers(spec.volume_pool, spec.event_producer)
        bgtask_mgr = BackgroundTaskManager(
            event_producer=spec.event_producer,
            task_registry=registry,
            valkey_client=spec.valkey_client,
            server_id=spec.node_id,
            tags=spec.tags,
        )
        return BgtaskManagerResult(bgtask_mgr)

    def _register_bgtask_handlers(
        self, volume_pool: VolumePool, event_producer: EventProducer
    ) -> BackgroundTaskHandlerRegistry:
        registry = BackgroundTaskHandlerRegistry()
        registry.register(VFolderDeleteTaskHandler(volume_pool, event_producer))
        return registry

    @override
    async def teardown(self, resource: BgtaskManagerResult) -> None:
        pass


class BgtaskManagerStage(ProvisionStage[BgtaskManagerSpec, BgtaskManagerResult]):
    pass
