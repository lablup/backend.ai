"""Preemption candidate selection logic for low-priority running sessions."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import PreemptionOrder, ResourceSlot
from ai.backend.manager.sokovan.data import RunningSessionData


@dataclass
class PreemptionResult:
    """Result of preemption candidate selection."""

    candidates: list[RunningSessionData]
    freed_slots: ResourceSlot


class PreemptionCandidateSelector:
    """Selects running sessions to preempt for a high-priority pending session.

    Algorithm:
    1. Check if preemption is needed (available < requested)
    2. Filter: keep only sessions where is_preemptible and priority <= preemptible_priority
       and priority < pending_priority
    3. Sort: lowest priority first; within same priority, by preemption_order (oldest/newest)
    4. Accumulate sessions until (available + freed) >= requested
    5. Return empty result if full deficit cannot be covered
    """

    def select_candidates(
        self,
        running_sessions: list[RunningSessionData],
        pending_priority: int,
        requested_slots: ResourceSlot,
        available_slots: ResourceSlot,
        preemptible_priority: int,
        preemption_order: PreemptionOrder,
    ) -> PreemptionResult:
        """Select the minimum set of running sessions to preempt.

        Args:
            running_sessions: All preemptible running sessions in the scaling group.
            pending_priority: Priority of the pending session that needs resources.
            requested_slots: Resource slots requested by the pending session.
            available_slots: Currently available resource slots.
            preemptible_priority: Sessions with priority <= this value are preemptible.
            preemption_order: Whether to preempt oldest or newest sessions first.

        Returns:
            PreemptionResult with selected candidates and total freed slots.
            Returns empty result if preemption is not needed or not possible.
        """
        # No preemption needed if enough resources are available
        if available_slots >= requested_slots:
            return PreemptionResult(candidates=[], freed_slots=ResourceSlot())

        # Filter: only preempt sessions with priority strictly lower than pending
        # and within the preemptible priority threshold
        candidates = [
            s
            for s in running_sessions
            if s.is_preemptible
            and s.priority <= preemptible_priority
            and s.priority < pending_priority
        ]

        if not candidates:
            return PreemptionResult(candidates=[], freed_slots=ResourceSlot())

        # Sort: lowest priority first, then by creation time per preemption_order
        # For OLDEST: smallest created_at first (ascending)
        # For NEWEST: largest created_at first (descending)
        reverse_time = preemption_order == PreemptionOrder.NEWEST
        candidates.sort(
            key=lambda s: (s.priority, s.created_at),
            reverse=False,
        )
        if reverse_time:
            # Re-sort same-priority groups by created_at descending
            candidates.sort(key=lambda s: (s.priority, -s.created_at.timestamp()))

        # Accumulate until freed resources cover the remaining deficit
        selected: list[RunningSessionData] = []
        freed = ResourceSlot()
        for session in candidates:
            selected.append(session)
            freed = freed + session.occupied_slots
            if (available_slots + freed) >= requested_slots:
                break

        # Only return candidates if we can cover the full deficit
        if not ((available_slots + freed) >= requested_slots):
            return PreemptionResult(candidates=[], freed_slots=ResourceSlot())

        return PreemptionResult(candidates=selected, freed_slots=freed)
