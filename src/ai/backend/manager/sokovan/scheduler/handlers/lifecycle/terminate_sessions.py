"""Handler for terminating sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import (
    SchedulerHandler,
    SessionLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class TerminateSessionsHandler(SchedulerHandler):
    """Handler for terminating sessions."""

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
        return "terminate-sessions"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Terminate sessions marked for termination."""
        return await self._scheduler.terminate_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """
        No post-processing needed.

        Actual status updates and events are handled by:
        - Agent event callbacks (for successful terminations)
        - sweep_lost_agent_kernels() (for lost agents or failed RPC calls)
        """
        # No action needed - terminate_sessions only sends RPC calls
        pass


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
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """All kernel statuses - termination applies to any kernel state."""
        return []  # Empty means any kernel status

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

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[HandlerSessionData],
    ) -> SessionExecutionResult:
        """Send termination RPC calls for TERMINATING sessions.

        The coordinator provides basic session info (HandlerSessionData).
        This handler:
        1. Fetches detailed session data (TerminatingSessionData) from repository
        2. Delegates to Terminator's handler-specific method
        3. Returns empty result (no status transitions needed)
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from HandlerSessionData
        session_ids = [s.session_id for s in sessions]

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
