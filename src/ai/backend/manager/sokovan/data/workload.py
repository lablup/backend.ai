"""Workload data types for scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.models.session import SessionStatus


@dataclass(frozen=True)
class KeyPairResourcePolicy:
    """Resource policy for a keypair."""

    name: str
    total_resource_slots: ResourceSlot
    max_concurrent_sessions: Optional[int]
    max_concurrent_sftp_sessions: Optional[int]
    max_pending_session_count: Optional[int]
    max_pending_session_resource_slots: Optional[ResourceSlot]


@dataclass(frozen=True)
class UserResourcePolicy:
    """Resource policy for a user."""

    name: str
    total_resource_slots: ResourceSlot


@dataclass(frozen=True)
class PendingSessionInfo:
    """Information about a pending session."""

    session_id: SessionId
    requested_slots: ResourceSlot
    creation_time: datetime


@dataclass(frozen=True)
class SessionDependencyInfo:
    """Information about a session dependency."""

    depends_on: SessionId
    dependency_name: str
    dependency_status: SessionStatus
    dependency_result: SessionResult


@dataclass(frozen=True)
class KernelWorkload:
    """Represents a kernel workload within a session."""

    # Unique identifier of the kernel
    kernel_id: UUID
    # Image name for the kernel
    image: str
    # Architecture required for the kernel
    architecture: str
    # Resource requirements for this kernel
    requested_slots: ResourceSlot


@dataclass(frozen=True)
class SessionWorkload:
    """Represents a session workload for scheduling with minimal required fields."""

    # Session identifier
    session_id: SessionId
    # User identification for fairness calculation
    access_key: AccessKey
    # Resource requirements
    requested_slots: ResourceSlot
    # User UUID for user resource limit checks
    user_uuid: UUID
    # Group ID for group resource limit checks
    group_id: UUID
    # Domain name for domain resource limit checks
    domain_name: str
    # Scaling group name
    scaling_group: str
    # Priority level (higher value = higher priority)
    priority: int = 0
    # Session type (INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes = SessionTypes.INTERACTIVE
    # Cluster mode (SINGLE_NODE or MULTI_NODE)
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    # Scheduled start time for batch sessions
    starts_at: Optional[datetime] = None
    # Whether this is a private session (SFTP)
    is_private: bool = False
    # Kernels to be scheduled for this session
    kernels: list[KernelWorkload] = field(default_factory=list)
    # Manually designated agent (for superadmin)
    designated_agent_ids: Optional[list[AgentId]] = None
    # Kernel counts at endpoint for each agent (for inference session spreading)
    # Only populated for inference sessions with enforce_spreading_endpoint_replica
    kernel_counts_at_endpoint: Optional[dict[AgentId, int]] = None
