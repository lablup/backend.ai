import logging

from ai.backend.common.events.agent import AgentStartedEvent
from ai.backend.common.events.schedule import (
    DoCheckPrecondEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoStartSessionEvent,
)
from ai.backend.common.events.session import (
    DoUpdateSessionStatusEvent,
    SessionEnqueuedEvent,
    SessionTerminatedEvent,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScheduleEventHandler:
    _scheduler_dispatcher: SchedulerDispatcher

    def __init__(self, scheduler_dispatcher: SchedulerDispatcher) -> None:
        self._scheduler_dispatcher = scheduler_dispatcher

    async def handle_session_enqueued(
        self, context: None, agent_id: str, ev: SessionEnqueuedEvent
    ) -> None:
        await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_session_terminated(
        self, context: None, agent_id: str, ev: SessionTerminatedEvent
    ) -> None:
        await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_agent_started(
        self, context: None, agent_id: str, ev: AgentStartedEvent
    ) -> None:
        await self._scheduler_dispatcher.schedule(ev.event_name())

    async def handle_do_schedule(self, context: None, agent_id: str, ev: DoScheduleEvent) -> None:
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
