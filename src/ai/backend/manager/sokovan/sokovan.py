import logging

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import DoCheckPrecondEvent
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

log = BraceStyleAdapter(logging.getLogger(__name__))


class SokovanOrchestrator:
    """
    Orchestrator for Sokovan scheduler that handles schedule events.
    """

    def __init__(
        self,
        scheduler: Scheduler,
        event_producer: EventProducer,
    ) -> None:
        self._scheduler = scheduler
        self._event_producer = event_producer

    async def handle_schedule_event(self) -> None:
        """
        Handle schedule event by triggering the Sokovan scheduler.

        The distributed lock and actual scheduling logic is handled by the Scheduler.
        """
        try:
            # Delegate to scheduler which handles locking internally
            # Returns True if any sessions were scheduled
            scheduled_session_count = await self._scheduler.schedule_all_scaling_groups()

            # Trigger check precondition event only if sessions were actually scheduled
            if scheduled_session_count > 0:
                await self._event_producer.anycast_event(DoCheckPrecondEvent())

        except Exception as e:
            log.exception("handle_schedule_event(): scheduling error: {}", repr(e))
            raise
