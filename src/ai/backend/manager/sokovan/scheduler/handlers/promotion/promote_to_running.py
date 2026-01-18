"""Handler for promoting sessions to RUNNING status."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    KernelMatchType,
    SessionInfo,
    SessionStatus,
    StatusTransitions,
    TransitionStatus,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.pagination import NoPagination
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.handlers.promotion.base import SessionPromotionHandler
from ai.backend.manager.sokovan.scheduler.hooks.registry import HookRegistry
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
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
    - Handler executes on_transition_to_running hooks
    - Handler calculates occupied_slots and updates sessions
    - Coordinator applies status transition to RUNNING

    Note: This handler requires additional data (for hooks) beyond what
    HandlerSessionData provides, so it fetches full session data from repository.
    """

    def __init__(
        self,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
        hook_registry: HookRegistry,
    ) -> None:
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository
        self._hook_registry = hook_registry

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
    def success_status(cls) -> SessionStatus:
        """Sessions transition to RUNNING on success."""
        return SessionStatus.RUNNING

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for promote to running handler (BEP-1030).

        - success: Session/kernel → RUNNING
        - need_retry: None
        - expired: None
        - give_up: None
        """
        return StatusTransitions(
            success=TransitionStatus(
                session=SessionStatus.RUNNING,
                kernel=KernelStatus.RUNNING,
            ),
            need_retry=None,
            expired=None,
            give_up=None,
        )

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionInfo],
    ) -> SessionExecutionResult:
        """Execute on_transition_to_running hooks and prepare for RUNNING transition.

        This handler needs to:
        1. Fetch full session+kernel data (coordinator passes session-only data)
        2. Execute hooks (on_transition_to_running)
        3. Calculate occupied_slots from all kernels
        4. Update sessions with occupying_slots (via repository)
        5. Return successes for status transition

        Note: The coordinator passes session-only data. This handler fetches
        full session+kernel data for hooks and occupied_slots calculation.
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

        # Execute hooks concurrently
        sessions_running_data: list[SessionRunningData] = []

        hook_coroutines = [
            self._hook_registry.get_hook(
                session.session_info.metadata.session_type
            ).on_transition_to_running(session)
            for session in full_sessions
        ]

        # Execute hooks concurrently (hooks have their own recording per session type)
        hook_results = await asyncio.gather(*hook_coroutines, return_exceptions=True)

        for session, hook_result in zip(full_sessions, hook_results, strict=True):
            session_info = session.session_info
            if isinstance(hook_result, BaseException):
                log.error(
                    "Hook failed with exception for session {}: {}",
                    session_info.identity.id,
                    hook_result,
                )
                # Don't include in successes - session stays in CREATING
                continue

            # Calculate total occupying_slots from all kernels
            total_occupying_slots = ResourceSlot()
            for kernel_info in session.kernel_infos:
                if kernel_info.resource.occupied_slots:
                    total_occupying_slots += kernel_info.resource.occupied_slots

            sessions_running_data.append(
                SessionRunningData(
                    session_id=session_info.identity.id,
                    occupying_slots=total_occupying_slots,
                )
            )

        # Update sessions with occupying_slots via repository
        if sessions_running_data:
            await self._repository.update_sessions_to_running(sessions_running_data)

            # Build success result - find matching SessionWithKernels for ScheduledSessionData
            session_map = {s.session_info.identity.id: s for s in full_sessions}
            for running_data in sessions_running_data:
                original_session = session_map.get(running_data.session_id)
                if original_session:
                    original_info = original_session.session_info
                    result.successes.append(
                        SessionTransitionInfo(
                            session_id=running_data.session_id,
                            from_status=original_info.lifecycle.status,
                        )
                    )
                    result.scheduled_data.append(
                        ScheduledSessionData(
                            session_id=original_info.identity.id,
                            creation_id=original_info.identity.creation_id,
                            access_key=AccessKey(original_info.metadata.access_key),
                            reason="triggered-by-scheduler",
                        )
                    )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Broadcast events for sessions that transitioned to RUNNING."""
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.START)
        log.info("{} sessions transitioned to RUNNING state", len(result.scheduled_data))

        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.RUNNING),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_data
        ]
        await self._event_producer.broadcast_events_batch(events)
