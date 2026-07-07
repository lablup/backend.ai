"""Handler for checking session preconditions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions, TransitionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.data import SessionWithKernels
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckPreconditionLifecycleHandler(SessionLifecycleHandler):
    """Handler for checking session preconditions and triggering image pulling.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with SCHEDULED status (provides HandlerSessionData)
    - Handler queries additional data (SessionDataForPull + ImageConfigData) via Repository
    - Handler triggers image pulling on agents via Launcher
    - Coordinator updates sessions to PREPARING status and broadcasts events
    """

    def __init__(
        self,
        launcher: SessionLauncher,
        repository: SchedulerRepository,
    ) -> None:
        self._launcher = launcher
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-precondition"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in SCHEDULED or PREPARING state.

        PREPARING is included so the handler re-queries sessions that have
        already started preparation and re-triggers the idempotent image
        pull. This recovers sessions stuck in PREPARING when a pull-related
        event (e.g. ImagePullFinished) was lost in transit, since nothing
        else re-sends check_and_pull once the session leaves SCHEDULED.
        """
        return [SessionStatus.SCHEDULED, SessionStatus.PREPARING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """Include sessions with kernels in SCHEDULED, PREPARING, or PULLING status.

        PREPARING/PULLING cover kernels whose pull already finished on the
        agent but were never updated to PREPARED because the ImagePullFinished
        event was lost; re-triggering makes the agent re-emit the completion
        event.
        """
        return [KernelStatus.SCHEDULED, KernelStatus.PREPARING, KernelStatus.PULLING]

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for check precondition handler (BEP-1030).

        - success: Session/kernel → PREPARING
        - need_retry: None (stays SCHEDULED)
        - expired: Session/kernel → PENDING (re-scheduling after timeout —
          a transient agent / network issue may resolve in a different
          slot, so put the session back in the queue)
        - give_up: Session/kernel → TERMINATING (retry budget exhausted —
          image pull failures that survive every attempt indicate a
          permanent problem such as a missing image or registry
          credentials; rescheduling repeatedly would just re-run the
          same failing pull, so we surface the failure to the user
          instead)
        """
        return StatusTransitions(
            success=TransitionStatus(
                session=SessionStatus.PREPARING,
                kernel=KernelStatus.PREPARING,
            ),
            need_retry=None,
            expired=TransitionStatus(
                session=SessionStatus.PENDING,
                kernel=KernelStatus.PENDING,
            ),
            give_up=TransitionStatus(
                session=SessionStatus.TERMINATING,
                kernel=KernelStatus.TERMINATING,
            ),
        )

    @property
    def lock_id(self) -> LockID | None:
        """Lock for operations targeting SCHEDULED sessions transitioning to PREPARING."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(
        self,
        _scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Trigger image pulling for SCHEDULED sessions.

        The coordinator provides SessionWithKernels data.
        This handler:
        1. Extracts session IDs from SessionWithKernels
        2. Queries Repository for additional data (SessionDataForPull + ImageConfigData)
        3. Triggers image pulling via Launcher
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from SessionWithKernels
        session_ids = [s.session_info.identity.id for s in sessions]

        # Query Repository for additional data needed by Launcher
        sessions_for_pull_data = await self._repository.get_sessions_for_pull_by_ids(session_ids)

        # Trigger image pulling via Launcher with the full data
        # Note: RecorderContext is handled inside Launcher
        await self._launcher.trigger_image_pulling(
            sessions_for_pull_data.sessions,
            sessions_for_pull_data.image_configs,
        )

        # Report re-triggered PREPARING sessions as skipped so the coordinator
        # does not re-apply the PREPARING transition (avoids racing against
        # concurrent promotions and re-broadcasting the same status event).
        for session in sessions:
            session_info = session.session_info
            from_status = session_info.lifecycle.status
            transition_info = SessionTransitionInfo(
                session_id=session_info.identity.id,
                from_status=from_status,
                reason="passed-preconditions",
                creation_id=session_info.identity.creation_id,
                access_key=AccessKey(session_info.metadata.access_key),
            )
            if from_status == SessionStatus.PREPARING:
                result.skipped.append(transition_info)
            else:
                result.successes.append(transition_info)

        return result
