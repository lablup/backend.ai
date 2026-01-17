"""Handler for scheduling pending sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions, TransitionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
        SessionProvisioner,
    )

log = BraceStyleAdapter(logging.getLogger(__name__))


class ScheduleSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for scheduling pending sessions.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PENDING status per scaling group
    - Handler delegates to Provisioner for session scheduling
    - Successfully scheduled sessions are moved to SCHEDULED status
    """

    def __init__(
        self,
        provisioner: SessionProvisioner,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
    ) -> None:
        self._provisioner = provisioner
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "schedule-sessions"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in PENDING state."""
        return [SessionStatus.PENDING]

    @classmethod
    def target_kernel_statuses(cls) -> Optional[list[KernelStatus]]:
        """No kernel filtering for scheduling."""
        return None

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """Successfully scheduled sessions move to SCHEDULED."""
        return SessionStatus.SCHEDULED

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status - failed scheduling stays PENDING."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """No stale status for scheduling handler."""
        return None

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for scheduling handler (BEP-1030).

        - success: Session/kernel → SCHEDULED
        - need_retry: None (stays PENDING, will retry on next schedule)
        - expired: Session/kernel → TERMINATING (some kernels may be in higher states)
        - give_up: Session/kernel → TERMINATING (some kernels may be in higher states)
        """
        return StatusTransitions(
            success=TransitionStatus(
                session=SessionStatus.SCHEDULED,
                kernel=KernelStatus.SCHEDULED,
            ),
            need_retry=None,
            expired=TransitionStatus(
                session=SessionStatus.TERMINATING,
                kernel=KernelStatus.TERMINATING,
            ),
            give_up=TransitionStatus(
                session=SessionStatus.TERMINATING,
                kernel=KernelStatus.TERMINATING,
            ),
        )

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PENDING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PENDING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Schedule pending sessions for a scaling group.

        Delegates to Provisioner's scheduling method which handles:
        - Resource allocation and agent selection
        - Session placement decisions
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Fetch scheduling data required by Provisioner
        scheduling_data = await self._repository.get_scheduling_data(scaling_group)
        if scheduling_data is None:
            log.debug(
                "No scheduling data for scaling group {}. Skipping scheduling.",
                scaling_group,
            )
            return result

        # Delegate to Provisioner with pre-fetched data
        schedule_result = await self._provisioner.schedule_scaling_group(
            scaling_group, scheduling_data
        )

        # Mark scheduled sessions as success for status transition
        session_map = {s.session_info.identity.id: s for s in sessions}
        for event_data in schedule_result.scheduled_sessions:
            original_session = session_map.get(event_data.session_id)
            from_status = (
                original_session.session_info.lifecycle.status
                if original_session
                else SessionStatus.PENDING  # fallback to expected status
            )
            result.successes.append(
                SessionTransitionInfo(
                    session_id=event_data.session_id,
                    from_status=from_status,
                )
            )
            result.scheduled_data.append(event_data)

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Request precondition check and invalidate cache."""
        # Request next phase first
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.CHECK_PRECONDITION)
        log.info("Scheduled {} sessions, requesting precondition check", len(result.successes))

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_data
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))

        # Broadcast batch event for scheduled sessions
        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.SCHEDULED),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_data
        ]
        if events:
            await self._event_producer.broadcast_events_batch(events)
