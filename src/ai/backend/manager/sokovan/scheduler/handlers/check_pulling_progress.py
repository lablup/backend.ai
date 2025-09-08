"""Handler for checking pulling progress of sessions."""

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
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .base import SchedulerHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckPullingProgressHandler(SchedulerHandler):
    """Handler for checking if PULLING or PREPARING sessions are ready to transition to PREPARED."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-pulling-progress"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARING/PULLING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(self) -> ScheduleResult:
        """Check if sessions in PULLING state have all kernels ready."""
        return await self._scheduler.check_pulling_progress()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request START scheduling if sessions transitioned to PREPARED."""
        log.info("{} sessions transitioned to PREPARED state", len(result.scheduled_sessions))

        # Broadcast batch event for sessions that transitioned to PREPARED
        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.PREPARED),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_sessions
        ]
        await self._event_producer.broadcast_events_batch(events)
