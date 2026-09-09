"""The session adapter, assembled for one row.

A session read answers through a service whose constructor demands eleven dependencies.
Ten of them are named unwired here, so a row that reaches one fails saying which rather
than passing against a mock that answered on its own.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.runner.unwired import unwired

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.idle_checker.processors import IdleCheckerProcessors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: tuple[ActionValidators, V2ActionValidators],
    monitors: ActionMonitors,
) -> SessionAdapter:
    _, v2_validators = validators
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=v2_validators,
            repository=OpsRepository(provider),
        )
    )
    service = SessionService(
        SessionServiceArgs(
            # The one a read reaches: get and search both go straight to it.
            session_repository=SessionRepository(engine, DBOpsProvider(engine)),
            # The ten it does not.
            scheduler_repository=unwired(SchedulerRepository, "only scheduling reads it"),
            user_repository=unwired(UserRepository, "only writes resolve the owner"),
            agent_registry=unwired(AgentRegistry, "only session writes reach the agents"),
            event_fetcher=unwired(EventFetcher, "only long-running work waits on events"),
            background_task_manager=unwired(BackgroundTaskManager, "only background work"),
            event_hub=unwired(EventHub, "only long-running work publishes"),
            error_monitor=unwired(ErrorPluginContext, "only failing writes report"),
            idle_checker_host=unwired(IdleCheckerHost, "only idle checks reach it"),
            scheduling_controller=unwired(SchedulingController, "only enqueue schedules"),
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
