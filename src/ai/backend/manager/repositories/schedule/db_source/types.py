"""
Data types returned by ScheduleDBSource.
These types include transformation methods to convert to common entities.
"""

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Mapping, Optional
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
    SlotName,
    SlotTypes,
)
from ai.backend.manager.models import (
    KernelStatus,
    SessionStatus,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentInfo
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    KernelWorkload,
    KeyPairResourcePolicy,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
    UserResourcePolicy,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.schedule.entity import (
        MarkTerminatingResult,
        SchedulingConfig,
        SchedulingContextData,
        SweptSessionInfo,
    )


@dataclass
class SchedulingSpec:
    """Specification of requirements for scheduling operations."""

    known_slot_types: Mapping[SlotName, SlotTypes]
    max_container_count: Optional[int] = None


@dataclass
class ScalingGroupMeta:
    """Scaling group metadata without ORM dependencies."""

    name: str
    scheduler: str
    scheduler_opts: ScalingGroupOpts


@dataclass
class AgentMeta:
    """Agent metadata without cached occupancy values."""

    id: AgentId
    addr: str
    architecture: str
    available_slots: ResourceSlot
    scaling_group: str


@dataclass
class DBKernelData:
    """Kernel data fetched from database."""

    id: UUID
    image: str
    architecture: str
    requested_slots: ResourceSlot
    agent: Optional[AgentId]

    def to_kernel_workload(self) -> KernelWorkload:
        """Convert to KernelWorkload entity."""
        return KernelWorkload(
            kernel_id=self.id,
            image=self.image,
            architecture=self.architecture,
            requested_slots=self.requested_slots,
        )


@dataclass
class DBPendingSessionData:
    """Pending session data fetched from database."""

    id: SessionId
    access_key: AccessKey
    requested_slots: ResourceSlot
    user_uuid: UUID
    group_id: UUID
    domain_name: str
    scaling_group_name: str
    priority: int
    session_type: SessionTypes
    cluster_mode: ClusterMode
    starts_at: Optional[datetime]
    is_private: bool
    kernels: list[DBKernelData]

    def to_session_workload(self) -> SessionWorkload:
        """Convert to SessionWorkload entity."""
        kernel_workloads = [k.to_kernel_workload() for k in self.kernels]
        return SessionWorkload(
            session_id=self.id,
            access_key=self.access_key,
            requested_slots=self.requested_slots,
            user_uuid=self.user_uuid,
            group_id=self.group_id,
            domain_name=self.domain_name,
            scaling_group=self.scaling_group_name,
            priority=self.priority,
            session_type=self.session_type,
            cluster_mode=self.cluster_mode,
            starts_at=self.starts_at,
            is_private=self.is_private,
            kernels=kernel_workloads,
            designated_agent=self.kernels[0].agent if self.kernels else None,
        )


@dataclass
class DBPendingSessions:
    """Wrapper for pending sessions with cached properties for entity extraction."""

    sessions: list[DBPendingSessionData]

    @cached_property
    def access_keys(self) -> set[AccessKey]:
        """Extract unique access keys from pending sessions."""
        return {s.access_key for s in self.sessions}

    @cached_property
    def user_uuids(self) -> set[UUID]:
        """Extract unique user UUIDs from pending sessions."""
        return {s.user_uuid for s in self.sessions}

    @cached_property
    def group_ids(self) -> set[UUID]:
        """Extract unique group IDs from pending sessions."""
        return {s.group_id for s in self.sessions}

    @cached_property
    def domain_names(self) -> set[str]:
        """Extract unique domain names from pending sessions."""
        return {s.domain_name for s in self.sessions}


@dataclass
class DBResourcePolicies:
    """Resource policies fetched from database."""

    keypair_policies: dict[AccessKey, KeyPairResourcePolicy]
    user_policies: dict[UUID, UserResourcePolicy]
    group_limits: dict[UUID, ResourceSlot]
    domain_limits: dict[str, ResourceSlot]


@dataclass
class DBSnapshotData:
    """Database snapshot data for system state."""

    resource_occupancy: ResourceOccupancySnapshot
    resource_policies: DBResourcePolicies
    session_dependencies: SessionDependencySnapshot

    def to_system_snapshot(
        self, known_slot_types: Mapping[SlotName, SlotTypes], total_capacity: ResourceSlot
    ) -> SystemSnapshot:
        """Convert to SystemSnapshot entity."""
        # Resource policies are already extracted in DBResourcePolicies
        resource_policy = ResourcePolicySnapshot(
            keypair_policies=self.resource_policies.keypair_policies,
            user_policies=self.resource_policies.user_policies,
            group_limits=self.resource_policies.group_limits,
            domain_limits=self.resource_policies.domain_limits,
        )

        # Create empty pending sessions and concurrency
        # These should be fetched from cache or calculated separately if needed
        pending_sessions = PendingSessionSnapshot(by_keypair={})
        concurrency = ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={})

        return SystemSnapshot(
            total_capacity=total_capacity,
            resource_occupancy=self.resource_occupancy,
            resource_policy=resource_policy,
            concurrency=concurrency,
            pending_sessions=pending_sessions,
            session_dependencies=self.session_dependencies,
            known_slot_types=known_slot_types,
        )


