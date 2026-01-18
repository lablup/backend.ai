"""Handler for promoting sessions to RUNNING status."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    KernelMatchType,
    PromotionStatusTransitions,
    SessionInfo,
    SessionStatus,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.pagination import NoPagination
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.handlers.promotion.base import SessionPromotionHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.sokovan.scheduler.types import SessionRunningData
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))


class PromoteToRunningPromotionHandler(SessionPromotionHandler):
    """Handler for promoting CREATING sessions to RUNNING.

    Promotes sessions when ALL kernels are RUNNING.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with CREATING status and ALL kernels RUNNING
    - Handler calculates occupied_slots from all kernels
    - Handler returns sessions_running_data for Coordinator to update
    - Coordinator executes hooks, applies status transition, and broadcasts events

    Note: Hook execution, occupied_slots update, and event broadcasting are handled
    by Coordinator after handler returns, ensuring hook failures don't affect sessions.
    """

    def __init__(
        self,
        scheduling_controller: SchedulingController,
        repository: SchedulerRepository,
    ) -> None:
        self._scheduling_controller = scheduling_controller
        self._repository = repository

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

        This handler:
        1. Fetches full session+kernel data (coordinator passes session-only data)
        2. Calculates occupied_slots from all kernels
        3. Returns sessions_running_data for Coordinator to update after hook execution

        Hook execution and occupied_slots update are handled by Coordinator.
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Fetch full session+kernel data for occupied_slots calculation
        session_ids = [s.identity.id for s in sessions]
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[SessionConditions.by_ids(session_ids)],
        )
        full_sessions = await self._repository.search_sessions_with_kernels_for_handler(querier)

        if not full_sessions:
            return result

        # Calculate occupied_slots for all sessions
        for session in full_sessions:
            session_info = session.session_info

            # Calculate total occupying_slots from all kernels
            total_occupying_slots = ResourceSlot()
            for kernel_info in session.kernel_infos:
                if kernel_info.resource.occupied_slots:
                    total_occupying_slots += kernel_info.resource.occupied_slots

            result.sessions_running_data.append(
                SessionRunningData(
                    session_id=session_info.identity.id,
                    occupying_slots=total_occupying_slots,
                )
            )
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
        """Request next scheduling phase. Events are broadcast by Coordinator."""
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.START)
        log.info("{} sessions transitioned to RUNNING state", len(result.successes))
