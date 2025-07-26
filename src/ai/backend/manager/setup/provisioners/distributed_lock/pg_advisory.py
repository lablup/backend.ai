from dataclasses import dataclass
from typing import override

from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.pglock import PgAdvisoryLock
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class PgAdvisoryLockSpec:
    db: ExtendedAsyncSAEngine


class PgAdvisoryLockProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "pg-advisory-lock-provisioner"

    @override
    async def setup(self, spec: PgAdvisoryLockSpec) -> DistributedLockFactory:
        return lambda lock_id, lifetime_hint: PgAdvisoryLock(spec.db, lock_id)

    @override
    async def teardown(self, resource: DistributedLockFactory) -> None:
        # Nothing to clean up
        pass
