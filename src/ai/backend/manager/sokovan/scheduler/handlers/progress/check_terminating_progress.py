"""Handler for checking terminating progress of sessions."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.handlers.base import (
    SchedulerHandler,
    SessionLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.hooks.registry import HookRegistry
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    ScheduledSessionData,
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckTerminatingProgressHandler(SchedulerHandler):
    """Handler for checking if TERMINATING sessions are ready to transition to TERMINATED.

    DEPRECATED: Use CheckTerminatingProgressLifecycleHandler instead.
    """

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
    ) -> None:
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
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.SCHEDULE)
        log.info("{} sessions transitioned to TERMINATED state", len(result.scheduled_sessions))

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        await self._repository.invalidate_kernel_related_cache(list(affected_keys))
        log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))

        # Broadcast batch event for sessions that transitioned to TERMINATED
        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.TERMINATED),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_sessions
        ]
        await self._event_producer.broadcast_events_batch(events)


class CheckTerminatingProgressLifecycleHandler(SessionLifecycleHandler):
    """Handler for checking if TERMINATING sessions are ready to transition to TERMINATED.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with TERMINATING status and ALL kernels TERMINATED
    - Handler executes on_transition_to_terminated hooks
    - Handler updates sessions to TERMINATED via repository
    - Coordinator applies status transition to TERMINATED

    Note: This handler executes cleanup hooks (best-effort) before termination.
    """

    def __init__(
        self,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
        hook_registry: HookRegistry,
    ) -> None:
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository
        self._hook_registry = hook_registry

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-terminating-progress"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in TERMINATING state."""
        return [SessionStatus.TERMINATING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Only include sessions where ALL kernels are TERMINATED."""
        return [KernelStatus.TERMINATED]

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """Sessions transition to TERMINATED on success."""
        return SessionStatus.TERMINATED

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status - termination always proceeds."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """No stale status for this handler."""
        return None

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[HandlerSessionData],
    ) -> SessionExecutionResult:
        """Execute on_transition_to_terminated hooks and prepare for TERMINATED transition.

        This handler needs to:
        1. Fetch full session data for hook execution
        2. Execute cleanup hooks (best-effort, don't block termination)
        3. Update sessions via repository
        4. Return successes for status transition
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Get session IDs for fetching full data
        session_ids = [s.session_id for s in sessions]

        # Fetch full transition data for hook execution
        sessions_data = await self._repository.get_sessions_for_transition(
            [SessionStatus.TERMINATING],
            [KernelStatus.TERMINATED],
        )

        # Filter to only sessions in our batch
        session_id_set = set(session_ids)
        sessions_data = [s for s in sessions_data if s.session_id in session_id_set]

        if not sessions_data:
            return result

        log.info("session types to terminate: {}", [s.session_type for s in sessions_data])

        # Execute hooks concurrently (best-effort - failures don't block termination)
        hook_coroutines = [
            self._hook_registry.get_hook(session_data.session_type).on_transition_to_terminated(
                session_data
            )
            for session_data in sessions_data
        ]

        hook_results = await asyncio.gather(*hook_coroutines, return_exceptions=True)

        # All sessions proceed to termination regardless of hook failures
        for session_data, hook_result in zip(sessions_data, hook_results, strict=True):
            if isinstance(hook_result, BaseException):
                log.error(
                    "Termination hook failed with exception for session {} (will still terminate): {}",
                    session_data.session_id,
                    hook_result,
                )
            # Always include in successes - termination always proceeds
            result.successes.append(session_data.session_id)
            result.scheduled_data.append(
                ScheduledSessionData(
                    session_id=session_data.session_id,
                    creation_id=session_data.creation_id,
                    access_key=session_data.access_key,
                    reason=session_data.status_info or "unknown",
                )
            )

        # Update sessions to TERMINATED via repository
        if result.successes:
            await self._repository.update_sessions_to_terminated(result.successes)

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Invalidate cache and broadcast events for terminated sessions."""
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.SCHEDULE)
        log.info("{} sessions transitioned to TERMINATED state", len(result.scheduled_data))

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_data
        }
        await self._repository.invalidate_kernel_related_cache(list(affected_keys))
        log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))

        # Broadcast batch event for sessions that transitioned to TERMINATED
        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.TERMINATED),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_data
        ]
        await self._event_producer.broadcast_events_batch(events)
