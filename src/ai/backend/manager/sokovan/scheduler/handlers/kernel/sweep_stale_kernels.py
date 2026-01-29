"""Handler for sweeping kernels with stale presence status."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.handlers.kernel.base import KernelLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    KernelExecutionResult,
    KernelStatusTransitions,
    KernelTransitionInfo,
)

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepStaleKernelsKernelHandler(KernelLifecycleHandler):
    """Handler for sweeping kernels with stale presence status.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries RUNNING kernels (provides KernelInfo)
    - Handler checks kernel presence in Redis and terminates stale ones
    - Before termination, confirms with agent that kernel is truly gone
    - Returns affected kernels for Coordinator to apply status transitions

    Note: Post-processing (schedule marking) is handled by the Coordinator.
    """

    def __init__(
        self,
        terminator: SessionTerminator,
    ) -> None:
        self._terminator = terminator

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-stale-kernels"

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Running kernels that may be stale."""
        return [KernelStatus.RUNNING]

    @classmethod
    def status_transitions(cls) -> KernelStatusTransitions:
        """Define state transitions for sweep stale kernels handler.

        - success: No status change (kernel is alive, keep RUNNING)
        - failure: Transition to TERMINATED (kernel is dead/stale)
        """
        return KernelStatusTransitions(
            success=None,  # Keep current status
            failure=KernelStatus.TERMINATED,
        )

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        _scaling_group: str,
        kernels: Sequence[KernelInfo],
    ) -> KernelExecutionResult:
        """Sweep kernels with stale presence status.

        The coordinator provides KernelInfo directly.
        This handler:
        1. Uses provided kernel data directly
        2. Checks kernel presence in Redis via Terminator
        3. Returns kernel results for Coordinator to apply status transitions
        """
        result = KernelExecutionResult()

        if not kernels:
            return result

        # Delegate to Terminator's kernel-specific presence check
        # Returns list of kernel_ids that are dead (stale)
        dead_kernel_ids = await self._terminator.check_stale_kernels(list(kernels))

        # Build result based on whether each kernel is alive or dead
        dead_kernel_id_set = set(dead_kernel_ids)
        for kernel_info in kernels:
            kernel_id = kernel_info.id
            if kernel_id in dead_kernel_id_set:
                # Kernel is dead/stale - mark as failure for TERMINATED transition
                result.failures.append(
                    KernelTransitionInfo(
                        kernel_id=kernel_id,
                        from_status=kernel_info.lifecycle.status,
                        reason="STALE_KERNEL",
                    )
                )
            else:
                # Kernel is alive - mark as success (no status change)
                result.successes.append(
                    KernelTransitionInfo(
                        kernel_id=kernel_id,
                        from_status=kernel_info.lifecycle.status,
                        reason=None,
                    )
                )

        return result
