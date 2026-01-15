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
from ai.backend.common.types import AccessKey, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.hooks.registry import HookRegistry
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))


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
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Execute on_transition_to_terminated hooks and prepare for TERMINATED transition.

        This handler needs to:
        1. Use provided SessionWithKernels data for hook execution
        2. Execute cleanup hooks (best-effort, don't block termination)
        3. Update sessions via repository
        4. Return successes for status transition
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        log.info(
            "session types to terminate: {}",
            [s.session_info.metadata.session_type for s in sessions],
        )

        # Execute hooks concurrently (best-effort - failures don't block termination)
        hook_coroutines = [
            self._hook_registry.get_hook(
                session.session_info.metadata.session_type
            ).on_transition_to_terminated(session)
            for session in sessions
        ]

        with RecorderContext[SessionId].shared_phase(
            "finalize_termination",
            success_detail="Session termination finalized",
        ):
            hook_results = await asyncio.gather(*hook_coroutines, return_exceptions=True)

        # All sessions proceed to termination regardless of hook failures
        for session, hook_result in zip(sessions, hook_results, strict=True):
            session_info = session.session_info
            if isinstance(hook_result, BaseException):
                log.error(
                    "Termination hook failed with exception for session {} (will still terminate): {}",
                    session_info.identity.id,
                    hook_result,
                )
            # Always include in successes - termination always proceeds
            result.successes.append(
                SessionTransitionInfo(
                    session_id=session_info.identity.id,
                    from_status=session_info.lifecycle.status,
                )
            )
            result.scheduled_data.append(
                ScheduledSessionData(
                    session_id=session_info.identity.id,
                    creation_id=session_info.identity.creation_id,
                    access_key=AccessKey(session_info.metadata.access_key),
                    reason=session_info.lifecycle.status_info or "unknown",
                )
            )

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
