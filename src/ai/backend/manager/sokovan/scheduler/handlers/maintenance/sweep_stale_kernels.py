"""Handler for sweeping kernels with stale presence status."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.types import KernelTerminationInfo, SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepStaleKernelsLifecycleHandler(SessionLifecycleHandler):
    """Handler for sweeping kernels with stale presence status.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries RUNNING sessions (provides HandlerSessionData)
    - Handler checks kernel presence in Redis and terminates stale ones
    - Before termination, confirms with agent that kernel is truly gone
    - Returns affected sessions for triggering CHECK_RUNNING_SESSION_TERMINATION
    """

    def __init__(
        self,
        terminator: SessionTerminator,
        valkey_schedule_client: ValkeyScheduleClient,
        repository: SchedulerRepository,
    ) -> None:
        self._terminator = terminator
        self._valkey_schedule_client = valkey_schedule_client
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-stale-kernels"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions with running kernels that may be stale."""
        return [SessionStatus.RUNNING]

    @classmethod
    def target_kernel_statuses(cls) -> Optional[list[KernelStatus]]:
        """Running kernels that may be stale."""
        return [KernelStatus.RUNNING]

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for sweep stale kernels handler (BEP-1030).

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
        """Sweep kernels with stale presence status.

        The coordinator provides SessionWithKernels with full SessionInfo/KernelInfo.
        This handler:
        1. Uses provided session/kernel data directly
        2. Checks kernel presence in Redis via Terminator
        3. Returns kernel terminations for Coordinator to process
        4. Returns affected sessions for post-processing
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Delegate to Terminator's handler-specific method
        # Phase/step recording is handled inside the terminator per entity
        sweep_result = await self._terminator.sweep_stale_kernels_for_handler(list(sessions))

        # Add kernel terminations for Coordinator to process
        for kernel_id in sweep_result.dead_kernel_ids:
            result.kernel_terminations.append(
                KernelTerminationInfo(
                    kernel_id=kernel_id,
                    reason="STALE_KERNEL",
                )
            )

        # Build scheduled data for affected sessions
        for session in sweep_result.affected_sessions:
            result.scheduled_data.append(
                ScheduledSessionData(
                    session_id=session.session_info.identity.id,
                    creation_id=session.session_info.identity.creation_id,
                    access_key=AccessKey(session.session_info.metadata.access_key),
                    reason="STALE_KERNEL",
                )
            )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Trigger CHECK_RUNNING_SESSION_TERMINATION and invalidate cache."""
        log.info("Swept kernels affecting {} sessions", len(result.scheduled_data))

        if result.scheduled_data:
            # Trigger CHECK_RUNNING_SESSION_TERMINATION to check if sessions need termination
            await self._valkey_schedule_client.mark_schedule_needed(
                ScheduleType.CHECK_RUNNING_SESSION_TERMINATION
            )

            # Invalidate cache for affected access keys
            affected_keys: set[AccessKey] = {
                event_data.access_key for event_data in result.scheduled_data
            }
            if affected_keys:
                await self._repository.invalidate_kernel_related_cache(list(affected_keys))
                log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))
