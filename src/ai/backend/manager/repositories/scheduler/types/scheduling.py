"""Repository-internal scheduling fetch types."""

from dataclasses import dataclass

from ai.backend.manager.views.sokovan.agent import AgentMeta
from ai.backend.manager.views.sokovan.resource_group import ResourceGroupMeta
from ai.backend.manager.views.sokovan.snapshot import (
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
