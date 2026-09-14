"""The session adapter, assembled for one row.

A session read answers through a service whose constructor demands eleven dependencies.
Three of them run against the real database and the real Valkey server; the other eight
are named unwired, so a row that reaches one fails saying which.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock

import pytest
from bai_scenario.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    FakeStorageSessionManager,
)
from bai_scenario.runner.unwired import unwired
from bai_scenario.valkey import ScenarioValkey

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentSelector
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)


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
) -> SessionAdapter:
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
    )
    service = SessionService(
        SessionServiceArgs(
            session_repository=SessionRepository(engine),
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
                    event_producer=unwired(EventProducer, "nothing here waits on the event"),
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
    return SessionAdapter(
        SessionProcessors(
            registry.group(GroupMeta(SessionEntityType())),
            registry.group(GroupMeta(ResourceGroupEntityType())),
            unwired(ResourceAllocationProcessors, "only allocation reads reach it"),
            service,
        ),
        unwired(IdleCheckerProcessors, "only idle-check reads reach it"),
    )
