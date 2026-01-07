"""Handler for sweeping stale sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import (
    SchedulerHandler,
    SessionLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    ScheduledSessionData,
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepSessionsHandler(SchedulerHandler):
    """Handler for sweeping stale sessions (maintenance operation)."""

    def __init__(
        self,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ) -> None:
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
        await self._repository.invalidate_kernel_related_cache(list(affected_keys))
        log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))


class SweepSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for sweeping stale sessions (maintenance operation).

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PENDING status (provides HandlerSessionData)
    - Handler fetches detailed timeout data and determines which sessions have timed out
    - Stale sessions are moved to TERMINATING status
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
        return "sweep-sessions"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions that may need sweeping - PENDING with timeout."""
        return [SessionStatus.PENDING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Any kernel status for sweep check."""
        return []

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """No success status - sweep operation moves to TERMINATING."""
        return None

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status for sweep handler."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """Stale sessions transition to TERMINATING."""
        return SessionStatus.TERMINATING

    @property
    def lock_id(self) -> Optional[LockID]:
        """No lock needed for sweeping stale sessions."""
        return None

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[HandlerSessionData],
    ) -> SessionExecutionResult:
        """Sweep stale sessions including those with pending timeout.

        The coordinator provides basic session info (HandlerSessionData).
        This handler:
        1. Fetches detailed timeout data from repository
        2. Delegates to Terminator's handler-specific method
        3. Returns stale session IDs for status transition
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from HandlerSessionData
        session_ids = [s.session_id for s in sessions]

        # Fetch detailed session data with timeout info
        timed_out_sessions = await self._repository.get_pending_timeout_sessions_by_ids(
            session_ids
        )

        if not timed_out_sessions:
            return result

        # Delegate to Terminator's handler-specific method
        swept_ids = await self._terminator.sweep_stale_sessions_for_handler(timed_out_sessions)

        # Build scheduled data for post-processing
        session_map = {s.session_id: s for s in sessions}
        for swept_id in swept_ids:
            result.stales.append(swept_id)
            if swept_id in session_map:
                session_data = session_map[swept_id]
                result.scheduled_data.append(
                    ScheduledSessionData(
                        session_id=swept_id,
                        creation_id=session_data.creation_id,
                        access_key=session_data.access_key,
                        reason="sweeped-as-stale",
                    )
                )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log the number of swept sessions and invalidate cache."""
        log.info("Swept {} stale sessions", len(result.stales))
        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_data
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))
