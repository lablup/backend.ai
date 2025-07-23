from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost, init_idle_checkers
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.setup.messaging.event_producer import EventProducerResource
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class IdleCheckerSpec:
    database: ExtendedAsyncSAEngine
    config_provider: ManagerConfigProvider
    event_producer_resource: EventProducerResource
    distributed_lock_factory: DistributedLockFactory


class IdleCheckerProvisioner(Provisioner[IdleCheckerSpec, IdleCheckerHost]):
    @property
    def name(self) -> str:
        return "idle_checker"

    async def setup(self, spec: IdleCheckerSpec) -> IdleCheckerHost:
        idle_checker_host = await init_idle_checkers(
            spec.database,
            spec.config_provider,
            spec.event_producer_resource.event_producer,
            spec.distributed_lock_factory,
        )
        await idle_checker_host.start()
        return idle_checker_host

    async def teardown(self, resource: IdleCheckerHost) -> None:
        await resource.shutdown()