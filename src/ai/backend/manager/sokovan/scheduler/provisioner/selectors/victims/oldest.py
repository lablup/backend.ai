"""Victim order: preempt the longest-running sessions first."""

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


class OldestVictimOrder(AbstractVictimOrder):
    """Victims are taken oldest first; agent choice stays neutral (the
    placement strategy decides)."""

    @override
    def name(self) -> str:
        return "oldest"

    @override
    def victim_key(
        self,
        candidate: PreemptionCandidate,
        agent_id: AgentId,
        shortfall: Mapping[ResourceSlotName, Decimal],
    ) -> tuple[float, ...]:
        if candidate.started_at is None:
            return (0.0, 0.0)
        return (1.0, candidate.started_at.timestamp())

    @override
    def agent_key(
        self,
        collected: Sequence[PreemptionCandidate],
        agent_id: AgentId,
    ) -> tuple[float, ...]:
        return (0.0,)
