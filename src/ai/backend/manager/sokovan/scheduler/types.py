from collections.abc import Mapping
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
from ai.backend.manager.sokovan.scheduler.selectors.selector import (
    AgentSelectionConfig,
    AgentSelectionCriteria2,
    KernelRequirements,
    SessionMetadata,
)


@dataclass(frozen=True)
class KeyPairResourcePolicy:
    """Resource policy for a keypair."""

    name: str
    total_resource_slots: ResourceSlot
    max_concurrent_sessions: int
    max_concurrent_sftp_sessions: int
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
class ResourceOccupancySnapshot:
    """Snapshot of current resource occupancy across different scopes."""

    by_keypair: Mapping[AccessKey, ResourceSlot]
    by_user: Mapping[UUID, ResourceSlot]
    by_group: Mapping[UUID, ResourceSlot]
    by_domain: Mapping[str, ResourceSlot]


@dataclass(frozen=True)
class ResourcePolicySnapshot:
    """Snapshot of resource policies and limits."""

    keypair_policies: Mapping[AccessKey, KeyPairResourcePolicy]
    user_policies: Mapping[UUID, UserResourcePolicy]
    group_limits: Mapping[UUID, ResourceSlot]
    domain_limits: Mapping[str, ResourceSlot]


@dataclass(frozen=True)
class ConcurrencySnapshot:
    """Snapshot of concurrent session counts."""

    sessions_by_keypair: Mapping[AccessKey, int]
    sftp_sessions_by_keypair: Mapping[AccessKey, int]


@dataclass(frozen=True)
class PendingSessionSnapshot:
    """Snapshot of pending sessions."""

    by_keypair: Mapping[AccessKey, list[PendingSessionInfo]]


@dataclass(frozen=True)
class SessionDependencySnapshot:
    """Snapshot of session dependencies."""

    by_session: Mapping[SessionId, list[SessionDependencyInfo]]


@dataclass(frozen=True)
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
    designated_agent: Optional[AgentId] = None
    # Kernel counts at endpoint for each agent (for inference session spreading)
    # Only populated for inference sessions with enforce_spreading_endpoint_replica
    kernel_counts_at_endpoint: Optional[dict[AgentId, int]] = None

    def to_agent_selection_criteria2(
        self,
        max_container_count: Optional[int],
        enforce_spreading: bool,
    ) -> tuple[AgentSelectionCriteria2, AgentSelectionConfig]:
        """
        Convert to new agent selection criteria and config for scheduling.

        Args:
            max_container_count: Maximum containers per agent (from etcd config)
            enforce_spreading: Whether to enforce endpoint replica spreading (from sgroup_opts)

        Returns:
            Tuple of (criteria, config) for agent selection
        """
        # Create session metadata
        session_metadata = SessionMetadata(
            session_id=self.session_id,
            session_type=self.session_type,
            scaling_group=self.scaling_group,
            cluster_mode=self.cluster_mode,
        )

        # Create kernel requirements map
        kernel_requirements = {
            kernel.kernel_id: KernelRequirements(
                requested_slots=kernel.requested_slots,
                required_architecture=kernel.architecture,
            )
            for kernel in self.kernels
        }

        # Create selection criteria
        criteria = AgentSelectionCriteria2(
            session_metadata=session_metadata,
            kernel_requirements=kernel_requirements,
            kernel_counts_at_endpoint=self.kernel_counts_at_endpoint,
        )

        # Create selection config
        config = AgentSelectionConfig(
            max_container_count=max_container_count,
            enforce_spreading_endpoint_replica=enforce_spreading,
        )

        return criteria, config


@dataclass
class KernelAllocation:
    """Represents an allocation decision for a single kernel."""

    # Unique identifier of the kernel
    kernel_id: UUID
    # Identifier of the agent where this kernel will be allocated
    agent_id: AgentId
    # Network address of the agent
    agent_addr: str
    # Scaling group that the agent belongs to
    scaling_group: str
    # Resource slots requested by this kernel
    requested_slots: ResourceSlot
    # Host ports allocated for this kernel (empty set if none)
    allocated_host_ports: set[int] = field(default_factory=set)


@dataclass
class AllocationSnapshot:
    """
    Represents a complete allocation decision for a session.

    Contains allocation information for all kernels in the session,
    regardless of whether they are allocated to a single node or multiple nodes.
    """

    # Unique identifier of the session
    session_id: SessionId
    # Type of the session (INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes
    # Cluster mode of the session (SINGLE_NODE or MULTI_NODE)
    cluster_mode: ClusterMode
    # List of kernel allocations for this session
    kernel_allocations: list[KernelAllocation]
