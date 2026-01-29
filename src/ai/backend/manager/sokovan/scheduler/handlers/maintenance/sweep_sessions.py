"""Handler for sweeping stale sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions, TransitionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.data import SessionWithKernels
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for sweeping stale sessions (maintenance operation).

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PENDING status (provides HandlerSessionData)
    - Handler fetches detailed timeout data and determines which sessions have timed out
    - Stale sessions are moved to TERMINATING status
    """

    def __init__(
        self,
        repository: SchedulerRepository,
    ) -> None:
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-sessions"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions that may need sweeping - PENDING with timeout."""
        return [SessionStatus.PENDING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """No kernel filtering for sweep check."""
        return None

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for sweep sessions handler (BEP-1030).

        - success: None (sweep operation doesn't have success transition)
        - need_retry: None
        - expired: Session/kernel → TERMINATING (pending timeout exceeded)
        - give_up: None
        """
        return StatusTransitions(
            success=None,
            need_retry=None,
            expired=TransitionStatus(
                session=SessionStatus.TERMINATING,
                kernel=KernelStatus.TERMINATING,
            ),
            give_up=None,
        )

    @property
    def lock_id(self) -> LockID | None:
        """No lock needed for sweeping stale sessions."""
        return None

    async def execute(
        self,
        _scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Sweep stale sessions including those with pending timeout.

        The coordinator provides SessionWithKernels with full SessionInfo/KernelInfo.
        This handler:
        1. Fetches detailed timeout data from repository
        2. Adds timed out sessions to stales for Coordinator to handle status transition
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from SessionWithKernels
        session_ids = [s.session_info.identity.id for s in sessions]

        # Fetch detailed session data with timeout info
        timed_out_sessions = await self._repository.get_pending_timeout_sessions_by_ids(session_ids)

        if not timed_out_sessions:
            return result

        log.info(
            "Found {} sessions with pending timeout that need termination",
            len(timed_out_sessions),
        )

        # Build session map for getting current status
        session_map = {s.session_info.identity.id: s for s in sessions}

        # Add timed out sessions to failures - Coordinator will apply policy-based transition
        for timed_out in timed_out_sessions:
            session_data = session_map.get(timed_out.session_id)
            if session_data:
                result.failures.append(
                    SessionTransitionInfo(
                        session_id=timed_out.session_id,
                        from_status=session_data.session_info.lifecycle.status,
                        reason="PENDING_TIMEOUT_EXCEEDED",
                        creation_id=timed_out.creation_id,
                        access_key=timed_out.access_key,
                    )
                )

        return result
