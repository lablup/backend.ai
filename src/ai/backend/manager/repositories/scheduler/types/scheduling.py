"""Repository-internal scheduling fetch types."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.types import AgentId
from ai.backend.manager.views.sokovan.agent import AgentMeta
from ai.backend.manager.views.sokovan.resource_group import ResourceGroupMeta
from ai.backend.manager.views.sokovan.snapshot import (
    PreemptionCandidateSnapshot,
    ResourceGroupSchedulingPolicy,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
)
from ai.backend.manager.views.sokovan.workload import SessionWorkload


@dataclass(frozen=True)
class SchedulingFetch:
    """DB-side sources of one scheduling run (no Valkey/config involved).

    The repository composes this with the per-agent retry hints and the
    configured agent limit into the final :class:`SchedulingData`.
    """

    resource_group: ResourceGroupMeta
    policy: ResourceGroupSchedulingPolicy
    workloads: list[SessionWorkload]
    agents: list[AgentMeta]
    occupancy: ResourceOccupancySnapshot
    resource_policy: ResourcePolicySnapshot
    session_dependencies: SessionDependencySnapshot
    # DB-sourced time the fetch ran (single time authority across managers)
    observed_at: datetime
    # Preemption victim candidates per owner (empty when preemption disabled)
    preemption_candidates: PreemptionCandidateSnapshot
    # Live session-group members per agent (empty when no pending session
    # carries a placement-engaged group)
    session_group_members: Mapping[AgentId, Mapping[SessionGroupID, int]]