@dataclass
class DBSchedulingData:
    """All scheduling data fetched from database."""

    scaling_group: ScalingGroupMeta
    pending_sessions: DBPendingSessions
    agents: list[AgentMeta]
    snapshot_data: Optional[DBSnapshotData]
    spec: SchedulingSpec

    @cached_property
    def total_capacity(self) -> ResourceSlot:
        """Calculate total available capacity from all agents."""
        return sum((agent.available_slots for agent in self.agents), ResourceSlot())

    def to_scheduling_context(self) -> "SchedulingContextData":
        """Convert to SchedulingContextData entity."""
        from ai.backend.manager.repositories.schedule.entity import (
            SchedulingContextData,
        )

        pending_workloads = [s.to_session_workload() for s in self.pending_sessions.sessions]
        agent_infos = self._transform_agents_to_info()
        scheduling_config = self._create_scheduling_config()

        if self.snapshot_data:
            system_snapshot = self.snapshot_data.to_system_snapshot(
                self.spec.known_slot_types, self.total_capacity
            )
        else:
            # Create empty snapshot
            system_snapshot = SystemSnapshot(
                total_capacity=self.total_capacity,
                resource_occupancy=ResourceOccupancySnapshot(
                    by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
                ),
                resource_policy=ResourcePolicySnapshot(
                    keypair_policies={}, user_policies={}, group_limits={}, domain_limits={}
                ),
                concurrency=ConcurrencySnapshot(
                    sessions_by_keypair={}, sftp_sessions_by_keypair={}
                ),
                pending_sessions=PendingSessionSnapshot(by_keypair={}),
                session_dependencies=SessionDependencySnapshot(by_session={}),
                known_slot_types=self.spec.known_slot_types,
            )

        return SchedulingContextData(
            scheduling_config=scheduling_config,
            pending_sessions=pending_workloads,
            system_snapshot=system_snapshot,
            agents=agent_infos,
        )

    def _transform_agents_to_info(self) -> list[AgentInfo]:
        """Transform agent metadata to AgentInfo objects.

        Note: occupied_slots and container_count should be populated from
        kernel occupancy data, not from agent metadata.
        """
        agent_infos: list[AgentInfo] = []
        for agent in self.agents:
            agent_info = AgentInfo(
                agent_id=agent.id,
                agent_addr=agent.addr,
                architecture=agent.architecture,
                available_slots=agent.available_slots,
                occupied_slots=ResourceSlot(),  # Should be populated from kernel occupancy
                scaling_group=agent.scaling_group,
                container_count=0,  # Should be populated from kernel occupancy
            )
            agent_infos.append(agent_info)
        return agent_infos

    def _create_scheduling_config(self) -> "SchedulingConfig":
        """Create combined scheduling configuration."""
        from ai.backend.manager.repositories.schedule.entity import SchedulingConfig

        return SchedulingConfig(
            scheduler_name=self.scaling_group.scheduler,
            agent_selection_strategy=str(
                self.scaling_group.scheduler_opts.agent_selection_strategy
            ),
            max_container_count_per_agent=self.spec.max_container_count,
            enforce_spreading_endpoint_replica=self.scaling_group.scheduler_opts.enforce_spreading_endpoint_replica,
        )


@dataclass
class DBTerminatingKernelData:
    """Kernel data for termination processing."""

    kernel_id: str
    status: KernelStatus
    container_id: Optional[str]
    agent_id: Optional[AgentId]
    agent_addr: Optional[str]
    occupied_slots: ResourceSlot


@dataclass
class DBTerminatingSessionData:
    """Data for a session that needs to be terminated."""

    session_id: SessionId
    access_key: AccessKey
    creation_id: str
    status: SessionStatus
    status_info: str
    session_type: SessionTypes
    kernels: list[DBTerminatingKernelData]


@dataclass
class DBMarkTerminatingResult:
    """Result of marking sessions for termination in database."""

    cancelled_sessions: list[str]
    terminating_sessions: list[str]
    skipped_sessions: list[str]
    not_found_sessions: list[str]

    def to_mark_terminating_result(self) -> "MarkTerminatingResult":
        """Convert to MarkTerminatingResult entity."""
        from ai.backend.manager.repositories.schedule.entity import MarkTerminatingResult

        return MarkTerminatingResult(
            cancelled_sessions=self.cancelled_sessions,
            terminating_sessions=self.terminating_sessions,
            skipped_sessions=self.skipped_sessions,
            not_found_sessions=self.not_found_sessions,
        )


@dataclass
class DBSweptSessionInfo:
    """Information about a swept session from database."""

    session_id: SessionId
    creation_id: str

    def to_swept_session_info(self) -> "SweptSessionInfo":
        """Convert to SweptSessionInfo entity."""
        from ai.backend.manager.repositories.schedule.entity import SweptSessionInfo

        return SweptSessionInfo(
            session_id=self.session_id,
            creation_id=self.creation_id,
        )
