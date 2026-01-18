"""Handler for retrying creating sessions."""

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
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher

log = BraceStyleAdapter(logging.getLogger(__name__))

# Time thresholds for health checks
CREATING_CHECK_THRESHOLD = 600.0  # 10 minutes


class RetryCreatingLifecycleHandler(SessionLifecycleHandler):
    """Handler for retrying CREATING sessions that appear stuck.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with CREATING status
    - Handler checks if sessions are truly stuck and retries them
    - Sessions exceeding max retries are marked as stale (TERMINATING)
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
        return "retry-creating"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in CREATING state."""
        return [SessionStatus.CREATING]

    @classmethod
    def target_kernel_statuses(cls) -> Optional[list[KernelStatus]]:
        """No kernel filtering - we check stuck sessions regardless."""
        return None

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for retry creating handler (BEP-1030).

        - success: None (stays CREATING, retry was successful)
        - need_retry: None (will retry on next check)
        - expired: Session/kernel → PENDING (exceeded time, re-schedule)
        - give_up: Session/kernel → PENDING (exceeded max retries, re-schedule)
        """
        return StatusTransitions(
            success=None,
            need_retry=None,
            expired=TransitionStatus(
                session=SessionStatus.PENDING,
                kernel=KernelStatus.PENDING,
            ),
            give_up=TransitionStatus(
                session=SessionStatus.PENDING,
                kernel=KernelStatus.PENDING,
            ),
        )

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Check and retry stuck CREATING sessions.

        Fetches detailed session data and delegates to Launcher's retry method which handles:
        - Filtering truly stuck sessions
        - Checking with agents if sessions are actively creating
        - Updating retry counts
        - Re-triggering session creation for sessions that should retry
        - Returning exceeded sessions for Coordinator to update to PENDING
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from SessionWithKernels
        session_ids = [s.session_info.identity.id for s in sessions]

        # Fetch detailed session data (SessionDataForStart) from repository
        sessions_with_images = await self._repository.get_sessions_for_start_by_ids(session_ids)
        sessions_for_start = sessions_with_images.sessions
        image_configs = sessions_with_images.image_configs

        if not sessions_for_start:
            return result

        # Delegate to Launcher's handler-specific method
        # Phase/step recording is handled inside the launcher per entity
        retry_result = await self._launcher.retry_creating_for_handler(
            sessions_for_start, image_configs
        )

        # Sessions that were retried are successes
        session_map = {s.session_info.identity.id: s for s in sessions}
        for session_id in retry_result.retried_ids:
            original_session = session_map.get(session_id)
            from_status = (
                original_session.session_info.lifecycle.status
                if original_session
                else SessionStatus.CREATING  # fallback to expected status
            )
            result.successes.append(
                SessionTransitionInfo(
                    session_id=session_id,
                    from_status=from_status,
                )
            )

        # Sessions that exceeded max retries are failures (Coordinator applies policy-based transition)
        for session_id in retry_result.exceeded_ids:
            original_session = session_map.get(session_id)
            from_status = (
                original_session.session_info.lifecycle.status
                if original_session
                else SessionStatus.CREATING  # fallback to expected status
            )
            result.failures.append(
                SessionTransitionInfo(
                    session_id=session_id,
                    from_status=from_status,
                    reason="EXCEEDED_MAX_RETRIES",
                )
            )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log retry results."""
        log.info("Completed retry check for CREATING sessions")
