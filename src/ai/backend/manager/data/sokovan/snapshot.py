"""System snapshot data types for scheduling decisions."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ResourceSlot,
    SessionId,
    SlotName,
    SlotQuantity,
    SlotTypes,
)

from .workload import (
    PendingSessionInfo,
    SessionDependencyInfo,
    UserResourcePolicy,
)


@dataclass
class AgentOccupancy:
    """Agent occupancy information including resources and container count."""

    occupied_slots: list[SlotQuantity]
    container_count: int


@dataclass
class ResourceOccupancySnapshot:
    """Snapshot of current resource occupancy across different scopes.

    Resource-quota occupancy is tracked per user/group/domain (and per
    agent for selection); keypair-scoped occupancy was folded into the
    user scope.
    """

    by_user: MutableMapping[UserID, list[SlotQuantity]]
    by_project: MutableMapping[ProjectID, list[SlotQuantity]]
    by_domain: MutableMapping[DomainID, list[SlotQuantity]]
    by_agent: MutableMapping[AgentId, AgentOccupancy]  # Agent-level occupancy from actual kernels


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
class ConcurrencySnapshot:
    """Snapshot of concurrent session counts, scoped per user."""

    sessions_by_user: MutableMapping[UserID, int]
    sftp_sessions_by_user: MutableMapping[UserID, int]


@dataclass
class PendingSessionSnapshot:
    """Snapshot of pending sessions."""

    by_keypair: MutableMapping[AccessKey, list[PendingSessionInfo]]


@dataclass
class SessionDependencySnapshot:
    """Snapshot of session dependencies."""

    by_session: Mapping[SessionId, list[SessionDependencyInfo]]


@dataclass
class SystemSnapshot:
    """Represents a complete snapshot of the system's state for scheduling decisions."""

    # Total resource capacity
    total_capacity: ResourceSlot

    # Resource occupancy state
    resource_occupancy: ResourceOccupancySnapshot

    # Resource policies and limits
    resource_policy: ResourcePolicySnapshot

    # Concurrent session state
    concurrency: ConcurrencySnapshot

    # Pending session state
    pending_sessions: PendingSessionSnapshot

    # Session dependency state
    session_dependencies: SessionDependencySnapshot

    # Known slot types from etcd config
    known_slot_types: Mapping[SlotName, SlotTypes] = field(default_factory=dict)
