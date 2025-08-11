"""
Schedule operation handlers that bundle the operation with its post-processing logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType

from .results import ScheduleResult

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
    from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

log = BraceStyleAdapter(logging.getLogger(__name__))


class ScheduleHandler(ABC):
    """Base class for schedule operation handlers."""

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

    def __init__(
        self,
        scheduler: "Scheduler",
        coordinator: "ScheduleCoordinator",
    ):
        self._scheduler = scheduler
        self._coordinator = coordinator

    async def execute(self) -> ScheduleResult:
        """Schedule all pending sessions across scaling groups."""
        log.trace("Scheduling sessions across all scaling groups")
        return await self._scheduler.schedule_all_scaling_groups()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request precondition check if sessions were scheduled."""
        # Request next phase
        await self._coordinator.request_scheduling(ScheduleType.CHECK_PRECONDITION)
        log.trace("Scheduled {} sessions, requesting precondition check", result.succeeded_count)


class CheckPreconditionHandler(ScheduleHandler):
    """Handler for checking session preconditions."""

    def __init__(
        self,
        scheduler: "Scheduler",
        coordinator: "ScheduleCoordinator",
        dispatcher: "SchedulerDispatcher",
    ):
        self._scheduler = scheduler
        self._coordinator = coordinator
        self._dispatcher = dispatcher

    async def execute(self) -> ScheduleResult:
        """Check preconditions for scheduled sessions."""
        # TODO: Remove dispatcher
        await self._dispatcher.check_precond("do_check_precond")
        log.debug("Checking preconditions")
        return ScheduleResult()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if preconditions are met."""
        log.trace("Checked {} sessions, requesting start", result.succeeded_count)


class StartSessionsHandler(ScheduleHandler):
    """Handler for starting sessions."""

    def __init__(
        self,
        scheduler: "Scheduler",
        coordinator: "ScheduleCoordinator",
        dispatcher: "SchedulerDispatcher",
    ):
        self._scheduler = scheduler
        self._coordinator = coordinator
        self._dispatcher = dispatcher

    async def execute(self) -> ScheduleResult:
        """Start sessions that passed precondition checks."""
        # TODO: Remove dispatcher
        await self._dispatcher.start("do_start_session")
        log.debug("Starting sessions")
        return ScheduleResult()
        # return await self._scheduler.start_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of started sessions."""
        log.trace("Started {} sessions", result.succeeded_count)


class TerminateSessionsHandler(ScheduleHandler):
    """Handler for terminating sessions."""

    def __init__(
        self,
        scheduler: "Scheduler",
        coordinator: "ScheduleCoordinator",
    ):
        self._scheduler = scheduler
        self._coordinator = coordinator

    async def execute(self) -> ScheduleResult:
        """Terminate sessions marked for termination."""
        return await self._scheduler.terminate_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of terminated sessions."""
        log.trace("Terminated {} sessions", result.succeeded_count)
