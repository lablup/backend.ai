"""Main scheduling data type."""

from dataclasses import dataclass

from ai.backend.manager.data.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.data.sokovan.workload import SessionWorkload

from .agent import AgentMeta
from .resource_group import ResourceGroupMeta


@dataclass
class SchedulingData:
    """Complete scheduling data structure."""

    resource_group: ResourceGroupMeta
    # Pending sessions converted to schedulable workloads (oldest first)
    workloads: list[SessionWorkload]
    agents: list[AgentMeta]
    # None when there is nothing to schedule (no pending sessions)
    system_snapshot: SystemSnapshot | None
    # Per-agent container limit from configuration (None = unlimited)
    max_container_count: int | None
