"""Session and kernel lifecycle data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    BinarySize,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.session.types import SessionInfo
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import MainKernelNotFound, TooManyKernelsFound
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.network import NetworkType

from .image import ImageConfigData


@dataclass
class KernelBindingData:
    """Kernel-agent binding data for precondition checking and session starting."""

    kernel_id: KernelId
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
    def from_dict(cls, data: dict[str, Any]) -> KernelCreationInfo:
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
class SessionRunningData:
    """
    Data for updating a session to RUNNING state.
    Contains the calculated occupying_slots from all kernels.
    """

    session_id: SessionId
    occupying_slots: ResourceSlot


@dataclass
class SessionWithKernels:
    """
    Bundles a session with its associated kernels.

    This is the primary data unit for scheduler operations,
    representing a session and all its kernels as an atomic unit.

    Attributes:
        session_info: Session information including lifecycle data
        kernel_infos: List of kernels belonging to this session
        phase_attempts: Number of attempts for current phase from scheduling history
                       (used for failure classification: give_up when >= max_retries)
        phase_started_at: When the current phase started from scheduling history
                         (used for failure classification: expired when timeout exceeded)
    """

    session_info: SessionInfo
    kernel_infos: list[KernelInfo]
    phase_attempts: int = 0
    phase_started_at: Optional[datetime] = None

    @property
    def main_kernel(self) -> KernelInfo:
        """Get the main kernel (kernel with DEFAULT_ROLE as cluster_role)."""
        main_kernels = [k for k in self.kernel_infos if k.cluster.cluster_role == DEFAULT_ROLE]
        if len(main_kernels) > 1:
            raise TooManyKernelsFound(
                f"Session {self.session_info.identity.id} has more than 1 main kernel"
            )
        if len(main_kernels) == 0:
            raise MainKernelNotFound(f"Session {self.session_info.identity.id} has no main kernel")
        return main_kernels[0]
