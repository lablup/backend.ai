"""The session adapter, assembled for one row.

A session read answers through a service whose constructor demands eleven dependencies.
Three of them run against the real database and the real Valkey server, one is a fake
agent, and the other seven are named unwired, so a row that reaches one fails saying
which.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.kernel import KernelFieldType
from ai.backend.common.data.entity.kernel_group import KernelGroupFieldType
from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironFieldType
from ai.backend.common.data.entity.kernel_group_resource_slot import (
    KernelGroupResourceSlotFieldType,
)
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.kernel_group.types import (
    KernelGroupData,
    KernelGroupEnvironData,
    KernelGroupResourceSlotData,
)
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.idle_checker.service import IdleCheckerService
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_environ_owner import (
    LookupBulkKernelGroupEnvironOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_owner import (
    LookupBulkKernelGroupOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_resource_slot_owner import (
    LookupBulkKernelGroupResourceSlotOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    LookupBulkKernelOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_field_owner import (
    LookupKernelFieldOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_group_environ_field_owner import (
    LookupKernelGroupEnvironFieldOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_group_field_owner import (
    LookupKernelGroupFieldOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_group_resource_slot_field_owner import (
    LookupKernelGroupResourceSlotFieldOwnerAction,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import (
    create_agent_selector,
)
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
from bai_scenario.fakes.agent import FakeAgentRegistry
from bai_scenario.fakes.events import SilentEventProducer
from bai_scenario.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    FakeStorageSessionManager,
)
from bai_scenario.runner.unwired import unwired
from bai_scenario.valkey import ScenarioValkey


@pytest.fixture
def storage() -> FakeStorageProxyManagerFacingClient:
    return FakeStorageProxyManagerFacingClient()


@pytest.fixture
def agent_registry() -> AgentRegistry:
    """The agent answers what a session service call reads off it, and nothing else."""
    return cast("AgentRegistry", FakeAgentRegistry())


@pytest.fixture
def fakes(storage: FakeStorageProxyManagerFacingClient) -> Sequence[object]:
    """What a ``then`` may read off the outside."""
    return (storage,)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    storage: FakeStorageProxyManagerFacingClient,
    agent_registry: AgentRegistry,
    valkey: ScenarioValkey,
) -> SessionAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    session_group = registry.group(GroupMeta(SessionEntityType()))
    scheduler_repository = SchedulerRepository(
        engine,
        ReconcileOpsProvider(engine),
        valkey.stat,
        valkey.schedule,
        config,
        FakeStorageSessionManager({"local": storage}),
        RbacPermissionCheckRepository(PermissionOpsProvider(engine), config),
        key_provider_pool=KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )
    service = SessionService(
        SessionServiceArgs(
            session_repository=SessionRepository(
                engine, provider, registry_db_source=ContainerRegistryDBSource(provider)
            ),
            scheduler_repository=scheduler_repository,
            user_repository=unwired(UserRepository, "only writes resolve the owner"),
            agent_registry=agent_registry,
            event_fetcher=unwired(EventFetcher, "only long-running work waits on events"),
            background_task_manager=unwired(BackgroundTaskManager, "only background work"),
            event_hub=unwired(EventHub, "only long-running work publishes"),
            error_monitor=unwired(ErrorPluginContext, "only failing writes report"),
            idle_checker_host=unwired(IdleCheckerHost, "only idle checks reach it"),
            scheduling_controller=SchedulingController(
                SchedulingControllerArgs(
                    repository=scheduler_repository,
                    config_provider=config,
                    storage_manager=FakeStorageSessionManager({"local": storage}),
                    event_producer=SilentEventProducer(),
                    valkey_schedule=valkey.schedule,
                    network_plugin_ctx=unwired(
                        NetworkPluginContext, "no session asks for a network"
                    ),
                    # No plugin is loaded, so the pre-enqueue hook dispatches to nobody.
                    hook_plugin_ctx=HookPluginContext(MagicMock(spec=AbstractKVStore), {}),
                    agent_selector=create_agent_selector(
                        config.config.manager.agent_selection_resource_priority
                    ),
                )
            ),
            appproxy_client_pool=unwired(AppProxyClientPool, "only app routes reach it"),
        )
    )
    idle_checker_service = IdleCheckerService(
        IdleCheckerRepository(engine, RelationOpsProvider(engine), provider),
        PrometheusQueryPresetRepository(
            engine,
            unwired(PrometheusClient, "no idle checker reads prometheus"),
            provider,
        ),
        OpsRepository(provider),
    )
    return SessionAdapter(
        SessionProcessors(
            session_group,
            registry.group(GroupMeta(ResourceGroupEntityType())),
            session_group.field_group(
                FieldGroupMeta(KernelFieldType()),
                KernelInfo,
                LookupKernelFieldOwnerAction,
                LookupBulkKernelOwnerAction,
            ),
            session_group.field_group(
                FieldGroupMeta(KernelGroupFieldType()),
                KernelGroupData,
                LookupKernelGroupFieldOwnerAction,
                LookupBulkKernelGroupOwnerAction,
            ),
            session_group.field_group(
                FieldGroupMeta(KernelGroupEnvironFieldType()),
                KernelGroupEnvironData,
                LookupKernelGroupEnvironFieldOwnerAction,
                LookupBulkKernelGroupEnvironOwnerAction,
            ),
            session_group.field_group(
                FieldGroupMeta(KernelGroupResourceSlotFieldType()),
                KernelGroupResourceSlotData,
                LookupKernelGroupResourceSlotFieldOwnerAction,
                LookupBulkKernelGroupResourceSlotOwnerAction,
            ),
            unwired(ResourceAllocationProcessors, "only allocation reads reach it"),
            service,
        ),
        IdleCheckerProcessors(
            registry.group(GroupMeta(IdleCheckerEntityType())),
            session_group,
            idle_checker_service,
        ),
    )
