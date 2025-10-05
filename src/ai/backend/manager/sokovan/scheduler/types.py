from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    AutoPullBehavior,
    ClusterMode,
    ClusterSSHPortMapping,
    ImageConfig,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
    SlotName,
    SlotTypes,
)
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import MainKernelNotFound, TooManyKernelsFound
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.network import NetworkType
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
    # Keypair associated with the session
    access_key: AccessKey
    # Phases that passed during scheduling
    passed_phases: list[SchedulingPredicate] = field(default_factory=list)
    # Phases that failed during scheduling (normally empty for successful allocations)
    failed_phases: list[SchedulingPredicate] = field(default_factory=list)

    @classmethod
    def from_agent_selections(
        cls,
        session_workload: SessionWorkload,
        selections: list["AgentSelection"],
        scaling_group: str,
    ) -> "SessionAllocation":
        """
        Build a SessionAllocation from agent selection results.

        :param session_workload: The original session workload
        :param selections: List of agent selection results
        :param scaling_group: The scaling group name
        :param access_key: The access key associated with the session
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
            access_key=session_workload.access_key,
        )

    def unique_agent_ids(self) -> list[AgentId]:
        """Extract unique agent IDs from kernel allocations."""
        return list({
            kernel_alloc.agent_id
            for kernel_alloc in self.kernel_allocations
            if kernel_alloc.agent_id is not None
        })


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

    def to_status_data(self, current_retries: int) -> dict:
        """Convert failure to status data dictionary for storage."""
        return {
            "passed_predicates": [p.serialize() for p in self.passed_phases],
            "failed_predicates": [p.serialize() for p in self.failed_phases],
            "retries": current_retries + 1,
            "last_try": self.last_try.isoformat() if self.last_try else None,
            "msg": self.msg,
        }


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


@dataclass
class KernelBindingData:
    """Kernel-agent binding data for precondition checking and session starting."""

    kernel_id: UUID
    agent_id: Optional[AgentId]
    agent_addr: Optional[str]
    scaling_group: str
    image: str
    architecture: str
    status: Optional[KernelStatus] = None
    status_changed: Optional[float] = None
    cluster_role: str = DEFAULT_ROLE
    cluster_idx: int = 0
    local_rank: int = 0
    cluster_hostname: Optional[str] = None
    uid: Optional[int] = None
    main_gid: Optional[int] = None
    gids: list[int] = field(default_factory=list)
    requested_slots: ResourceSlot = field(default_factory=ResourceSlot)
    resource_opts: dict[str, Any] = field(default_factory=dict)
    bootstrap_script: Optional[str] = None
    startup_command: Optional[str] = None
    preopen_ports: list[int] = field(default_factory=list)
    internal_data: Optional[dict[str, Any]] = None
    vfolder_mounts: list[Any] = field(
        default_factory=list
    )  # Would be list[VFolderMount] in full impl


@dataclass(frozen=True)
class ImageIdentifier:
    """Identifier for an image with architecture."""

    image: str
    architecture: str


@dataclass
class ImageConfigData:
    """Image configuration data resolved from database."""

    canonical: str
    architecture: str
    project: Optional[str]
    is_local: bool
    digest: str
    labels: dict[str, str]
    registry_name: str
    registry_url: str
    registry_username: Optional[str]
    registry_password: Optional[str]

    def to_image_config(self, auto_pull: AutoPullBehavior) -> ImageConfig:
        """
        Convert ImageConfigData to ImageConfig format for agents.

        :param auto_pull: Auto pull behavior setting
        :return: ImageConfig dictionary for agent RPC calls
        """
        return ImageConfig(
            architecture=self.architecture,
            project=self.project,
            canonical=self.canonical,
            is_local=self.is_local,
            digest=self.digest,
            labels=self.labels,
            repo_digest=None,
            registry={
                "name": self.registry_name,
                "url": self.registry_url,
                "username": self.registry_username,
                "password": self.registry_password,
            },
            auto_pull=auto_pull,
        )


@dataclass
class SessionDataForPull:
    """Data for a session that needs image pulling."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    kernels: list[KernelBindingData]


