"""Handler for starting sessions."""

import logging
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

from .base import SchedulerHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class StartSessionsHandler(SchedulerHandler):
    """Handler for starting sessions."""

    def __init__(
        self,
        scheduler: Scheduler,
        event_producer: EventProducer,
    ):
        self._scheduler = scheduler
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "start-sessions"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(self) -> ScheduleResult:
        """Start sessions that passed precondition checks."""
        return await self._scheduler.start_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of started sessions and broadcast event."""
        log.info("Started {} sessions", len(result.scheduled_sessions))

        # Broadcast batch event for started sessions
        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.CREATING),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_sessions
        ]
        await self._event_producer.broadcast_events_batch(events)
