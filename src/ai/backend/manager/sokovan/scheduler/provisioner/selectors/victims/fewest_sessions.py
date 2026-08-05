"""Victim order: preempt as few sessions as possible."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import override

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.victims.order import (
    AbstractVictimOrder,
)
from ai.backend.manager.views.sokovan.snapshot import PreemptionCandidate


class FewestSessionsVictimOrder(AbstractVictimOrder):
    """Victims contributing most toward the shortfall are taken first, so
    fewer sessions cover it; agents needing fewer victims are preferred."""

    @override
    def name(self) -> str:
        return "fewest-sessions"

    @override
    def victim_key(
        self,
        candidate: PreemptionCandidate,
        agent_id: AgentId,
        shortfall: Mapping[ResourceSlotName, Decimal],
    ) -> tuple[float, ...]:
        allocated = candidate.allocated_slots_by_agent[agent_id]
        contribution = sum(
            min(allocated.get(slot_name, Decimal(0)), needed)
            for slot_name, needed in shortfall.items()
        )
        started = (
            (0.0, 0.0) if candidate.started_at is None else (1.0, candidate.started_at.timestamp())
        )
        return (-float(contribution), *started)

    @override
    def agent_key(
        self,
        collected: Sequence[PreemptionCandidate],
        agent_id: AgentId,
    ) -> tuple[float, ...]:
        return (float(len(collected)),)
