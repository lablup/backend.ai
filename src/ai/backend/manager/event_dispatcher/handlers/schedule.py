import logging

from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.events.event_types.schedule.anycast import (
    DoCheckPrecondEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoStartSessionEvent,
)
from ai.backend.common.events.event_types.session.anycast import (
    DoUpdateSessionStatusEvent,
    SessionEnqueuedAnycastEvent,
    SessionTerminatedAnycastEvent,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.sokovan.sokovan import SokovanOrchestrator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScheduleEventHandler:
    _scheduler_dispatcher: SchedulerDispatcher
    _sokovan_orchestrator: SokovanOrchestrator
    _use_sokovan: bool

    def __init__(
        self,
        scheduler_dispatcher: SchedulerDispatcher,
        sokovan_orchestrator: SokovanOrchestrator,
        use_sokovan: bool = False,
    ) -> None:
        self._scheduler_dispatcher = scheduler_dispatcher
        self._sokovan_orchestrator = sokovan_orchestrator
        self._use_sokovan = use_sokovan

    async def handle_session_enqueued(
        self, context: None, agent_id: str, ev: SessionEnqueuedAnycastEvent
    ) -> None:
        if self._use_sokovan:
            await self._sokovan_orchestrator.handle_schedule_event()
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_session_terminated(
        self, context: None, agent_id: str, ev: SessionTerminatedAnycastEvent
    ) -> None:
        if self._use_sokovan:
            await self._sokovan_orchestrator.handle_schedule_event()
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_agent_started(
        self, context: None, agent_id: str, ev: AgentStartedEvent
    ) -> None:
        if self._use_sokovan:
            await self._sokovan_orchestrator.handle_schedule_event()
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_do_schedule(self, context: None, agent_id: str, ev: DoScheduleEvent) -> None:
        if self._use_sokovan:
            await self._sokovan_orchestrator.handle_schedule_event()
        else:
            await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_do_start_session(
        self, context: None, agent_id: str, ev: DoStartSessionEvent
    ) -> None:
        await self._scheduler_dispatcher.start(ev.event_name())

    async def handle_do_check_precond(
        self, context: None, agent_id: str, ev: DoCheckPrecondEvent
    ) -> None:
        await self._scheduler_dispatcher.check_precond(ev.event_name())

    async def handle_do_scale(self, context: None, agent_id: str, ev: DoScaleEvent) -> None:
        await self._scheduler_dispatcher.scale_services(ev.event_name())

    async def handle_do_update_session_status(
        self, context: None, agent_id: str, ev: DoUpdateSessionStatusEvent
    ) -> None:
        await self._scheduler_dispatcher.update_session_status()
