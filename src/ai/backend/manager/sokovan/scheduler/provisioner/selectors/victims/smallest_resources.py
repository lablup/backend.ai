"""Victim order: preempt the smallest total amount of resources."""

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


class SmallestResourcesVictimOrder(AbstractVictimOrder):
    """Smaller victims are taken first; agents reclaiming the smallest
    total are preferred."""

    @override
    def name(self) -> str:
        return "smallest-resources"

    @override
    def victim_key(
        self,
        candidate: PreemptionCandidate,
        agent_id: AgentId,
        shortfall: Mapping[ResourceSlotName, Decimal],
    ) -> tuple[float, ...]:
        allocated = candidate.allocated_slots_by_agent[agent_id]
        total = sum(allocated.values(), Decimal(0))
        started = (
            (0.0, 0.0) if candidate.started_at is None else (1.0, candidate.started_at.timestamp())
        )
        return (float(total), *started)

    @override
    def agent_key(
        self,
        collected: Sequence[PreemptionCandidate],
        agent_id: AgentId,
    ) -> tuple[float, ...]:
        total = Decimal(0)
        for candidate in collected:
            total += sum(candidate.allocated_slots_by_agent[agent_id].values(), Decimal(0))
        return (float(total),)
