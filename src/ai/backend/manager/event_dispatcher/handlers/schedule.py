import logging
from typing import TYPE_CHECKING

from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.events.event_types.schedule.anycast import (
    DoCheckPrecondEvent,
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
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScheduleEventHandler:
    _scheduler_dispatcher: SchedulerDispatcher
    _schedule_coordinator: "ScheduleCoordinator"
    _use_sokovan: bool

    def __init__(
        self,
        scheduler_dispatcher: SchedulerDispatcher,
        schedule_coordinator: "ScheduleCoordinator",
        use_sokovan: bool = False,
    ) -> None:
        self._scheduler_dispatcher = scheduler_dispatcher
        self._schedule_coordinator = schedule_coordinator
        self._use_sokovan = use_sokovan

    async def handle_session_enqueued(
        self, context: None, agent_id: str, ev: SessionEnqueuedAnycastEvent
    ) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle
            await self._schedule_coordinator.request_scheduling(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_session_terminated(
        self, context: None, agent_id: str, ev: SessionTerminatedAnycastEvent
    ) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle
            await self._schedule_coordinator.request_scheduling(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_agent_started(
        self, context: None, agent_id: str, ev: AgentStartedEvent
    ) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle
            await self._schedule_coordinator.request_scheduling(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_do_schedule(self, context: None, agent_id: str, ev: DoScheduleEvent) -> None:
        if self._use_sokovan:
            # Request scheduling for next cycle
            await self._schedule_coordinator.request_scheduling(ScheduleType.SCHEDULE)
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_do_start_session(
        self, context: None, agent_id: str, ev: DoStartSessionEvent
    ) -> None:
        if self._use_sokovan:
            # Process start if needed (checks mark)
            await self._schedule_coordinator.request_scheduling(ScheduleType.START)
        else:
            await self._scheduler_dispatcher.start(ev.event_name())

    async def handle_do_check_precond(
        self, context: None, agent_id: str, ev: DoCheckPrecondEvent
    ) -> None:
        if self._use_sokovan:
            # Process check precondition if needed (checks mark)
            await self._schedule_coordinator.request_scheduling(ScheduleType.CHECK_PRECONDITION)
        else:
            await self._scheduler_dispatcher.check_precond(ev.event_name())

    async def handle_do_scale(self, context: None, agent_id: str, ev: DoScaleEvent) -> None:
        await self._scheduler_dispatcher.scale_services(ev.event_name())

    async def handle_do_update_session_status(
        self, context: None, agent_id: str, ev: DoUpdateSessionStatusEvent
    ) -> None:
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
