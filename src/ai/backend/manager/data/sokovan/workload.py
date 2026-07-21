"""Workload data types for scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionStatus


@dataclass(frozen=True)
class UserResourcePolicy:
    """Resource policy for a user, applied per user by the scheduler.

    All limits are sourced from the user's main keypair policy (no
    user-level DB columns yet). This is the single policy the scheduler
    snapshot carries; per-keypair policies are no longer tracked.
    """

    name: str
    total_resource_slots: ResourceSlot
    max_concurrent_sessions: int | None
    max_concurrent_sftp_sessions: int | None


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
    # User ID for user resource limit checks
    user_uuid: UserID
    # Project ID for project resource limit checks
    project_id: ProjectID
    # Domain ID for domain resource limit checks
    domain_id: DomainID
    # Scaling group name
    scaling_group: str
    # Scaling group id
    resource_group_id: ResourceGroupID
    # Priority level (higher value = higher priority)
    priority: int = 0
    # Scope-local preemption priority among the owner's own sessions
    # (higher preempts lower; decoupled from the global scheduler ``priority``)
    job_priority: int = 0
    # Session type (INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes = SessionTypes.INTERACTIVE
    # Cluster mode (SINGLE_NODE or MULTI_NODE)
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    # Scheduled start time for batch sessions
    starts_at: datetime | None = None
    # Whether this is a private session (SFTP)
    is_private: bool = False
    # Whether this session can be preempted
    is_preemptible: bool = True
    # Kernels to be scheduled for this session
    kernels: list[KernelWorkload] = field(default_factory=list)
    # Manually designated agent (for superadmin)
    designated_agent_ids: list[AgentId] | None = None
    # Kernel counts at endpoint for each agent (for inference session spreading)
    # Only populated for inference sessions with enforce_spreading_endpoint_replica
    kernel_counts_at_endpoint: dict[AgentId, int] | None = None
    # Agents that previously failed for this session (populated from Valkey during scheduling)
    failed_agent_ids: frozenset[AgentId] = frozenset()
