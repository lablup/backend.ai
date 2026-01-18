"""Handler for sweeping kernels with lost agents."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import SessionExecutionResult
from ai.backend.manager.sokovan.scheduler.types import KernelTerminationInfo, SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepLostAgentKernelsLifecycleHandler(SessionLifecycleHandler):
    """Handler for sweeping kernels with lost or missing agents.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with TERMINATING status (provides SessionWithKernels)
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
    def target_kernel_statuses(cls) -> Optional[list[KernelStatus]]:
        """Kernels in TERMINATING status that need sweep."""
        return [KernelStatus.TERMINATING]

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for sweep lost agent kernels handler (BEP-1030).

        All transitions are None because this handler only updates kernel status,
        not session status. Kernel status is updated directly in the terminator.
        """
        return StatusTransitions(
            success=None,
            need_retry=None,
            expired=None,
            give_up=None,
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
        """Sweep kernels with lost or missing agents.

        The coordinator provides SessionWithKernels data.
        This handler:
        1. Fetches kernels with lost/missing agents from repository
        2. Delegates to Terminator's handler-specific method
        3. Returns kernel terminations for Coordinator to process
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from SessionWithKernels
        session_ids = [s.session_info.identity.id for s in sessions]

        # Fetch kernels with lost or missing agents
        lost_kernels = await self._repository.get_terminating_kernels_with_lost_agents_by_ids(
            session_ids
        )

        if not lost_kernels:
            return result

        # Delegate to Terminator's handler-specific method
        # Note: No recorder instrumentation - this is DB-update only operation
        kernel_results = await self._terminator.sweep_lost_agent_kernels_for_handler(lost_kernels)

        # Add kernel terminations for Coordinator to process
        for kernel_result in kernel_results:
            result.kernel_terminations.append(
                KernelTerminationInfo(
                    kernel_id=kernel_result.kernel_id,
                    reason="swept-lost-agent",
                )
            )

        log.info("Swept {} kernels with lost/missing agents", len(kernel_results))

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log completion - cache invalidation handled by Terminator."""
        log.info("Completed sweep of lost agent kernels")
