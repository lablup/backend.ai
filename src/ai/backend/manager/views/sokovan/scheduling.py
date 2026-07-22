"""Read bundles the scheduler repository hands to the scheduling layer."""

from dataclasses import dataclass

from .agent import AgentLimit, ResourceGroupResource
from .resource_group import ResourceGroupMeta
from .session_creation import SessionSpecContext
from .snapshot import SystemSnapshot
from .workload import SessionWorkload


@dataclass
class SchedulingData:
    """Complete read state of one scheduling run.

    Assembled by the repository (DB, Valkey retry hints, config limits);
    ``None`` is returned instead when the group has nothing to schedule,
    so the snapshot is always present and fully populated.
    """

    resource_group: ResourceGroupMeta
    # Pending sessions converted to schedulable workloads (oldest first)
    workloads: list[SessionWorkload]
    system_snapshot: SystemSnapshot


@dataclass
class ComputeScheduleData:
    """Read bundle for the compute-schedule fitting check."""

    spec_context: SessionSpecContext
    resources: ResourceGroupResource
    limit: AgentLimit
