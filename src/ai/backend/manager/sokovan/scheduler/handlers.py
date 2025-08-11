"""
Schedule operation handlers that bundle the operation with its post-processing logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import DoCheckPrecondEvent
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.scheduler.types import ScheduleType

from .results import ScheduleResult

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
    from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

log = BraceStyleAdapter(logging.getLogger(__name__))


class ScheduleHandler(ABC):
    """Base class for schedule operation handlers."""

    _scheduler: "Scheduler"
    _coordinator: "ScheduleCoordinator"
    _event_producer: EventProducer

    def __init__(
        self,
        scheduler: "Scheduler",
        coordinator: "ScheduleCoordinator",
        event_producer: EventProducer,
    ):
        self._scheduler = scheduler
        self._coordinator = coordinator
        self._event_producer = event_producer

    @abstractmethod
    async def execute(self) -> ScheduleResult:
        """Execute the scheduling operation.

        Returns:
            Result of the scheduling operation
        """
        ...

    @abstractmethod
    async def post_process(self, result: ScheduleResult) -> None:
        """Handle post-processing after the operation.

        Args:
            result: The result from execute()
        """
        ...

    @final
    async def handle(self) -> ScheduleResult:
        """Execute the operation and run post-processing."""
        result = await self.execute()
        if result.needs_post_processing():
            await self.post_process(result)
        return result


class ScheduleSessionsHandler(ScheduleHandler):
    """Handler for scheduling pending sessions."""

    async def execute(self) -> ScheduleResult:
        """Schedule all pending sessions across scaling groups."""
        return await self._scheduler.schedule_all_scaling_groups()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request precondition check if sessions were scheduled."""
        # Request next phase
        await self._coordinator.request_scheduling(ScheduleType.CHECK_PRECONDITION)
        # Also trigger event for backward compatibility
        await self._event_producer.anycast_event(DoCheckPrecondEvent())
        log.info("Scheduled {} sessions, requesting precondition check", result.succeeded_count)


class CheckPreconditionHandler(ScheduleHandler):
    """Handler for checking session preconditions."""

    async def execute(self) -> ScheduleResult:
        """Check preconditions for scheduled sessions."""
        # TODO: Implement when method is added to Scheduler
        log.info("Checking preconditions (not yet implemented)")
        return ScheduleResult()
        # return await self._scheduler.check_preconditions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if preconditions are met."""
        await self._coordinator.request_scheduling(ScheduleType.START)
        log.info("Checked {} sessions, requesting start", result.succeeded_count)


class StartSessionsHandler(ScheduleHandler):
    """Handler for starting sessions."""

    async def execute(self) -> ScheduleResult:
        """Start sessions that passed precondition checks."""
        # TODO: Implement when method is added to Scheduler
        log.info("Starting sessions (not yet implemented)")
        return ScheduleResult()
        # return await self._scheduler.start_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of started sessions."""
        log.info("Started {} sessions", result.succeeded_count)


class TerminateSessionsHandler(ScheduleHandler):
    """Handler for terminating sessions."""

    async def execute(self) -> ScheduleResult:
        """Terminate sessions marked for termination."""
        # TODO: Implement when method is added to Scheduler
        log.info("Terminating sessions (not yet implemented)")
        return ScheduleResult()
        # return await self._scheduler.terminate_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of terminated sessions."""
        log.info("Terminated {} sessions", result.succeeded_count)
