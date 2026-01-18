"""Handler for promoting sessions to TERMINATED status."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
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
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))


class PromoteToTerminatedPromotionHandler(SessionPromotionHandler):
    """Handler for promoting TERMINATING sessions to TERMINATED.

    Promotes sessions when ALL kernels are TERMINATED.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with TERMINATING status and ALL kernels TERMINATED
    - Coordinator executes on_transition_to_terminated hooks (best-effort)
    - Coordinator applies status transition to TERMINATED

    Note: Cleanup hooks are executed by the Coordinator (best-effort behavior).
    Hook failures are logged but don't prevent session termination.
    """

    def __init__(
        self,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
    ) -> None:
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "promote-to-terminated"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in TERMINATING state."""
        return [SessionStatus.TERMINATING]

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
        """Define state transitions for promote to terminated handler (BEP-1030).

        Session → TERMINATED (kernel status unchanged, driven by agent events)
        """
        return PromotionStatusTransitions(success=SessionStatus.TERMINATED)

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionInfo],
    ) -> SessionExecutionResult:
        """Return sessions ready for TERMINATED transition.

        The Coordinator handles:
        - Fetching full session+kernel data for hooks
        - Executing on_transition_to_terminated hooks (best-effort)
        - All sessions proceed to TERMINATED regardless of hook failures

        This handler simply marks all eligible sessions for transition.
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
                    reason=session_info.lifecycle.status_info or "unknown",
                )
            )

        if result.successes:
            log.info(
                "Marked {} TERMINATING sessions for TERMINATED transition",
                len(result.successes),
            )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Invalidate cache and broadcast events for terminated sessions."""
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.SCHEDULE)
        log.info("{} sessions transitioned to TERMINATED state", len(result.scheduled_data))

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_data
        }
        await self._repository.invalidate_kernel_related_cache(list(affected_keys))
        log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))

        # Broadcast batch event for sessions that transitioned to TERMINATED
        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.TERMINATED),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_data
        ]
        await self._event_producer.broadcast_events_batch(events)
