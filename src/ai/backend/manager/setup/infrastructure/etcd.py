from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.stage.types import Provisioner


@dataclass
class EtcdSpec:
    config: EtcdConfigData


class EtcdProvisioner(Provisioner[EtcdSpec, AsyncEtcd]):
    @property
    def name(self) -> str:
        return "etcd"

    async def setup(self, spec: EtcdSpec) -> AsyncEtcd:
        return AsyncEtcd.initialize(spec.config)

    async def teardown(self, resource: AsyncEtcd) -> None:
        await resource.close()
