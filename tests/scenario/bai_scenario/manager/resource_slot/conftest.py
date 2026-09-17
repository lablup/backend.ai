"""The resource slot adapter, assembled for every row of its tables.

The slot type rows run through the slot type processors alone. The agent resource
rows reach the agent processors for the name lookup and the scoped search, and the
domain overview rows reach the domain processors for the name lookup. Neither of those
reaches its service, so the agent service is built on dependencies that refuse.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.bulk.validator.rbac import BulkOwnCheck
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_slot.repository import ResourceSlotRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.resource_slot.service import ResourceSlotService
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from bai_scenario.runner.unwired import unwired


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ResourceSlotAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return ResourceSlotAdapter(
        ResourceSlotProcessors(
            registry.group(GroupMeta(ResourceSlotTypeEntityType())),
            registry.group(GroupMeta(SessionEntityType())),
            registry.group(GroupMeta(AgentEntityType())),
            ResourceSlotService(ResourceSlotRepository(engine)),
        ),
        AgentProcessors(
            registry.group(GroupMeta(AgentEntityType())),
            AgentService(
                etcd=unwired(AsyncEtcd, "only the watcher calls read etcd"),
                agent_registry=unwired(AgentRegistry, "only agent writes reach the registry"),
                config_provider=unwired(ManagerConfigProvider, "only the watcher calls read it"),
                agent_repository=unwired(
                    AgentRepository, "the lookup and the scoped search go through the ops"
                ),
                scheduler_repository=unwired(SchedulerRepository, "only scheduling reaches it"),
                scheduling_controller=unwired(SchedulingController, "only scheduling reaches it"),
                own_check=unwired(BulkOwnCheck, "only the permission loads reach it"),
            ),
        ),
        DomainProcessors(
            registry.group(GroupMeta(DomainEntityType())),
            DomainService(DomainRepository(engine, provider)),
        ),
    )