@dataclass
class SessionDataForStart:
    """Data for a session ready to start with full details."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    session_type: SessionTypes
    name: str
    cluster_mode: ClusterMode
    kernels: list[KernelBindingData]
    user_uuid: UUID
    user_email: str
    user_name: str
    environ: dict[str, str]
    network_type: Optional[NetworkType] = None
    network_id: Optional[str] = None


@dataclass
class ScheduledSessionData:
    """Data for a scheduled session ready for precondition check."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    session_type: SessionTypes
    name: str
    kernels: list[KernelBindingData]
    # Additional fields for PREPARED sessions
    cluster_mode: Optional[ClusterMode] = None
    user_uuid: Optional[UUID] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    network_type: Optional[NetworkType] = None
    network_id: Optional[str] = None


@dataclass
class SessionsForPullWithImages:
    """Sessions for image pulling with their image configurations."""

    sessions: list[SessionDataForPull]
    image_configs: dict[str, ImageConfigData]


@dataclass
class SessionsForStartWithImages:
    """Sessions for starting with their image configurations."""

    sessions: list[SessionDataForStart]
    image_configs: dict[str, ImageConfigData]


@dataclass
class ScheduledSessionsWithImages:
    """Scheduled sessions with their image configurations."""

    sessions: list[ScheduledSessionData]
    image_configs: dict[str, ImageConfigData]


@dataclass
class KernelStartData:
    """Kernel data for starting a session."""

    kernel_id: UUID
    agent_id: AgentId
    agent_addr: str
    scaling_group: str
    image: str
    architecture: str
    cluster_role: str
    cluster_idx: int
    requested_slots: ResourceSlot
    resource_opts: dict[str, Any]
    preopen_ports: list[int]
    container_id: Optional[str] = None
    cluster_hostname: Optional[str] = None
    bootstrap_script: Optional[str] = None
    startup_command: Optional[str] = None


