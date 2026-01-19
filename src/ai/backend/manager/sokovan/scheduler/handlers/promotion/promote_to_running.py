"""Handler for promoting sessions to RUNNING status."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    KernelMatchType,
    PromotionStatusTransitions,
    SessionInfo,
    SessionStatus,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.handlers.promotion.base import SessionPromotionHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class PromoteToRunningPromotionHandler(SessionPromotionHandler):
    """Handler for promoting CREATING sessions to RUNNING.

    Promotes sessions when ALL kernels are RUNNING.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with CREATING status and ALL kernels RUNNING
    - Handler returns session transition info for Coordinator to process
    - Coordinator executes hooks, calculates occupied_slots, applies status transition,
      and broadcasts events

    Note: Hook execution, occupied_slots calculation, and event broadcasting are handled
    by Coordinator after handler returns, ensuring hook failures don't affect sessions.
    """

    def __init__(self) -> None:
        pass

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "promote-to-running"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in CREATING state."""
        return [SessionStatus.CREATING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Only include sessions where ALL kernels are RUNNING."""
        return [KernelStatus.RUNNING]

    @classmethod
    def kernel_match_type(cls) -> KernelMatchType:
        """All kernels must be RUNNING."""
        return KernelMatchType.ALL

    @classmethod
    def status_transitions(cls) -> PromotionStatusTransitions:
        """Define state transitions for promote to running handler (BEP-1030).

        Session → RUNNING (kernel status unchanged, driven by agent events)
        """
        return PromotionStatusTransitions(success=SessionStatus.RUNNING)

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionInfo],
    ) -> SessionExecutionResult:
        """Prepare sessions for RUNNING transition.

        Simply marks sessions for promotion. Coordinator handles:
        - Hook execution
        - occupied_slots calculation from kernel data
        - Status transition and event broadcasting
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Simply mark sessions for promotion - Coordinator handles the rest
        for session_info in sessions:
            result.successes.append(
                SessionTransitionInfo(
                    session_id=session_info.identity.id,
                    from_status=session_info.lifecycle.status,
                    reason="triggered-by-scheduler",
                    creation_id=session_info.identity.creation_id,
                    access_key=AccessKey(session_info.metadata.access_key),
                )
            )

        return result
