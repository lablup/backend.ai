"""
Schedule operation handlers that bundle the operation with its post-processing logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    BatchSchedulingBroadcastEvent,
    SessionSchedulingEventData,
)
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
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

    @property
    @abstractmethod
    def lock_id(self) -> Optional[LockID]:
        """Get the lock ID for this handler.

        Returns:
            LockID to acquire before execution, or None if no lock needed
        """
        raise NotImplementedError("Subclasses must implement lock_id")

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


class ScheduleSessionsHandler(ScheduleHandler):
    """Handler for scheduling pending sessions."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "schedule-sessions"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PENDING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PENDING

    async def execute(self) -> ScheduleResult:
        """Schedule all pending sessions across scaling groups."""
        log.trace("Scheduling sessions across all scaling groups")
        return await self._scheduler.schedule_all_scaling_groups()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request precondition check if sessions were scheduled and invalidate cache."""
        # Request next phase first
        await self._scheduling_controller.request_scheduling(ScheduleType.CHECK_PRECONDITION)
        log.info(
            "Scheduled {} sessions, requesting precondition check", len(result.scheduled_sessions)
        )

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            session.access_key for session in result.scheduled_sessions
        }
        await self._repository.invalidate_keypair_concurrency_cache(list(affected_keys))
        log.debug("Invalidated concurrency cache for {} access keys", len(affected_keys))

        # Broadcast batch event for scheduled sessions
        event = BatchSchedulingBroadcastEvent(
            session_events=[
                SessionSchedulingEventData(
                    session_id=event_data.session_id,
                    creation_id=event_data.creation_id,
                )
                for event_data in result.scheduled_sessions
            ],
            status_transition=str(SessionStatus.SCHEDULED),
        )
        await self._event_producer.broadcast_event(event)


class CheckPreconditionHandler(ScheduleHandler):
    """Handler for checking session preconditions."""

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
        return "check-precondition"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(self) -> ScheduleResult:
        """Check preconditions for scheduled sessions."""
        return await self._scheduler.check_preconditions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if preconditions are met."""
        # Request next phase first
        log.info("Checked preconditions for {} sessions", len(result.scheduled_sessions))
        await self._scheduling_controller.request_scheduling(ScheduleType.START)

        # Broadcast batch event for sessions that passed precondition check
        event = BatchSchedulingBroadcastEvent(
            session_events=[
                SessionSchedulingEventData(
                    session_id=event_data.session_id,
                    creation_id=event_data.creation_id,
                )
                for event_data in result.scheduled_sessions
            ],
            status_transition=str(SessionStatus.PREPARING),  # Sessions transition to PREPARING
        )
        await self._event_producer.broadcast_event(event)


class StartSessionsHandler(ScheduleHandler):
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
        event = BatchSchedulingBroadcastEvent(
            session_events=[
                SessionSchedulingEventData(
                    session_id=event_data.session_id,
                    creation_id=event_data.creation_id,
                )
                for event_data in result.scheduled_sessions
            ],
            status_transition=str(SessionStatus.CREATING),
        )
        await self._event_producer.broadcast_event(event)


class TerminateSessionsHandler(ScheduleHandler):
    """Handler for terminating sessions."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "terminate-sessions"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Terminate sessions marked for termination."""
        return await self._scheduler.terminate_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of terminated sessions and invalidate cache."""
        log.info("Try to terminate {} sessions", len(result.scheduled_sessions))
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        await self._repository.invalidate_keypair_concurrency_cache(list(affected_keys))


class SweepSessionsHandler(ScheduleHandler):
    """Handler for sweeping stale sessions (maintenance operation)."""

    def __init__(
        self,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ):
        self._scheduler = scheduler
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-sessions"

    @property
    def lock_id(self) -> Optional[LockID]:
        """No lock needed for sweeping stale sessions."""
        return None

    async def execute(self) -> ScheduleResult:
        """Sweep stale sessions including those with pending timeout."""
        return await self._scheduler.sweep_stale_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of swept sessions."""
        log.info("Swept {} stale sessions", len(result.scheduled_sessions))
        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        await self._repository.invalidate_keypair_concurrency_cache(list(affected_keys))
        log.debug("Invalidated concurrency cache for {} access keys", len(affected_keys))


