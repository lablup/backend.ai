"""Handler for deprioritizing sessions that exceeded max scheduling retries."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.defs.session import SESSION_PRIORITY_MIN
from ai.backend.common.types import AccessKey
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

log = BraceStyleAdapter(logging.getLogger(__name__))

# Amount to lower priority when deprioritizing
DEPRIORITIZE_AMOUNT = 10


class DeprioritizeSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for deprioritizing sessions that exceeded max scheduling retries.

    When sessions in PENDING status exceed max scheduling retries (give_up),
    they transition to DEPRIORITIZING. This handler:
    1. Lowers the session priority
    2. Transitions back to PENDING for re-scheduling with lower priority

    This allows sessions to eventually be scheduled when resources become available,
    rather than being terminated outright.
    """

    def __init__(
        self,
        repository: SchedulerRepository,
    ) -> None:
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "deprioritize-sessions"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in DEPRIORITIZING state."""
        return [SessionStatus.DEPRIORITIZING]

    @classmethod
    def target_kernel_statuses(cls) -> Optional[list[KernelStatus]]:
        """No kernel filtering for deprioritize."""
        return None

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for deprioritize handler (BEP-1030).

        - success: Session → PENDING (re-schedule with lower priority)
        - need_retry: None
        - expired: None
        - give_up: None
        """
        return StatusTransitions(
            success=TransitionStatus(
                session=SessionStatus.PENDING,
                kernel=None,  # Kernel status unchanged
            ),
            need_retry=None,
            expired=None,
            give_up=None,
        )

    @property
    def lock_id(self) -> Optional[LockID]:
        """No lock needed for deprioritizing sessions."""
        return None

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Lower priority and prepare for re-scheduling.

        The coordinator provides SessionWithKernels.
        This handler:
        1. Lowers priority for each session via repository
        2. Reports all as success for Coordinator to transition to PENDING
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Lower priority for all sessions (with floor at SESSION_PRIORITY_MIN)
        session_ids = [s.session_info.identity.id for s in sessions]
        await self._repository.lower_session_priority(
            session_ids, DEPRIORITIZE_AMOUNT, SESSION_PRIORITY_MIN
        )

        log.info(
            "Lowered priority by {} for {} sessions in scaling group {}",
            DEPRIORITIZE_AMOUNT,
            len(sessions),
            scaling_group,
        )

        # Mark all sessions as success for status transition to PENDING
        for session in sessions:
            session_info = session.session_info
            result.successes.append(
                SessionTransitionInfo(
                    session_id=session_info.identity.id,
                    from_status=session_info.lifecycle.status,
                    reason="deprioritized-for-rescheduling",
                    creation_id=session_info.identity.creation_id,
                    access_key=AccessKey(session_info.metadata.access_key),
                )
            )

        return result
