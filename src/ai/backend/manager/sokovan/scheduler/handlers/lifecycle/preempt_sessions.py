"""Handler for preempting low-priority running sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.common.types import PreemptionMode, ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.data import SessionWithKernels
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.provisioner.preemptor import PreemptionCandidateSelector
from ai.backend.manager.sokovan.scheduler.results import SessionExecutionResult

log = BraceStyleAdapter(logging.getLogger(__name__))


class PreemptSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for preempting low-priority running sessions (BEP-1014).

    When high-priority sessions are stuck in PENDING due to resource shortage,
    this handler checks if terminating lower-priority preemptible running sessions
    would free enough resources.

    Preemption condition:
    - running session: is_preemptible == True AND priority <= preemptible_priority
    - pending session must have higher priority than the preempted session

    Candidate selection:
    - Lowest priority first
    - Among same-priority: oldest or newest first (per preemption_order config)
    - Accumulate until freed resources cover the pending session's request

    Preempted sessions transition normally: RUNNING → TERMINATING → TERMINATED
    (via existing TerminateSessionsLifecycleHandler)
    """

    def __init__(self, repository: SchedulerRepository) -> None:
        self._repository = repository
        self._selector = PreemptionCandidateSelector()

    @classmethod
    def name(cls) -> str:
        return "preempt-sessions"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Handle PENDING sessions that may trigger preemption."""
        return [SessionStatus.PENDING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """No kernel status filtering for pending sessions."""
        return None

    @classmethod
    def status_transitions(cls) -> StatusTransitions:
        """No status transitions for PENDING sessions themselves.

        Preempted sessions (running → terminating) are handled by mark_sessions_terminating,
        not through the normal status_transitions mechanism.
        """
        return StatusTransitions(
            success=None,
            need_retry=None,
            expired=None,
            give_up=None,
        )

    @property
    def lock_id(self) -> LockID | None:
        """Lock to prevent concurrent preemption decisions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PENDING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Evaluate preemption for unscheduled high-priority pending sessions.

        For each pending session (sorted by priority, highest first):
        1. Fetch current scheduling data to determine available resources
        2. Fetch preemptible running sessions for the scaling group
        3. Check if preemption is needed and possible
        4. Mark selected candidates as TERMINATING

        Args:
            scaling_group: The scaling group being processed
            sessions: PENDING sessions provided by the coordinator

        Returns:
            Empty SessionExecutionResult (preemption is a side-effect, not a status change)
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Get scheduling data (agents, snapshot) for this scaling group
        scheduling_data = await self._repository.get_scheduling_data(scaling_group)
        if scheduling_data is None:
            return result

        # Check if preemption is enabled for this scaling group
        preemption_config = scheduling_data.scaling_group.scheduler_opts.preemption
        if preemption_config.mode != PreemptionMode.TERMINATE:
            return result

        # Compute total available slots across all agents
        total_capacity = scheduling_data.total_capacity
        total_occupied = ResourceSlot()
        if scheduling_data.snapshot_data is not None:
            for agent_occ in scheduling_data.snapshot_data.resource_occupancy.by_agent.values():
                agent_occupied = ResourceSlot({
                    sq.slot_name: sq.quantity for sq in agent_occ.occupied_slots
                })
                total_occupied = total_occupied + agent_occupied
        available_slots = total_capacity - total_occupied

        # Fetch preemptible running sessions for this scaling group
        running_sessions = await self._repository.get_running_sessions_for_preemption(scaling_group)

        if not running_sessions:
            return result

        # Sort pending sessions by priority (highest first)
        sorted_sessions = sorted(
            sessions,
            key=lambda s: s.session_info.metadata.priority,
            reverse=True,
        )

        preempted_session_ids = set()

        for pending_session in sorted_sessions:
            pending_priority = pending_session.session_info.metadata.priority
            requested_slots = pending_session.session_info.resource.requested_slots

            # Skip sessions where we already committed preemption this cycle
            # (adjusted available reflects sessions already preempted)
            preemption_result = self._selector.select_candidates(
                running_sessions=[
                    s for s in running_sessions if s.session_id not in preempted_session_ids
                ],
                pending_priority=pending_priority,
                requested_slots=requested_slots,
                available_slots=available_slots,
                preemptible_priority=preemption_config.preemptible_priority,
                preemption_order=preemption_config.order,
            )

            if not preemption_result.candidates:
                continue

            candidate_ids = [s.session_id for s in preemption_result.candidates]
            log.info(
                "Preempting {} sessions for pending session {} (priority={}) in scaling group {}",
                len(candidate_ids),
                pending_session.session_info.identity.id,
                pending_priority,
                scaling_group,
            )

            await self._repository.mark_sessions_terminating(
                candidate_ids,
                reason="PREEMPTED",
            )

            # Track preempted sessions and update available slots for subsequent iterations
            for session in preemption_result.candidates:
                preempted_session_ids.add(session.session_id)
            available_slots = available_slots + preemption_result.freed_slots

        return result
