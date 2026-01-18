"""Handler for detecting abnormal termination of RUNNING sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
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
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.handlers.promotion.base import SessionPromotionHandler
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    SessionExecutionResult,
    SessionTransitionInfo,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class DetectTerminationPromotionHandler(SessionPromotionHandler):
    """Handler for detecting RUNNING sessions where all kernels are TERMINATED.

    Detects abnormal termination and transitions sessions to TERMINATING.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with RUNNING status and ALL kernels TERMINATED
    - Handler marks sessions as TERMINATING (abnormal termination)
    - Coordinator applies status transition to TERMINATING

    This detects abnormal terminations (e.g., kernel died, agent lost) and
    ensures session cleanup proceeds through the normal termination flow.
    """

    def __init__(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        repository: SchedulerRepository,
    ) -> None:
        self._valkey_schedule_client = valkey_schedule_client
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "detect-termination"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in RUNNING state."""
        return [SessionStatus.RUNNING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Only include sessions where ALL kernels are TERMINATED."""
        return [KernelStatus.TERMINATED]

    @classmethod
    def kernel_match_type(cls) -> KernelMatchType:
        """All kernels must be TERMINATED."""
        return KernelMatchType.ALL

    @classmethod
    def status_transitions(cls) -> PromotionStatusTransitions:
        """Define state transitions for detect termination handler (BEP-1030).

        Session → TERMINATING (kernels already TERMINATED by agent events)
        """
        return PromotionStatusTransitions(success=SessionStatus.TERMINATING)

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionInfo],
    ) -> SessionExecutionResult:
        """Mark RUNNING sessions with all kernels TERMINATED as TERMINATING.

        The coordinator has already filtered sessions where ALL kernels
        are TERMINATED. We just need to mark them for termination.
        """
        result = SessionExecutionResult()

        for session_info in sessions:
            result.successes.append(
                SessionTransitionInfo(
                    session_id=session_info.identity.id,
                    from_status=session_info.lifecycle.status,
                )
            )
            result.scheduled_data.append(
                ScheduledSessionData(
                    session_id=session_info.identity.id,
                    creation_id=session_info.identity.creation_id,
                    access_key=AccessKey(session_info.metadata.access_key),
                    reason="ABNORMAL_TERMINATION",
                )
            )

        if result.successes:
            log.info(
                "Marked {} RUNNING sessions as TERMINATING (all kernels terminated unexpectedly)",
                len(result.successes),
            )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Trigger CHECK_TERMINATING_PROGRESS and invalidate cache."""
        log.info(
            "{} RUNNING sessions marked as TERMINATING",
            len(result.scheduled_data),
        )

        # Trigger CHECK_TERMINATING_PROGRESS to finalize session termination
        await self._valkey_schedule_client.mark_schedule_needed(
            ScheduleType.CHECK_TERMINATING_PROGRESS
        )

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_data
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug(
                "Invalidated kernel-related cache for {} access keys",
                len(affected_keys),
            )
