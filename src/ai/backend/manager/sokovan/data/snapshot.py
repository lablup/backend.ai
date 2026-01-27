"""System snapshot data types for scheduling decisions."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ResourceSlot,
    SessionId,
    SlotName,
    SlotTypes,
)

from .workload import (
    KeyPairResourcePolicy,
    PendingSessionInfo,
    SessionDependencyInfo,
    UserResourcePolicy,
)


@dataclass
class KeypairOccupancy:
    """Keypair occupancy information including resources and session counts."""

    occupied_slots: ResourceSlot
    session_count: int
    sftp_session_count: int


@dataclass
class AgentOccupancy:
    """Agent occupancy information including resources and container count."""

    occupied_slots: ResourceSlot
    container_count: int


@dataclass
class ResourceOccupancySnapshot:
    """Snapshot of current resource occupancy across different scopes."""

    by_keypair: MutableMapping[AccessKey, KeypairOccupancy]
    by_user: MutableMapping[UUID, ResourceSlot]
    by_group: MutableMapping[UUID, ResourceSlot]
    by_domain: MutableMapping[str, ResourceSlot]
    by_agent: MutableMapping[AgentId, AgentOccupancy]  # Agent-level occupancy from actual kernels


@dataclass(frozen=True)
class ResourcePolicySnapshot:
    """Snapshot of resource policies and limits."""

    keypair_policies: Mapping[AccessKey, KeyPairResourcePolicy]
    user_policies: Mapping[UUID, UserResourcePolicy]
    group_limits: Mapping[UUID, ResourceSlot]
    domain_limits: Mapping[str, ResourceSlot]


@dataclass
class ConcurrencySnapshot:
    """Snapshot of concurrent session counts."""

    sessions_by_keypair: MutableMapping[AccessKey, int]
    sftp_sessions_by_keypair: MutableMapping[AccessKey, int]


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
