"""System snapshot data types for scheduling decisions."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import override

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import (
    AgentSelectionStrategy,
    SessionId,
)

from .agent import AgentLimit, ResourceGroupResource
from .workload import (
    ResourceRequest,
    SessionDependencyInfo,
    SessionResourceRequest,
)


@dataclass(frozen=True)
class SlotAllocation:
    """Aggregated live allocations for one slot within an owner scope.

    Each allocation row contributes to exactly one field: ``used`` when its
    usage has been reported (running), else ``requested`` (still a
    reservation). ``allocated`` is therefore the exact sum of per-row
    used-or-requested amounts.
    """

    requested: Decimal
    used: Decimal

    @property
    def allocated(self) -> Decimal:
        return self.requested + self.used


@dataclass(frozen=True)
class ResourceLimit:
    """Slot quota owned by one scope (project/domain)."""

    # Total slot quota (unspecified known slots are materialized per policy default)
    slots: Mapping[ResourceSlotName, Decimal]


@dataclass(frozen=True)
class UserResourceLimit(ResourceLimit):
    """User-scope limits: slot quota plus session-count caps."""

    # Session-count caps; None means no limit
    max_session_count: int | None
    max_sftp_session_count: int | None


@dataclass(frozen=True)
class ResourceAllocation:
    """Cluster-wide observed slot occupancy for one scope (project/domain)."""

    slots: Mapping[ResourceSlotName, SlotAllocation]

    @classmethod
    def empty(cls) -> ResourceAllocation:
        return ResourceAllocation(slots={})

    def exceeds(self, request: ResourceRequest, limit: ResourceLimit) -> bool:
        """True if allocated + requested exceeds the slot quota on any slot.

        Missing keys count as zero on every side, matching the previous
        ``ResourceSlot`` union-key comparison semantics.
        """
        slot_names = self.slots.keys() | request.slots.keys() | limit.slots.keys()
        for slot_name in slot_names:
            allocation = self.slots.get(slot_name)
            allocated = allocation.allocated if allocation is not None else Decimal(0)
            requested = request.slots.get(slot_name, Decimal(0))
            if allocated + requested > limit.slots.get(slot_name, Decimal(0)):
                return True
        return False

    def _merged_slots(self, request: ResourceRequest) -> dict[ResourceSlotName, SlotAllocation]:
        """Requested slots accumulate as reservations (the session is not running yet)."""
        slots = dict(self.slots)
        for slot_name, amount in request.slots.items():
            current = slots.get(slot_name, SlotAllocation(Decimal(0), Decimal(0)))
            slots[slot_name] = SlotAllocation(
                requested=current.requested + amount,
                used=current.used,
            )
        return slots

    def add(self, request: ResourceRequest) -> ResourceAllocation:
        """Return a new allocation with the request folded in."""
        return ResourceAllocation(slots=self._merged_slots(request))


@dataclass(frozen=True)
class UserResourceAllocation(ResourceAllocation):
    """User-scope occupancy: slots plus global active session counts."""

    session_count: int
    sftp_session_count: int

    @classmethod
    @override
    def empty(cls) -> UserResourceAllocation:
        return UserResourceAllocation(slots={}, session_count=0, sftp_session_count=0)

    def count_exceeds(self, request: SessionResourceRequest, limit: UserResourceLimit) -> bool:
        """True if adding the request pushes a session count past its cap.

        Only the session kind actually being requested is enforced; a None
        cap means unlimited.
        """
        if (
            request.session_count > 0
            and limit.max_session_count is not None
            and self.session_count + request.session_count > limit.max_session_count
        ):
            return True
        return (
            request.sftp_session_count > 0
            and limit.max_sftp_session_count is not None
            and self.sftp_session_count + request.sftp_session_count > limit.max_sftp_session_count
        )

    @override
    def add(self, request: ResourceRequest) -> UserResourceAllocation:
        """Return a new allocation with the slots folded in (counts unchanged)."""
        return UserResourceAllocation(
            slots=self._merged_slots(request),
            session_count=self.session_count,
            sftp_session_count=self.sftp_session_count,
        )

    def add_session(self, request: SessionResourceRequest) -> UserResourceAllocation:
        """Return a new allocation with a session request folded in, counts included."""
        return UserResourceAllocation(
            slots=self._merged_slots(request),
            session_count=self.session_count + request.session_count,
            sftp_session_count=self.sftp_session_count + request.sftp_session_count,
        )


@dataclass
class ResourceOccupancySnapshot:
    """Cluster-wide occupancy per owner scope.

    Keypair-scoped occupancy was folded into the user scope; agent-level
    state (slot resources, container counts) lives on ``AgentMeta``/
    ``AgentInfo``, not here. Only the user scope tracks session counts
    (the only scope with count limits).
    """

    by_user: MutableMapping[UserID, UserResourceAllocation]
    by_project: MutableMapping[ProjectID, ResourceAllocation]
    by_domain: MutableMapping[DomainID, ResourceAllocation]

    def add_occupancy(
        self,
        user_id: UserID,
        project_id: ProjectID,
        domain_id: DomainID,
        request: SessionResourceRequest,
    ) -> None:
        """Accumulate an in-batch allocation into every owner scope."""
        self.by_user[user_id] = self.by_user.get(
            user_id, UserResourceAllocation.empty()
        ).add_session(request)
        self.by_project[project_id] = self.by_project.get(
            project_id, ResourceAllocation.empty()
        ).add(request)
        self.by_domain[domain_id] = self.by_domain.get(domain_id, ResourceAllocation.empty()).add(
            request
        )


@dataclass(frozen=True)
class ResourcePolicySnapshot:
    """Resource limits per owner scope (global entities)."""

    by_user: Mapping[UserID, UserResourceLimit]
    by_project: Mapping[ProjectID, ResourceLimit]
    by_domain: Mapping[DomainID, ResourceLimit]


@dataclass
class SessionDependencySnapshot:
    """Snapshot of session dependencies."""

    by_session: Mapping[SessionId, list[SessionDependencyInfo]]


@dataclass
class ResourceGroupSchedulingPolicy:
    """How the resource group schedules: pool keys for sequencer/selector."""

    # Sequencing strategy name (sequencer pool key)
    scheduler: str
    # Agent selection strategy (selector pool key)
    agent_selection_strategy: AgentSelectionStrategy


@dataclass
class ResourceGroupScopeSnapshot:
    """Scheduling execution context of the resource group being scheduled."""

    # The group's schedulable agents and their aggregate capacity
    resources: ResourceGroupResource
    # Dependency status for this resource group's pending sessions
    session_dependencies: SessionDependencySnapshot
    # Scheduling policy configured on the resource group
    policy: ResourceGroupSchedulingPolicy


@dataclass
class GlobalScopeSnapshot:
    """Cluster-wide validation state, independent of the resource group."""

    # Cluster-wide occupancy per owner scope
    occupancy: ResourceOccupancySnapshot
    # Resource limits per owner scope
    resource_policy: ResourcePolicySnapshot
    # Per-agent container cap from manager configuration
    agent_limit: AgentLimit


@dataclass
class SystemSnapshot:
    """Complete snapshot of system state for scheduling decisions.

    Split by data scope: ``resource_group`` holds the execution context of
    the resource group being scheduled, ``global_scope`` holds the
    cluster-wide state limits are validated against.
    """

    resource_group: ResourceGroupScopeSnapshot
    global_scope: GlobalScopeSnapshot
    # DB-sourced time the snapshot was taken; time-based validations compare
    # against this instead of per-server clocks (HA clock-skew safety)
    observed_at: datetime
