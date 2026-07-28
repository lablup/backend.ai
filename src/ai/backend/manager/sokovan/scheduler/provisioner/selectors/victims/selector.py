"""Common victim-selection algorithm over the pooled victim orders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, PreemptionOrder
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.victims.order import (
    AbstractVictimOrder,
)
from ai.backend.manager.views.sokovan.snapshot import AgentVictimCandidates, PreemptionCandidate


class VictimSelector:
    """Owns the common preemption-ordering arithmetic; the pooled
    :class:`AbstractVictimOrder` strategies only supply keys (unknown
    orders fall back through the pool default)."""

    _order_pool: Mapping[PreemptionOrder, AbstractVictimOrder]

    def __init__(self, order_pool: Mapping[PreemptionOrder, AbstractVictimOrder]) -> None:
        self._order_pool = order_pool

    def collect_victims(
        self,
        order: PreemptionOrder,
        agent_victims: AgentVictimCandidates,
        shortfall: Mapping[ResourceSlotName, Decimal],
    ) -> list[PreemptionCandidate]:
        """The victims covering the agent's shortfall.

        Victims are taken by job_priority ascending, then the order's key;
        candidates contributing nothing toward the remaining deficit are
        skipped.
        """
        strategy = self._order_pool[order]
        agent_id = agent_victims.agent_id
        deficit = {slot_name: needed for slot_name, needed in shortfall.items() if needed > 0}
        ranked = sorted(
            agent_victims.candidates,
            key=lambda candidate: (
                candidate.job_priority,
                *strategy.victim_key(candidate, agent_id, shortfall),
            ),
        )
        collected: list[PreemptionCandidate] = []
        for candidate in ranked:
            if not deficit:
                break
            allocated = candidate.allocated_slots_by_agent[agent_id]
            if not any(allocated.get(slot_name, Decimal(0)) > 0 for slot_name in deficit):
                continue
            collected.append(candidate)
            deficit = {
                slot_name: remaining
                for slot_name, needed in deficit.items()
                if (remaining := needed - allocated.get(slot_name, Decimal(0))) > 0
            }
        return collected

    def narrow_agents(
        self,
        order: PreemptionOrder,
        trackers: Sequence[AgentStateTracker],
        victims_by_agent: Mapping[AgentId, AgentVictimCandidates],
        shortfalls: Mapping[AgentId, Mapping[ResourceSlotName, Decimal]],
    ) -> list[AgentStateTracker]:
        """Keep the trackers ranked best by the order's agent key."""
        strategy = self._order_pool[order]

        def rank(tracker: AgentStateTracker) -> tuple[float, ...]:
            agent_id = tracker.original_agent.agent_id
            agent_victims = victims_by_agent.get(agent_id)
            if agent_victims is None:
                return strategy.agent_key([], agent_id)
            collected = self.collect_victims(order, agent_victims, shortfalls.get(agent_id, {}))
            return strategy.agent_key(collected, agent_id)

        best = min(rank(tracker) for tracker in trackers)
        return [tracker for tracker in trackers if rank(tracker) == best]
