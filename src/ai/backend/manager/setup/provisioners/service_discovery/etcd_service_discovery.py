from dataclasses import dataclass
from typing import override

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.stage.types import Provisioner


@dataclass
class EtcdServiceDiscoverySpec:
    etcd: AsyncEtcd


class EtcdServiceDiscoveryProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "etcd-service-discovery-provisioner"

    @override
    async def setup(self, spec: EtcdServiceDiscoverySpec) -> ETCDServiceDiscovery:
        return ETCDServiceDiscovery(ETCDServiceDiscoveryArgs(spec.etcd))

    @override
    async def teardown(self, resource: ETCDServiceDiscovery) -> None:
        # Nothing to clean up
        pass
