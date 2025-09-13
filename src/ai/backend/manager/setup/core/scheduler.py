from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.setup.core.agent_registry import AgentRegistryResource
from ai.backend.manager.setup.infrastructure.redis import ValkeyClients
from ai.backend.manager.setup.messaging.event_producer import EventProducerResource
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class SchedulerDispatcherSpec:
    config_provider: ManagerConfigProvider
    etcd: AsyncEtcd
    event_producer_resource: EventProducerResource
    distributed_lock_factory: DistributedLockFactory
    agent_registry_resource: AgentRegistryResource
    valkey_clients: ValkeyClients
    repositories: Repositories


class SchedulerDispatcherProvisioner(Provisioner[SchedulerDispatcherSpec, SchedulerDispatcher]):
    @property
    def name(self) -> str:
        return "scheduler_dispatcher"

    async def setup(self, spec: SchedulerDispatcherSpec) -> SchedulerDispatcher:
        scheduler_dispatcher = await SchedulerDispatcher.create(
            spec.config_provider,
            spec.etcd,
            spec.event_producer_resource.event_producer,
            spec.distributed_lock_factory,
            spec.agent_registry_resource.registry,
            spec.valkey_clients.valkey_live,
            spec.valkey_clients.valkey_stat,
            spec.repositories.schedule.repository,
        )
        return scheduler_dispatcher

    async def teardown(self, resource: SchedulerDispatcher) -> None:
        await resource.close()