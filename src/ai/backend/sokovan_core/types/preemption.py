"""Preemption victim candidates the agent selection may reclaim."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import cached_property

from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, SessionId


@dataclass(frozen=True)
class PreemptionCandidate:
    """One preemption victim candidate (a whole session — the preemption unit).

    Prefiltered at load time (the filter, including the minimum runtime,
    is defined at the load site); per-pending comparison, reclaim ordering,
    and victim selection stay in the selection layer.
    """

    session_id: SessionId
    job_priority: int
    # Execution start time (written at the RUNNING transition); the
    # oldest/newest reclaim-order basis. None when the session never ran
    started_at: datetime | None
    # Per-agent live allocations freed by preempting this session
    allocated_slots_by_agent: Mapping[AgentId, Mapping[ResourceSlotName, Decimal]]


@dataclass(frozen=True)
class AgentVictimCandidates:
    """Victim candidates holding allocations on one agent."""

    agent_id: AgentId
    # Candidates with a portion on this agent (shared with the owner's list)
    candidates: list[PreemptionCandidate]

    @cached_property
    def total_reclaimable(self) -> Mapping[ResourceSlotName, Decimal]:
        """Upper bound freed on this agent if every candidate is preempted."""
        totals: dict[ResourceSlotName, Decimal] = {}
        for candidate in self.candidates:
            for slot_name, amount in candidate.allocated_slots_by_agent[self.agent_id].items():
                totals[slot_name] = totals.get(slot_name, Decimal(0)) + amount
        return totals


@dataclass(frozen=True)
class ScopeVictimCandidates:
    """One scope key's victim candidates with the per-agent decomposition derived.

    ``candidates`` is the stored form (one entry per session — the
    preemption unit); the per-agent grouping and reclaimable totals are
    computed on construction-time reads, so re-instantiating with a
    filtered subset (e.g. the planner's per-pending eligible set) yields
    consistent sums for free.
    """

    candidates: list[PreemptionCandidate]

    @cached_property
    def by_agent(self) -> Mapping[AgentId, AgentVictimCandidates]:
        grouped: dict[AgentId, list[PreemptionCandidate]] = {}
        for candidate in self.candidates:
            for agent_id in candidate.allocated_slots_by_agent:
                grouped.setdefault(agent_id, []).append(candidate)
        return {
            agent_id: AgentVictimCandidates(agent_id=agent_id, candidates=agent_candidates)
            for agent_id, agent_candidates in grouped.items()
        }
