"""Handler for promoting sessions to PREPARED status."""

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


class PromoteToPreparedPromotionHandler(SessionPromotionHandler):
    """Handler for promoting PREPARING/PULLING sessions to PREPARED.

    Promotes sessions when ALL kernels are PREPARED or RUNNING.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PREPARING/PULLING status
    - Coordinator filters sessions where ALL kernels are PREPARED or RUNNING
    - Handler returns session IDs as successes (no additional logic needed)
    - Coordinator updates sessions to PREPARED status and broadcasts events
    """

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "promote-to-prepared"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in PREPARING or PULLING state."""
        return [SessionStatus.PREPARING, SessionStatus.PULLING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Only include sessions where ALL kernels are PREPARED or RUNNING."""
        return [KernelStatus.PREPARED, KernelStatus.RUNNING]

    @classmethod
    def kernel_match_type(cls) -> KernelMatchType:
        """All kernels must be PREPARED or RUNNING."""
        return KernelMatchType.ALL

    @classmethod
    def status_transitions(cls) -> PromotionStatusTransitions:
        """Define state transitions for promote to prepared handler (BEP-1030).

        Session → PREPARED (kernel status unchanged, driven by agent events)
        """
        return PromotionStatusTransitions(success=SessionStatus.PREPARED)

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARING/PULLING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionInfo],
    ) -> SessionExecutionResult:
        """Return all provided sessions as successes.

        The coordinator has already filtered sessions where ALL kernels
        match target_kernel_statuses (PREPARED or RUNNING).
        No additional business logic needed for this handler.
        """
        result = SessionExecutionResult()

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

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log transition completion. Events are broadcast by Coordinator."""
        log.info("{} sessions transitioned to PREPARED state", len(result.successes))
