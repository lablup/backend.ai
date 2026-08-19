"""Victim order interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from decimal import Decimal

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
from ai.backend.manager.views.sokovan.snapshot import PreemptionCandidate


class AbstractVictimOrder(ABC):
    """Keys for the two ordering decisions of the preemption path.

    ``victim_key`` orders one agent's victims for collection (lower first;
    job_priority ascending is fixed by the common algorithm before this
    key applies). ``agent_key`` ranks agents by their collected victim set
    (lower preferred) during the order stage.
    """

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def victim_key(
        self,
        candidate: PreemptionCandidate,
        agent_id: AgentId,
        shortfall: Mapping[ResourceSlotName, Decimal],
    ) -> tuple[float, ...]:
        raise NotImplementedError

    @abstractmethod
    def agent_key(
        self,
        collected: Sequence[PreemptionCandidate],
        agent_id: AgentId,
    ) -> tuple[float, ...]:
        raise NotImplementedError
