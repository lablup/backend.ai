from dataclasses import dataclass
from typing import override

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)

from ....config.loaders import make_etcd
from ...config import StorageProxyPrivilegedWorkerConfig


@dataclass
class EtcdSpec:
    local_config: StorageProxyPrivilegedWorkerConfig


class EtcdSpecGenerator(ArgsSpecGenerator[EtcdSpec]):
    pass


@dataclass
class EtcdResult:
    etcd: AsyncEtcd


class EtcdProvisioner(Provisioner[EtcdSpec, EtcdResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-etcd"

    @override
    async def setup(self, spec: EtcdSpec) -> EtcdResult:
        etcd = make_etcd(spec.local_config)
        return EtcdResult(etcd)

    @override
    async def teardown(self, resource: EtcdResult) -> None:
        pass


class EtcdStage(ProvisionStage[EtcdSpec, EtcdResult]):
    pass
