"""System snapshot data types for scheduling decisions."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import (
    ResourceSlot,
    SessionId,
    SlotName,
)

from .workload import (
    SessionDependencyInfo,
    UserResourcePolicy,
)


@dataclass(frozen=True)
class SlotAllocation:
    """Aggregated live allocations for one slot within an owner scope.

    Each allocation row contributes to exactly one field: ``used`` when its
    usage has been reported (running), else ``requested`` (still a
    reservation). ``occupied`` is therefore the exact sum of per-row
    used-or-requested amounts.
    """

    requested: Decimal
    used: Decimal

    @property
    def occupied(self) -> Decimal:
        return self.requested + self.used


@dataclass(frozen=True)
class ResourceAllocation:
    """Per-scope aggregated slot allocations (value of the by-user/project/domain maps)."""

    slots: Mapping[SlotName, SlotAllocation]


@dataclass
class ResourceOccupancySnapshot:
    """Snapshot of resource-quota occupancy per owner scope.

    Keypair-scoped occupancy was folded into the user scope; agent-level
    state (slot resources, container counts) lives on ``AgentMeta``/
    ``AgentInfo``, not here.
    """

    by_user: MutableMapping[UserID, ResourceAllocation]
    by_project: MutableMapping[ProjectID, ResourceAllocation]
    by_domain: MutableMapping[DomainID, ResourceAllocation]


@dataclass(frozen=True)
class ResourcePolicySnapshot:
    """Snapshot of resource policies and limits (user-scoped)."""

    user_policies: Mapping[UserID, UserResourcePolicy]
    project_limits: Mapping[ProjectID, ResourceSlot]
    domain_limits: Mapping[DomainID, ResourceSlot]


@dataclass(frozen=True)
class UserSessionCounts:
    """Global active session counts for a single user."""

    regular: int
    sftp: int


@dataclass
class SessionDependencySnapshot:
    """Snapshot of session dependencies."""

    by_session: Mapping[SessionId, list[SessionDependencyInfo]]


@dataclass
class ResourceGroupScopeSnapshot:
    """State scoped to the resource group being scheduled.

    Every value here is derived only from agents/kernels/sessions that
    belong to this resource group.
    """

    # Total capacity of this resource group's agents
    total_capacity: ResourceSlot
    # Quota occupancy aggregated from this resource group's kernels
    occupancy: ResourceOccupancySnapshot
    # Dependency status for this resource group's pending sessions
    session_dependencies: SessionDependencySnapshot


@dataclass
class GlobalScopeSnapshot:
    """Cluster-wide state, independent of the resource group being scheduled."""

    # Global per-user active session counts (concurrency limits are global)
    active_session_counts: MutableMapping[UserID, UserSessionCounts]
    # Resource policies and limits (global entities)
    resource_policy: ResourcePolicySnapshot


@dataclass
class SystemSnapshot:
    """Complete snapshot of system state for scheduling decisions.

    Split by data scope: ``resource_group`` holds state of the resource
    group being scheduled, ``global_scope`` holds cluster-wide state.
    """

    resource_group: ResourceGroupScopeSnapshot
    global_scope: GlobalScopeSnapshot