@dataclass
class PreparedSessionData:
    """Data for a prepared session ready to start."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    session_type: SessionTypes
    name: str
    cluster_mode: ClusterMode
    kernels: list[KernelStartData]
    user_uuid: UUID
    user_email: str
    user_name: str
    network_type: Optional[NetworkType] = None
    network_id: Optional[str] = None


@dataclass
class PreparedSessionsWithImages:
    """Prepared sessions with their image configurations."""

    sessions: list[PreparedSessionData]
    image_configs: dict[str, ImageConfigData]


@dataclass
class NetworkSetup:
    """Network configuration for a session."""

    network_name: Optional[str] = None
    network_config: dict[str, Any] = field(default_factory=dict)
    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None


@dataclass
class SessionStartResult:
    """Result of a session start operation."""

    session_id: SessionId
    success: bool
    error: Optional[str] = None
    error_info: Optional[ErrorStatusInfo] = None


@dataclass
class KernelCreationInfo:
    """Information about kernel creation from agent."""

    container_id: Optional[str] = None
    resource_spec: Optional[dict[str, Any]] = None
    attached_devices: dict[str, Any] = field(default_factory=dict)
    repl_in_port: Optional[int] = None
    repl_out_port: Optional[int] = None
    stdin_port: Optional[int] = None
    stdout_port: Optional[int] = None
    service_ports: list[int] = field(default_factory=list)
    kernel_host: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KernelCreationInfo":
        """Create from dictionary, handling missing or invalid fields."""
        return cls(
            container_id=data.get("container_id"),
            resource_spec=data.get("resource_spec"),
            attached_devices=data.get("attached_devices", {}),
            repl_in_port=data.get("repl_in_port"),
            repl_out_port=data.get("repl_out_port"),
            stdin_port=data.get("stdin_port"),
            stdout_port=data.get("stdout_port"),
            service_ports=data.get("service_ports", []),
            kernel_host=data.get("kernel_host"),
        )

    def get_resource_allocations(self) -> ResourceSlot:
        """
        Extract resource allocations from resource_spec.
        Compatible with AgentRegistry.convert_resource_spec_to_resource_slot() format.

        Handles the agent-side nested format:
        allocations: {
            "device_type": {
                "slot_name": {
                    "device_id": "value"
                }
            }
        }
        """
        if not self.resource_spec or "allocations" not in self.resource_spec:
            return ResourceSlot()

        allocations = self.resource_spec["allocations"]
        return self.convert_allocations_to_resource_slot(allocations)

    @staticmethod
    def convert_allocations_to_resource_slot(allocations: dict[str, Any]) -> ResourceSlot:
        """
        Convert per-device resource spec allocations (agent-side format)
        back into a resource slot (manager-side format).

        This is a static method that mirrors AgentRegistry.convert_resource_spec_to_resource_slot()
        for compatibility.

        Args:
            allocations: The allocations dict from resource_spec

        Returns:
            ResourceSlot with aggregated resource values
        """
        from decimal import Decimal

        from ai.backend.common.types import BinarySize

        if not allocations or not isinstance(allocations, dict):
            return ResourceSlot()

        slots = ResourceSlot()

        # Handle the nested structure from agent
        for alloc_map in allocations.values():
            if not isinstance(alloc_map, dict):
                continue

            for slot_name, allocation_by_device in alloc_map.items():
                if not isinstance(allocation_by_device, dict):
                    # If it's not the expected nested structure,
                    # try to use it directly as a value
                    if allocation_by_device is not None:
                        slots[slot_name] = str(allocation_by_device)
                    continue

                # Sum allocations across devices
                total_allocs: list[Decimal] = []
                for allocation in allocation_by_device.values():
                    if allocation is None:
                        continue

                    # Handle BinarySize values (e.g., "1073741824b", "1g")
                    if (
                        isinstance(allocation, str)
                        and len(allocation) > 0
                        and BinarySize.suffix_map.get(allocation[-1].lower()) is not None
                    ):
                        total_allocs.append(Decimal(BinarySize.from_str(allocation)))
                    else:
                        # Regular decimal value or special values like "Infinity"
                        total_allocs.append(Decimal(allocation))

                if total_allocs:
                    slots[slot_name] = str(sum(total_allocs))

        return slots


@dataclass(frozen=True)
class KernelTransitionData:
    """Kernel information for state transitions."""

    kernel_id: str
    agent_id: AgentId
    agent_addr: str
    cluster_role: str  # DEFAULT_ROLE for main kernel
    container_id: Optional[str]
    startup_command: Optional[str]
    status_info: Optional[str]
    occupied_slots: Optional[ResourceSlot] = None


@dataclass(frozen=True)
class SessionTransitionData:
    """
    Session data for state transitions.
    Contains all necessary information for hooks without exposing database rows.
    """

    session_id: SessionId
    creation_id: str
    session_name: str
    session_type: SessionTypes
    access_key: AccessKey
    cluster_mode: ClusterMode
    network_type: Optional[NetworkType]
    network_id: Optional[str]
    status_info: Optional[str]
    kernels: list[KernelTransitionData]
    batch_timeout: Optional[int]  # For batch sessions

    @property
    def main_kernel(self) -> KernelTransitionData:
        """Get the main kernel (kernel with DEFAULT_ROLE as cluster_role)."""
        main_kernels = [k for k in self.kernels if k.cluster_role == DEFAULT_ROLE]
        if len(main_kernels) > 1:
            raise TooManyKernelsFound(f"Session {self.session_id} has more than 1 main kernel")
        if len(main_kernels) == 0:
            raise MainKernelNotFound(f"Session {self.session_id} has no main kernel")
        return main_kernels[0]


@dataclass(frozen=True)
class SessionRunningData:
    """
    Data for updating a session to RUNNING state.
    Contains the calculated occupying_slots from all kernels.
    """

    session_id: SessionId
    occupying_slots: ResourceSlot
