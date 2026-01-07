"""Handler for checking pulling progress of sessions."""

from __future__ import annotations

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
from ai.backend.manager.sokovan.scheduler.handlers.base import (
    SchedulerHandler,
    SessionLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckPullingProgressHandler(SchedulerHandler):
    """Handler for checking if PULLING or PREPARING sessions are ready to transition to PREPARED.

    DEPRECATED: Use CheckPullingProgressLifecycleHandler instead.
    """

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
    ) -> None:
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


class CheckPullingProgressLifecycleHandler(SessionLifecycleHandler):
    """Handler for checking if PULLING/PREPARING sessions are ready to transition to PREPARED.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PREPARING/PULLING status
    - Coordinator filters sessions where ALL kernels are PREPARED or RUNNING
    - Handler returns session IDs as successes (no additional logic needed)
    - Coordinator updates sessions to PREPARED status
    """

    def __init__(
        self,
        event_producer: EventProducer,
    ) -> None:
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-pulling-progress"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in PREPARING or PULLING state."""
        return [SessionStatus.PREPARING, SessionStatus.PULLING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Only include sessions where ALL kernels are PREPARED or RUNNING."""
        return [KernelStatus.PREPARED, KernelStatus.RUNNING]

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """Sessions transition to PREPARED on success."""
        return SessionStatus.PREPARED

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status - sessions stay in current state."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """No stale status for this handler."""
        return None

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARING/PULLING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Return all provided sessions as successes.

        The coordinator has already filtered sessions where ALL kernels
        match target_kernel_statuses (PREPARED or RUNNING).
        No additional business logic needed for this handler.
        """
        result = SessionExecutionResult()

        for session in sessions:
            session_info = session.session_info
            result.successes.append(session_info.identity.id)
            result.scheduled_data.append(
                ScheduledSessionData(
                    session_id=session_info.identity.id,
                    creation_id=session_info.identity.creation_id,
                    access_key=AccessKey(session_info.metadata.access_key),
                    reason="triggered-by-scheduler",
                )
            )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Broadcast events for sessions that transitioned to PREPARED."""
        log.info("{} sessions transitioned to PREPARED state", len(result.scheduled_data))

        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.PREPARED),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_data
        ]
        await self._event_producer.broadcast_events_batch(events)
