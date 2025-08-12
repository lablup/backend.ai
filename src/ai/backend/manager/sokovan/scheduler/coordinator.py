import logging
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType

from .handlers import (
    CheckPreconditionHandler,
    ScheduleHandler,
    ScheduleSessionsHandler,
    StartSessionsHandler,
    TerminateSessionsHandler,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.schedule.repository import MarkTerminatingResult
    from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

log = BraceStyleAdapter(logging.getLogger(__name__))


class ScheduleCoordinator:
    """
    Coordinate scheduling operations based on scheduling needs.
    Handles the actual scheduling logic and state management.
    """

    _valkey_schedule: ValkeyScheduleClient
    _scheduler: "Scheduler"
    _event_producer: EventProducer
    _schedule_handlers: dict[ScheduleType, ScheduleHandler]
    _scheduler_dispatcher: SchedulerDispatcher

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        scheduler: "Scheduler",
        event_producer: EventProducer,
        scheduler_dispatcher: SchedulerDispatcher,
    ) -> None:
        self._valkey_schedule = valkey_schedule
        self._scheduler = scheduler
        self._event_producer = event_producer
        self._scheduler_dispatcher = scheduler_dispatcher

        # Initialize handlers for each schedule type
        self._schedule_handlers = {
            ScheduleType.SCHEDULE: ScheduleSessionsHandler(scheduler, self),
            ScheduleType.CHECK_PRECONDITION: CheckPreconditionHandler(
                scheduler, self, self._scheduler_dispatcher
            ),
            ScheduleType.START: StartSessionsHandler(scheduler, self, self._scheduler_dispatcher),
            ScheduleType.TERMINATE: TerminateSessionsHandler(scheduler, self),
        }

    async def process_schedule(
        self,
        schedule_type: ScheduleType,
    ) -> bool:
        """
        Force processing of a specific schedule type.
        This method processes the scheduling operation even if it was not requested for guaranteed execution.
        So it should be called in long term loops.

        :param schedule_type: Type of scheduling operation
        :return: True if operation was performed, False otherwise
        """
        try:
            log.debug("Processing schedule type: {}", schedule_type.value)

            # Get handler from map and execute
            handler = self._schedule_handlers.get(schedule_type)
            if not handler:
                log.warning("No handler for schedule type: {}", schedule_type.value)
                return False

            # Execute the handler (includes operation and post-processing)
            await handler.handle()
            return True
        except Exception as e:
            log.exception(
                "Error processing schedule type {}: {}",
                schedule_type.value,
                e,
            )
            # No re-queueing as per user request
            raise

    async def process_if_needed(self, schedule_type: ScheduleType) -> bool:
        """
        Process scheduling operation if needed (based on internal state).
        This method checks if the scheduling operation was requested and processes it if so.

        :param schedule_type: Type of scheduling operation
        :return: True if operation was performed, False otherwise
        """
        # Check internal state (uses Redis marks)
        if not await self._valkey_schedule.load_and_delete_schedule_mark(schedule_type.value):
            return False

        return await self.process_schedule(schedule_type)

    async def request_scheduling(self, schedule_type: ScheduleType) -> None:
        """
        Request a scheduling operation for the next cycle.

        :param schedule_type: Type of scheduling to request
        """
        await self._valkey_schedule.mark_schedule_needed(schedule_type.value)
        log.debug("Requested scheduling for type: {}", schedule_type.value)

    async def start(self) -> None:
        """
        Start the scheduling process.
        """
        await self._scheduler_dispatcher.start("do_start_session")
        log.debug("Starting scheduling process")

    async def check_preconditions(self):
        """
        Check preconditions for scheduling.
        """
        await self._scheduler_dispatcher.check_precond("do_check_precond")
        log.debug("Checking preconditions for scheduling")

    async def mark_sessions_for_termination(
        self,
        session_ids: list[str],
        reason: str = "USER_REQUESTED",
    ) -> "MarkTerminatingResult":
        """
        Mark multiple sessions and their kernels for termination by updating their status to TERMINATING.
        This provides fast response to users by only updating the status and returning immediately.
        Also requests the TERMINATE scheduling operation for the next cycle.

        :param session_ids: List of session IDs to terminate
        :param reason: Reason for termination
        :return: MarkTerminatingResult with categorized session statuses
        """
        # Use the internal scheduler method to mark sessions
        result = await self._scheduler._mark_sessions_for_termination(session_ids, reason)

        # Request termination scheduling for the next cycle if there are sessions to terminate
        if result.has_processed():
            await self.request_scheduling(ScheduleType.TERMINATE)
            log.info(
                "Marked {} sessions for termination and requested TERMINATE scheduling",
                result.processed_count(),
            )

        return result