class CheckPullingProgressHandler(ScheduleHandler):
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
        if result.scheduled_sessions:
            event = BatchSchedulingBroadcastEvent(
                session_events=[
                    SessionSchedulingEventData(
                        session_id=event_data.session_id,
                        creation_id=event_data.creation_id,
                    )
                    for event_data in result.scheduled_sessions
                ],
                status_transition=str(SessionStatus.PREPARED),
            )
            await self._event_producer.broadcast_event(event)


class CheckCreatingProgressHandler(ScheduleHandler):
    """Handler for checking if CREATING sessions are ready to transition to RUNNING."""

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
        return "check-creating-progress"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(self) -> ScheduleResult:
        """Check if sessions in CREATING state have all kernels running."""
        return await self._scheduler.check_creating_progress()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of sessions that transitioned to RUNNING."""
        await self._scheduling_controller.request_scheduling(ScheduleType.START)
        log.info("{} sessions transitioned to RUNNING state", len(result.scheduled_sessions))

        # Broadcast batch event for sessions that transitioned to RUNNING
        if result.scheduled_sessions:
            event = BatchSchedulingBroadcastEvent(
                session_events=[
                    SessionSchedulingEventData(
                        session_id=event_data.session_id,
                        creation_id=event_data.creation_id,
                    )
                    for event_data in result.scheduled_sessions
                ],
                status_transition=str(SessionStatus.RUNNING),
            )
            await self._event_producer.broadcast_event(event)


class CheckTerminatingProgressHandler(ScheduleHandler):
    """Handler for checking if TERMINATING sessions are ready to transition to TERMINATED."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-terminating-progress"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Check if sessions in TERMINATING state have all kernels terminated."""
        return await self._scheduler.check_terminating_progress()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of sessions that transitioned to TERMINATED and invalidate cache."""
        await self._scheduling_controller.request_scheduling(ScheduleType.SCHEDULE)
        log.info("{} sessions transitioned to TERMINATED state", len(result.scheduled_sessions))

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        await self._repository.invalidate_keypair_concurrency_cache(list(affected_keys))
        log.debug("Invalidated concurrency cache for {} access keys", len(affected_keys))

        # Broadcast batch event for sessions that transitioned to TERMINATED
        if result.scheduled_sessions:
            event = BatchSchedulingBroadcastEvent(
                session_events=[
                    SessionSchedulingEventData(
                        session_id=event_data.session_id,
                        creation_id=event_data.creation_id,
                    )
                    for event_data in result.scheduled_sessions
                ],
                status_transition=str(SessionStatus.TERMINATED),
            )
            await self._event_producer.broadcast_event(event)


# Time thresholds for health checks
PREPARING_CHECK_THRESHOLD = 900.0  # 15 minutes
CREATING_CHECK_THRESHOLD = 600.0  # 10 minutes


class RetryPreparingHandler(ScheduleHandler):
    """Handler for retrying PREPARING/PULLING sessions that appear stuck."""

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
        return "retry-preparing"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARING sessions (retry)."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(self) -> ScheduleResult:
        """Check and retry stuck PREPARING/PULLING sessions."""
        log.debug("Checking for stuck PREPARING/PULLING sessions to retry")

        # Call scheduler method to handle retry logic
        return await self._scheduler.retry_preparing_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request precondition check if sessions were retried."""
        log.info("Retried {} stuck PREPARING/PULLING sessions", len(result.scheduled_sessions))


class RetryCreatingHandler(ScheduleHandler):
    """Handler for retrying CREATING sessions that appear stuck."""

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
        return "retry-creating"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions (retry)."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(self) -> ScheduleResult:
        """Check and retry stuck CREATING sessions."""
        log.debug("Checking for stuck CREATING sessions to retry")

        # Call scheduler method to handle retry logic
        return await self._scheduler.retry_creating_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if sessions were retried."""
        log.info("Retried {} stuck CREATING sessions", len(result.scheduled_sessions))
