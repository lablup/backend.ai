from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.models.session import SessionStatus

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.selectors.selector import (
        AgentSelection,
        AgentSelectionCriteria,
    )


@dataclass
class SchedulingPredicate:
    """Represents a scheduling predicate (passed or failed)."""

    # Name of the component that generated this predicate
    name: str
    # Message describing the result
    msg: str

    def serialize(self) -> dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {"name": self.name, "msg": self.msg}


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


@dataclass
class ResourceOccupancySnapshot:
    """Snapshot of current resource occupancy across different scopes."""

    by_keypair: MutableMapping[AccessKey, ResourceSlot]
    by_user: MutableMapping[UUID, ResourceSlot]
    by_group: MutableMapping[UUID, ResourceSlot]
    by_domain: MutableMapping[str, ResourceSlot]


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

    def to_agent_selection_criteria(self) -> "AgentSelectionCriteria":
        """
        Convert to new agent selection criteria for scheduling.

        Returns:
            AgentSelectionCriteria for agent selection
        """
        # Import here to avoid circular dependency
        from ai.backend.manager.sokovan.scheduler.selectors.selector import (
            AgentSelectionCriteria,
            KernelResourceSpec,
            SessionMetadata,
        )

        # Create session metadata
        session_metadata = SessionMetadata(
            session_id=self.session_id,
            session_type=self.session_type,
            scaling_group=self.scaling_group,
            cluster_mode=self.cluster_mode,
        )

        # Create kernel requirements map
        kernel_requirements = {
            kernel.kernel_id: KernelResourceSpec(
                requested_slots=kernel.requested_slots,
                required_architecture=kernel.architecture,
            )
            for kernel in self.kernels
        }

        # Create selection criteria
        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements=kernel_requirements,
            kernel_counts_at_endpoint=self.kernel_counts_at_endpoint,
        )

        return criteria


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
    # Host ports allocated for this kernel (empty set if none)
    allocated_host_ports: set[int] = field(default_factory=set)


@dataclass
class AgentAllocation:
    """Represents resource allocation to a specific agent."""

    # Identifier of the agent
    agent_id: AgentId
    # List of resource slots allocated to this agent
    allocated_slots: list[ResourceSlot]


@dataclass
class SessionAllocation:
    """Represents an allocation decision for a session with all its kernels."""

    # Unique identifier of the session
    session_id: SessionId
    # Type of the session (INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes
    # Cluster mode of the session (SINGLE_NODE or MULTI_NODE)
    cluster_mode: ClusterMode
    # Scaling group that the session belongs to
    scaling_group: str
    # List of kernel allocations for this session
    kernel_allocations: list[KernelAllocation]
    # List of agent allocations for this session
    agent_allocations: list[AgentAllocation]
    # Phases that passed during scheduling
    passed_phases: list[SchedulingPredicate] = field(default_factory=list)
    # Phases that failed during scheduling (normally empty for successful allocations)
    failed_phases: list[SchedulingPredicate] = field(default_factory=list)

    @classmethod
    def from_agent_selections(
        cls,
        session_workload: "SessionWorkload",
        selections: list["AgentSelection"],
        scaling_group: str,
    ) -> "SessionAllocation":
        """
        Build a SessionAllocation from agent selection results.

        :param session_workload: The original session workload
        :param selections: List of agent selection results
        :param scaling_group: The scaling group name
        :return: SessionAllocation with kernel and agent allocations
        """
        kernel_allocations: list[KernelAllocation] = []
        agent_allocation_map: dict[AgentId, AgentAllocation] = {}

        for selection in selections:
            resource_req = selection.resource_requirements
            selected_agent = selection.selected_agent

            # Track resource allocation for this agent
            if selected_agent.agent_id not in agent_allocation_map:
                agent_allocation_map[selected_agent.agent_id] = AgentAllocation(
                    agent_id=selected_agent.agent_id,
                    allocated_slots=[],
                )
            agent_allocation_map[selected_agent.agent_id].allocated_slots.append(
                resource_req.requested_slots
            )

            # Create kernel allocations
            for kernel_id in resource_req.kernel_ids:
                kernel_allocations.append(
                    KernelAllocation(
                        kernel_id=kernel_id,
                        agent_id=selected_agent.agent_id,
                        agent_addr=selected_agent.agent_addr,
                        scaling_group=selected_agent.scaling_group,
                    )
                )

        # Create session allocation
        agent_allocations = list(agent_allocation_map.values())

        return cls(
            session_id=session_workload.session_id,
            session_type=session_workload.session_type,
            cluster_mode=session_workload.cluster_mode,
            scaling_group=scaling_group,
            kernel_allocations=kernel_allocations,
            agent_allocations=agent_allocations,
        )


@dataclass
class SchedulingFailure:
    """Information about a scheduling failure for status updates.

    Maintains compatibility with frontend scheduler JSON structure:
    {
        failed_predicates: Array<{name: string, msg?: string}>,
        passed_predicates: Array<{name: string}>,
        retries: number,
        last_try: string,
        msg?: string
    }
    """

    session_id: SessionId
    passed_phases: list[SchedulingPredicate] = field(default_factory=list)
    failed_phases: list[SchedulingPredicate] = field(default_factory=list)
    last_try: Optional[datetime] = field(default_factory=lambda: datetime.now(tzutc()))
    msg: Optional[str] = None


@dataclass
class AllocationBatch:
    """Bundle of session allocations and scheduling failures for batch processing."""

    # Successful allocations to process
    allocations: list[SessionAllocation]
    # Failed scheduling attempts to update status for
    failures: list[SchedulingFailure]

    def get_agent_ids(self) -> set[AgentId]:
        """Extract all agent IDs from allocations for efficient pre-fetching."""
        agent_ids: set[AgentId] = set()
        for allocation in self.allocations:
            for agent_alloc in allocation.agent_allocations:
                agent_ids.add(agent_alloc.agent_id)
        return agent_ids


@dataclass
class SchedulingConfig:
    """Configuration needed for scheduling decisions."""

    max_container_count_per_agent: Optional[int]
    enforce_spreading_endpoint_replica: bool


@dataclass
class ScalingGroupInfo:
    """Scaling group configuration for scheduling."""

    scheduler_name: str
    agent_selection_strategy: AgentSelectionStrategy
    pending_timeout: timedelta
