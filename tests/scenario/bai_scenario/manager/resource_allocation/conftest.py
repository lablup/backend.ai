"""The resource allocation adapter, assembled for one row.

Every usage read reaches the resource allocation processors, which take a real
repository over the database and the config provider. The session processors worn
around them demand a session service that no row here reaches, so it is built with the
dependencies the session tables use and the rest named unwired.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.kernel import KernelFieldType
from ai.backend.common.data.entity.kernel_group import KernelGroupFieldType
from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironFieldType
from ai.backend.common.data.entity.kernel_group_resource_slot import (
    KernelGroupResourceSlotFieldType,
)
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.resource_allocation.adapter import (
    ResourceAllocationAdapter,
)
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.kernel_group.types import (
    KernelGroupData,
    KernelGroupEnvironData,
    KernelGroupResourceSlotData,
)
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_allocation.provider import (
    ResourceAllocationOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.resource_allocation.repository import (
    ResourceAllocationRepository,
)
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
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
from ai.backend.manager.services.session.resource_allocation.service import (
    ResourceAllocationService,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentSelector
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
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
    valkey: ScenarioValkey,
) -> ResourceAllocationAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    scheduler_repository = SchedulerRepository(
        engine,
        ReconcileOpsProvider(engine),
        valkey.stat,
        valkey.schedule,
        config,
        FakeStorageSessionManager({"local": storage}),
        RbacPermissionCheckRepository(PermissionOpsProvider(engine), config),
    )
    session_group = registry.group(GroupMeta(SessionEntityType()))
    resource_allocation = ResourceAllocationProcessors(
        user=registry.group(GroupMeta(UserEntityType())),
        project=registry.group(GroupMeta(ProjectEntityType())),
        domain=registry.group(GroupMeta(DomainEntityType())),
        resource_group=registry.group(GroupMeta(ResourceGroupEntityType())),
        session=session_group,
        resource_preset=registry.group(GroupMeta(ResourcePresetEntityType())),
        service=ResourceAllocationService(
            ResourceAllocationRepository(engine, ResourceAllocationOpsProvider(engine), config),
            ResourcePresetRepository(engine, config, ShareOpsProvider(engine)),
        ),
    )
    service = SessionService(
        SessionServiceArgs(
            session_repository=SessionRepository(
                engine, provider, registry_db_source=ContainerRegistryDBSource(provider)
            ),
            scheduler_repository=scheduler_repository,
            user_repository=unwired(UserRepository, "only writes resolve the owner"),
            agent_registry=unwired(AgentRegistry, "only session writes reach the agents"),
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
                    agent_selector=unwired(AgentSelector, "only scheduling picks an agent"),
                )
            ),
            appproxy_client_pool=unwired(AppProxyClientPool, "only app routes reach it"),
        )
    )
    return ResourceAllocationAdapter(
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
            resource_allocation,
            service,
        ),
        DomainProcessors(
            registry.group(GroupMeta(DomainEntityType())),
            registry.concern(ConcernMeta(Concern.ORGANIZATION)).relation_group(),
            DomainService(DomainRepository(engine, DomainOpsProvider(engine))),
        ),
        config,
    )
