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
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

log = BraceStyleAdapter(logging.getLogger(__name__))


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
