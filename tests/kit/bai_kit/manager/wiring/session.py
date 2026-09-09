"""Session wiring.

Third of the shapes tried, and the one that does not fit cheaply. Domain and model card
answer reads straight from the ops path; session answers even a read through a service
whose constructor demands eleven dependencies. Ten of them are named here as unwired,
so a scenario that reaches one fails saying which, rather than passing against a mock
that answered on its own.
"""

from __future__ import annotations

from typing import Any

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
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
from ai.backend.testutils.typed_scenario import op
from bai_kit.manager.runner import Wired, WiringDeps
from bai_kit.manager.unwired import unwired

DISPATCH: dict[type, str] = {
    AdminSearchSessionsInput: "admin_search",
}


def session_wiring(deps: WiringDeps) -> Wired:
    provider = V2DBOpsProvider(deps.engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=deps.monitors,
            validators=deps.v2_validators,
            repository=OpsRepository(provider),
        )
    )
    service = SessionService(
        SessionServiceArgs(
            # The one a read reaches: get and search both go straight to it.
            session_repository=SessionRepository(deps.engine, DBOpsProvider(deps.engine)),
            # The ten it does not. Named rather than mocked, so a scenario that turns
            # out to need one fails saying which.
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
    session = SessionProcessors(
        registry.group(GroupMeta(SessionEntityType())),
        registry.group(GroupMeta(ResourceGroupEntityType())),
        unwired(ResourceAllocationProcessors, "only allocation reads reach it"),
        service,
    )
    adapter = SessionAdapter(
        session,
        unwired(IdleCheckerProcessors, "only idle-check reads reach it"),
    )
    return Wired(adapter=adapter, dispatch=DISPATCH, client_attr="session")


# ---------------------------------------------------------------------------
# The operations a session scenario may name
# ---------------------------------------------------------------------------

search_sessions = op(SessionAdapter.admin_search)
my_sessions = op(SessionAdapter.my_search)
get_session = op(SessionAdapter.get)
