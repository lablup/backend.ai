import logging

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import (
    DoCheckPrecondEvent,
    DoStartSessionEvent,
)
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

    async def handle_check_precond_event(self) -> None:
        """
        Handle check precondition event by checking and pulling images for SCHEDULED sessions.

        This transitions sessions from SCHEDULED to PREPARING state.
        """
        try:
            # Check preconditions for all SCHEDULED sessions
            processed_count = await self._scheduler.check_preconditions_all()

            # Note: Actual image pulling is triggered by the dispatcher
            # which monitors PREPARING state and calls AgentRegistry.check_and_pull_images()

            log.debug("handle_check_precond_event(): Processed {} sessions", processed_count)

        except Exception as e:
            log.exception("handle_check_precond_event(): precondition check error: {}", repr(e))
            raise

    async def handle_start_session_event(self) -> None:
        """
        Handle start session event by marking PREPARED sessions as CREATING.

        This transitions sessions from PREPARED to CREATING state.
        The actual container creation is handled by the dispatcher calling AgentRegistry.start_session().
        """
        try:
            # Mark PREPARED sessions as CREATING
            started_count = await self._scheduler.start_sessions_all()

            # Note: The actual container creation is handled by the dispatcher
            # which monitors CREATING sessions and calls AgentRegistry.start_session()

            log.debug("handle_start_session_event(): Marked {} sessions as CREATING", started_count)

        except Exception as e:
            log.exception("handle_start_session_event(): session start error: {}", repr(e))
            raise
