import logging

from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.events.event_types.schedule.anycast import (
    DoCheckPrecondEvent,
    DoDeploymentLifecycleEvent,
    DoDeploymentLifecycleIfNeededEvent,
    DoRouteLifecycleEvent,
    DoRouteLifecycleIfNeededEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoSokovanProcessIfNeededEvent,
    DoSokovanProcessScheduleEvent,
    DoStartSessionEvent,
)
from ai.backend.common.events.event_types.session.anycast import (
    DoUpdateSessionStatusEvent,
    SessionEnqueuedAnycastEvent,
    SessionTerminatedAnycastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScheduleEventHandler:
    _scheduler_dispatcher: SchedulerDispatcher
    _schedule_coordinator: ScheduleCoordinator
    _scheduling_controller: SchedulingController
    _deployment_coordinator: DeploymentCoordinator
    _route_coordinator: RouteCoordinator
    _event_hub: EventHub
    _use_sokovan: bool

    def __init__(
        self,
        scheduler_dispatcher: SchedulerDispatcher,
        schedule_coordinator: ScheduleCoordinator,
        scheduling_controller: SchedulingController,
        deployment_coordinator: DeploymentCoordinator,
        route_coordinator: RouteCoordinator,
        event_hub: EventHub,
        use_sokovan: bool = False,
    ) -> None:
        self._scheduler_dispatcher = scheduler_dispatcher
        self._schedule_coordinator = schedule_coordinator
        self._scheduling_controller = scheduling_controller
        self._deployment_coordinator = deployment_coordinator
        self._route_coordinator = route_coordinator
        self._event_hub = event_hub
        self._use_sokovan = use_sokovan

    async def handle_session_enqueued(
        self, context: None, agent_id: str, ev: SessionEnqueuedAnycastEvent
    ) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle through SchedulingController
            await self._scheduling_controller.mark_scheduling_needed(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_session_terminated(
        self, context: None, agent_id: str, ev: SessionTerminatedAnycastEvent
    ) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle through SchedulingController
            await self._scheduling_controller.mark_scheduling_needed(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_agent_started(
        self, context: None, agent_id: str, ev: AgentStartedEvent
    ) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle through SchedulingController
            await self._scheduling_controller.mark_scheduling_needed(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_do_schedule(self, context: None, agent_id: str, ev: DoScheduleEvent) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle through SchedulingController
            await self._scheduling_controller.mark_scheduling_needed(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_do_start_session(
        self, context: None, agent_id: str, ev: DoStartSessionEvent
    ) -> None:
        if self._use_sokovan:
            # Request start scheduling through SchedulingController
            await self._scheduling_controller.mark_scheduling_needed(ScheduleType.START)
        else:
            await self._scheduler_dispatcher.start(ev.event_name())

    async def handle_do_check_precond(
        self, context: None, agent_id: str, ev: DoCheckPrecondEvent
    ) -> None:
        if self._use_sokovan:
            # Request check precondition through SchedulingController
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_PRECONDITION
            )
        else:
            await self._scheduler_dispatcher.check_precond(ev.event_name())

    async def handle_do_scale(self, context: None, agent_id: str, ev: DoScaleEvent) -> None:
        if not self._use_sokovan:
            await self._scheduler_dispatcher.scale_services(ev.event_name())

    async def handle_do_update_session_status(
        self, context: None, agent_id: str, ev: DoUpdateSessionStatusEvent
    ) -> None:
        if not self._use_sokovan:
            await self._scheduler_dispatcher.update_session_status()

    async def handle_do_sokovan_process_if_needed(
        self, context: None, agent_id: str, ev: DoSokovanProcessIfNeededEvent
    ) -> None:
        """Handle Sokovan process if needed event (checks marks)."""
        if self._use_sokovan:
            schedule_type = ScheduleType(ev.schedule_type)
            await self._schedule_coordinator.process_if_needed(schedule_type)

    async def handle_do_sokovan_process_schedule(
        self, context: None, agent_id: str, ev: DoSokovanProcessScheduleEvent
    ) -> None:
        """Handle Sokovan process schedule event (unconditional)."""
        if self._use_sokovan:
            schedule_type = ScheduleType(ev.schedule_type)
            await self._schedule_coordinator.process_schedule(schedule_type)

    async def handle_scheduling_broadcast(
        self, context: None, source: AgentId, ev: SchedulingBroadcastEvent
    ) -> None:
        """Handle scheduling broadcast event (individual)."""
        if self._use_sokovan:
            await self._event_hub.propagate_event(ev)

    async def handle_do_deployment_lifecycle_if_needed(
        self, context: None, agent_id: str, ev: DoDeploymentLifecycleIfNeededEvent
    ) -> None:
        """Handle deployment lifecycle if needed event (checks marks)."""
        if self._use_sokovan:
            lifecycle_type = DeploymentLifecycleType(ev.lifecycle_type)
            await self._deployment_coordinator.process_if_needed(lifecycle_type)

    async def handle_do_deployment_lifecycle(
        self, context: None, agent_id: str, ev: DoDeploymentLifecycleEvent
    ) -> None:
        """Handle deployment lifecycle event (unconditional)."""
        if self._use_sokovan:
            lifecycle_type = DeploymentLifecycleType(ev.lifecycle_type)
            await self._deployment_coordinator.process_deployment_lifecycle(lifecycle_type)

    async def handle_do_route_lifecycle_if_needed(
        self, context: None, agent_id: str, ev: DoRouteLifecycleIfNeededEvent
    ) -> None:
        """Handle route lifecycle if needed event (checks marks)."""
        if self._use_sokovan:
            lifecycle_type = RouteLifecycleType(ev.lifecycle_type)
            await self._route_coordinator.process_if_needed(lifecycle_type)

    async def handle_do_route_lifecycle(
        self, context: None, agent_id: str, ev: DoRouteLifecycleEvent
    ) -> None:
        """Handle route lifecycle event (unconditional)."""
        if self._use_sokovan:
            lifecycle_type = RouteLifecycleType(ev.lifecycle_type)
            await self._route_coordinator.process_route_lifecycle(lifecycle_type)
