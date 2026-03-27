"""Handler for scheduling pending sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions, TransitionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.data import SessionWithKernels
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)

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
    - Coordinator broadcasts events after status transition
    """

    def __init__(
        self,
        provisioner: SessionProvisioner,
        repository: SchedulerRepository,
    ) -> None:
        self._provisioner = provisioner
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
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """No kernel filtering for scheduling."""
        return None

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for scheduling handler (BEP-1030).

        - success: Session/kernel → SCHEDULED
        - need_retry: None (stays PENDING, will retry on next schedule)
        - expired: Session/kernel → TERMINATING (some kernels may be in higher states)
        - give_up: Session → DEPRIORITIZING (lower priority and re-schedule)
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
                session=SessionStatus.DEPRIORITIZING,
                kernel=None,  # Kernel status unchanged
            ),
        )

    @property
    def lock_id(self) -> LockID | None:
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

        Returns:
        - successes: Sessions that were scheduled
        - skipped: Sessions that were not attempted (priority-based, resource constraints)
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Build session map for lookup
        session_map = {s.session_info.identity.id: s for s in sessions}

        # Fetch scheduling data required by Provisioner
        scheduling_data = await self._repository.get_scheduling_data(scaling_group)
        if scheduling_data is None:
            log.debug(
                "No scheduling data for scaling group {}. Skipping all sessions.",
                scaling_group,
            )
            # All sessions are skipped when no scheduling data available
            for session in sessions:
                result.skipped.append(
                    SessionTransitionInfo(
                        session_id=session.session_info.identity.id,
                        from_status=session.session_info.lifecycle.status,
                        reason="no-scheduling-data",
                        creation_id=session.session_info.identity.creation_id,
                        access_key=AccessKey(session.session_info.metadata.access_key),
                    )
                )
            return result

        # Delegate to Provisioner with pre-fetched data
        provision_time = await self._repository.get_db_now()
        schedule_result = await self._provisioner.schedule_scaling_group(
            scaling_group, scheduling_data, provision_time
        )

        # Track scheduled session IDs
        scheduled_session_ids = set()

        # Mark scheduled sessions as success for status transition
        for event_data in schedule_result.scheduled_sessions:
            scheduled_session_ids.add(event_data.session_id)
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
                    reason=event_data.reason,
                    creation_id=event_data.creation_id,
                    access_key=event_data.access_key,
                )
            )

        # Mark non-scheduled sessions as skipped (not attempted due to priority/resources)
        for session in sessions:
            session_id = session.session_info.identity.id
            if session_id not in scheduled_session_ids:
                result.skipped.append(
                    SessionTransitionInfo(
                        session_id=session_id,
                        from_status=session.session_info.lifecycle.status,
                        reason="not-scheduled-this-cycle",
                        creation_id=session.session_info.identity.creation_id,
                        access_key=AccessKey(session.session_info.metadata.access_key),
                    )
                )

        return result
