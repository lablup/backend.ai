"""Handler for terminating sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions, TransitionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import SessionExecutionResult
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class TerminateSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for terminating sessions marked for termination.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with TERMINATING status (provides HandlerSessionData)
    - Handler queries additional kernel data and sends termination RPC to agents
    - No status transition by Coordinator (handled by agent events)

    Note: This handler doesn't transition status because:
    - Kernel termination is async (agent sends events when done)
    - Session status updates are triggered by kernel status changes
    """

    def __init__(
        self,
        terminator: SessionTerminator,
        repository: SchedulerRepository,
    ) -> None:
        self._terminator = terminator
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "terminate-sessions"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in TERMINATING state."""
        return [SessionStatus.TERMINATING]

    @classmethod
    def target_kernel_statuses(cls) -> Optional[list[KernelStatus]]:
        """No kernel filtering - termination applies to any kernel state."""
        return None

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """No automatic status transition - handled by agent events."""
        return None

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status - RPC failures are handled by sweep."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """No stale status for this handler."""
        return None

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for terminate sessions handler (BEP-1030).

        - success: None (handled by agent events - kernel termination is async)
        - need_retry: None (stays TERMINATING, will retry)
        - expired: Session/kernel → TERMINATED (timeout, nothing more we can do)
        - give_up: Session/kernel → TERMINATED (max retries, nothing more we can do)
        """
        return StatusTransitions(
            success=None,
            need_retry=None,
            expired=TransitionStatus(
                session=SessionStatus.TERMINATED,
                kernel=KernelStatus.TERMINATED,
            ),
            give_up=TransitionStatus(
                session=SessionStatus.TERMINATED,
                kernel=KernelStatus.TERMINATED,
            ),
        )

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Send termination RPC calls for TERMINATING sessions.

        The coordinator provides SessionWithKernels data.
        This handler:
        1. Fetches detailed session data (TerminatingSessionData) from repository
        2. Delegates to Terminator's handler-specific method
        3. Returns empty result (no status transitions needed)
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from SessionWithKernels
        session_ids = [s.session_info.identity.id for s in sessions]

        # Fetch detailed session data (TerminatingSessionData) from repository
        terminating_sessions = await self._repository.get_terminating_sessions_by_ids(session_ids)

        if not terminating_sessions:
            return result

        # Delegate to Terminator's handler-specific method
        await self._terminator.terminate_sessions_for_handler(terminating_sessions)

        # Don't mark as success - status updates happen via agent events
        # The Coordinator won't update any status because success_status is None

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """No post-processing needed - termination events come from agents."""
        pass
