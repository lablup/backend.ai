"""
Schedule operation handlers that bundle the operation with its post-processing logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import final

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .results import ScheduleResult

log = BraceStyleAdapter(logging.getLogger(__name__))

__all__ = [
    "ScheduleHandler",
    "ScheduleSessionsHandler",
    "CheckPreconditionHandler",
    "StartSessionsHandler",
    "TerminateSessionsHandler",
    "SweepSessionsHandler",
    "CheckPullingProgressHandler",
    "CheckCreatingProgressHandler",
    "CheckTerminatingProgressHandler",
    "RetryPreparingHandler",
    "RetryCreatingHandler",
]


class ScheduleHandler(ABC):
    """Base class for schedule operation handlers."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        raise NotImplementedError("Subclasses must implement name()")

    @abstractmethod
    async def execute(self) -> ScheduleResult:
        """Execute the scheduling operation.

        Returns:
            Result of the scheduling operation
        """
        raise NotImplementedError("Subclasses must implement execute()")

    @abstractmethod
    async def post_process(self, result: ScheduleResult) -> None:
        """Handle post-processing after the operation.

        Args:
            result: The result from execute()
        """
        raise NotImplementedError("Subclasses must implement post_process()")

    @final
    async def handle(self) -> ScheduleResult:
        """Execute the operation and run post-processing."""
        result = await self.execute()
        if result.needs_post_processing():
            try:
                await self.post_process(result)
            except Exception as e:
                log.error("Error during post-processing: {}", e)
        return result


class ScheduleSessionsHandler(ScheduleHandler):
    """Handler for scheduling pending sessions."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "schedule-sessions"

    async def execute(self) -> ScheduleResult:
        """Schedule all pending sessions across scaling groups."""
        log.trace("Scheduling sessions across all scaling groups")
        return await self._scheduler.schedule_all_scaling_groups()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request precondition check if sessions were scheduled."""
        # Request next phase
        await self._scheduling_controller.request_scheduling(ScheduleType.CHECK_PRECONDITION)
        log.info("Scheduled {} sessions, requesting precondition check", result.succeeded_count)


class CheckPreconditionHandler(ScheduleHandler):
    """Handler for checking session preconditions."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-precondition"

    async def execute(self) -> ScheduleResult:
        """Check preconditions for scheduled sessions."""
        return await self._scheduler.check_preconditions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if preconditions are met."""
        log.info("Checked preconditions for {} sessions", result.succeeded_count)
        await self._scheduling_controller.request_scheduling(ScheduleType.START)


class StartSessionsHandler(ScheduleHandler):
    """Handler for starting sessions."""

    def __init__(
        self,
        scheduler: Scheduler,
    ):
        self._scheduler = scheduler

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "start-sessions"

    async def execute(self) -> ScheduleResult:
        """Start sessions that passed precondition checks."""
        return await self._scheduler.start_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of started sessions."""
        log.info("Started {} sessions", result.succeeded_count)


class TerminateSessionsHandler(ScheduleHandler):
    """Handler for terminating sessions."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "terminate-sessions"

    async def execute(self) -> ScheduleResult:
        """Terminate sessions marked for termination."""
        return await self._scheduler.terminate_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of terminated sessions."""
        log.info("Terminated {} sessions", result.succeeded_count)


class SweepSessionsHandler(ScheduleHandler):
    """Handler for sweeping stale sessions (maintenance operation)."""

    def __init__(
        self,
        scheduler: Scheduler,
    ):
        self._scheduler = scheduler

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-sessions"

    async def execute(self) -> ScheduleResult:
        """Sweep stale sessions including those with pending timeout."""
        return await self._scheduler.sweep_stale_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of swept sessions."""
        log.info("Swept {} stale sessions", result.succeeded_count)


class CheckPullingProgressHandler(ScheduleHandler):
    """Handler for checking if PULLING or PREPARING sessions are ready to transition to PREPARED."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-pulling-progress"

    async def execute(self) -> ScheduleResult:
        """Check if sessions in PULLING state have all kernels ready."""
        return await self._scheduler.check_pulling_progress()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request START scheduling if sessions transitioned to PREPARED."""
        log.info("{} sessions transitioned to PREPARED state", result.succeeded_count)


class CheckCreatingProgressHandler(ScheduleHandler):
    """Handler for checking if CREATING sessions are ready to transition to RUNNING."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-creating-progress"

    async def execute(self) -> ScheduleResult:
        """Check if sessions in CREATING state have all kernels running."""
        return await self._scheduler.check_creating_progress()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of sessions that transitioned to RUNNING."""
        log.info("{} sessions transitioned to RUNNING state", result.succeeded_count)
        await self._scheduling_controller.request_scheduling(ScheduleType.START)


class CheckTerminatingProgressHandler(ScheduleHandler):
    """Handler for checking if TERMINATING sessions are ready to transition to TERMINATED."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-terminating-progress"

    async def execute(self) -> ScheduleResult:
        """Check if sessions in TERMINATING state have all kernels terminated."""
        return await self._scheduler.check_terminating_progress()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of sessions that transitioned to TERMINATED."""
        log.info("{} sessions transitioned to TERMINATED state", result.succeeded_count)
        await self._scheduling_controller.request_scheduling(ScheduleType.SCHEDULE)


# Time thresholds for health checks
PREPARING_CHECK_THRESHOLD = 900.0  # 15 minutes
CREATING_CHECK_THRESHOLD = 600.0  # 10 minutes


class RetryPreparingHandler(ScheduleHandler):
    """Handler for retrying PREPARING/PULLING sessions that appear stuck."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "retry-preparing"

    async def execute(self) -> ScheduleResult:
        """Check and retry stuck PREPARING/PULLING sessions."""
        log.debug("Checking for stuck PREPARING/PULLING sessions to retry")

        # Call scheduler method to handle retry logic
        return await self._scheduler.retry_preparing_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request precondition check if sessions were retried."""
        log.info("Retried {} stuck PREPARING/PULLING sessions", result.succeeded_count)


class RetryCreatingHandler(ScheduleHandler):
    """Handler for retrying CREATING sessions that appear stuck."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "retry-creating"

    async def execute(self) -> ScheduleResult:
        """Check and retry stuck CREATING sessions."""
        log.debug("Checking for stuck CREATING sessions to retry")

        # Call scheduler method to handle retry logic
        return await self._scheduler.retry_creating_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if sessions were retried."""
        log.info("Retried {} stuck CREATING sessions", result.succeeded_count)
