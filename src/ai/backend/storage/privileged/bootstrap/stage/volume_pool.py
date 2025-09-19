from dataclasses import dataclass
from typing import override

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)

from ....volumes.pool import VolumePool
from ...config import StorageProxyPrivilegedWorkerConfig


@dataclass
class VolumePoolSpec:
    local_config: StorageProxyPrivilegedWorkerConfig
    etcd: AsyncEtcd
    event_dispatcher: EventDispatcher
    event_producer: EventProducer


class VolumePoolSpecGenerator(ArgsSpecGenerator[VolumePoolSpec]):
    pass


@dataclass
class VolumePoolResult:
    volume_pool: VolumePool


class VolumePoolProvisioner(Provisioner[VolumePoolSpec, VolumePoolResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-volume-pool"

    @override
    async def setup(self, spec: VolumePoolSpec) -> VolumePoolResult:
        volume_pool = await VolumePool.create(
            local_config=spec.local_config,
            etcd=spec.etcd,
            event_dispatcher=spec.event_dispatcher,
            event_producer=spec.event_producer,
        )
        return VolumePoolResult(volume_pool)

    @override
    async def teardown(self, resource: VolumePoolResult) -> None:
        pass


class VolumePoolStage(ProvisionStage[VolumePoolSpec, VolumePoolResult]):
    pass
