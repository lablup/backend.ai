from dataclasses import dataclass
from typing import override

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.lock import EtcdLock
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class EtcdLockSpec:
    etcd: AsyncEtcd


class EtcdLockProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "etcd-lock-provisioner"

    @override
    async def setup(self, spec: EtcdLockSpec) -> DistributedLockFactory:
        return lambda lock_id, lifetime_hint: EtcdLock(
            str(lock_id),
            spec.etcd,
            lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
        )

    @override
    async def teardown(self, resource: DistributedLockFactory) -> None:
        # Nothing to clean up
        pass
