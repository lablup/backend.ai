"""Handler for sweeping kernels with lost agents."""

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
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepLostAgentKernelsHandler(SchedulerHandler):
    """Handler for sweeping kernels with lost or missing agents."""

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
        return "sweep-lost-agent-kernels"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Sweep kernels with lost or missing agents."""
        return await self._scheduler.sweep_lost_agent_kernels()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of swept kernels and invalidate cache."""
        log.info("Swept {} sessions with lost agent kernels", len(result.scheduled_sessions))
        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        await self._repository.invalidate_kernel_related_cache(list(affected_keys))
        log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))


class SweepLostAgentKernelsLifecycleHandler(SessionLifecycleHandler):
    """Handler for sweeping kernels with lost or missing agents.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with TERMINATING status (provides HandlerSessionData)
    - Handler fetches kernels with lost/missing agents and terminates them
    - Kernel status is updated to TERMINATED (session status updated by other handlers)
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
        return "sweep-lost-agent-kernels"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in TERMINATING state that may have kernels with lost agents."""
        return [SessionStatus.TERMINATING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Kernels in TERMINATING status that need sweep."""
        return [KernelStatus.TERMINATING]

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """No success status - kernel status updated, not session status."""
        return None

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status for sweep handler."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """No stale status - this handler updates kernel status only."""
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
        """Sweep kernels with lost or missing agents.

        The coordinator provides basic session info (HandlerSessionData).
        This handler:
        1. Fetches kernels with lost/missing agents from repository
        2. Delegates to Terminator's handler-specific method
        3. Returns empty result (kernel status updated, not session status)
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from HandlerSessionData
        session_ids = [s.session_id for s in sessions]

        # Fetch kernels with lost or missing agents
        lost_kernels = await self._repository.get_terminating_kernels_with_lost_agents_by_ids(
            session_ids
        )

        if not lost_kernels:
            return result

        # Delegate to Terminator's handler-specific method
        swept_count = await self._terminator.sweep_lost_agent_kernels_for_handler(lost_kernels)

        log.info("Swept {} kernels with lost/missing agents", swept_count)

        # No session status change - kernel status updated only
        # CHECK_TERMINATING_PROGRESS will update session status when all kernels are terminated

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log completion - cache invalidation handled by Terminator."""
        log.info("Completed sweep of lost agent kernels")
