"""The agent adapter, assembled for one row.

The reads run through the ops and the agent repository. The watcher, the registry and
the scheduling controller are reached only by calls no row makes, so each refuses.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.bulk.validator.rbac import BulkOwnCheck
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)
from bai_scenario.runner.unwired import unwired
from bai_scenario.valkey import ScenarioValkey


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    valkey: ScenarioValkey,
) -> AgentAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    permission_check = RbacPermissionCheckRepository(PermissionOpsProvider(engine), config)
    return AgentAdapter(
        AgentProcessors(
            registry.group(GroupMeta(AgentEntityType())),
            AgentService(
                etcd=unwired(AsyncEtcd, "only the watcher calls read etcd"),
                agent_registry=unwired(AgentRegistry, "no row writes an agent"),
                config_provider=config,
                agent_repository=AgentRepository(
                    engine,
                    unwired(ValkeyImageClient, "no row reads the images an agent installed"),
                    unwired(ValkeyLiveClient, "no row reads a live agent's health"),
                    valkey.stat,
                    config,
                    ShareOpsProvider(engine),
                ),
                scheduler_repository=SchedulerRepository(
                    engine,
                    ReconcileOpsProvider(engine),
                    valkey.stat,
                    valkey.schedule,
                    config,
                    unwired(StorageSessionManager, "no row reaches a storage host"),
                    permission_check,
                ),
                scheduling_controller=unwired(
                    SchedulingController, "no row leaves a kernel running on the agent"
                ),
                own_check=BulkOwnCheck(permission_check),
            ),
        )
    )
