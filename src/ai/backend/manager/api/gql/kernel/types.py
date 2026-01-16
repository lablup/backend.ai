"""GraphQL types for kernel management."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.types import SessionId
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.common.types import (
    DotfileInfoGQL,
    MetricStatGQL,
    MetricValueGQL,
    ResourceOptsGQL,
    SchedulerInfoGQL,
    SchedulerPredicateGQL,
    ServicePortsGQL,
    SessionResultGQL,
    SessionTypesGQL,
    SSHKeypairGQL,
    VFolderMountGQL,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.errors.kernel import InvalidKernelData
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders

KernelStatusGQL = strawberry.enum(KernelStatus, name="KernelStatus", description="Added in 26.1.0")


@strawberry.enum(
    name="KernelOrderField", description="Added in 26.1.0. Fields available for ordering kernels."
)
class KernelOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(
    name="KernelStatusFilter", description="Added in 26.1.0. Filter for kernel status."
)
class KernelStatusFilterGQL:
    in_: list[KernelStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[KernelStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        if self.in_:
            return KernelConditions.by_statuses(self.in_)
        if self.not_in:
            # For not_in, we need all statuses except the ones in the list
            all_statuses = set(KernelStatus)
            allowed_statuses = all_statuses - set(self.not_in)
            return KernelConditions.by_statuses(list(allowed_statuses))
        return None


@strawberry.input(
    name="KernelFilter", description="Added in 26.1.0. Filter criteria for querying kernels."
)
class KernelFilterGQL(GQLFilter):
    status: KernelStatusFilterGQL | None = None
    session_id: UUID | None = None

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.status:
            condition = self.status.build_condition()
            if condition:
                conditions.append(condition)
        if self.session_id:
            conditions.append(KernelConditions.by_session_ids([SessionId(self.session_id)]))
        return conditions


@strawberry.input(
    name="KernelOrderBy", description="Added in 26.1.0. Ordering specification for kernels."
)
class KernelOrderByGQL(GQLOrderBy):
    field: KernelOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case KernelOrderFieldGQL.CREATED_AT:
                return KernelOrders.created_at(ascending)
            case KernelOrderFieldGQL.ID:
                return KernelOrders.id(ascending)


# ========== Kernel Status History Types ==========


@strawberry.type(
    name="KernelStatusHistoryEntry",
    description=(
        "Added in 26.1.0. A single status history entry recording a status transition. "
        "Contains the status name and the timestamp when the kernel entered that status."
    ),
)
class KernelStatusHistoryEntryGQL:
    """Single status history entry with status and timestamp."""

    status: str = strawberry.field(
        description="The kernel status name (e.g., 'PENDING', 'RUNNING', 'TERMINATED')."
    )
    timestamp: datetime = strawberry.field(
        description="Timestamp when the kernel entered this status."
    )


@strawberry.type(
    name="KernelStatusHistory",
    description=(
        "Added in 26.1.0. A collection of status history entries for a kernel. "
        "Records the progression of status changes throughout the kernel's lifecycle."
    ),
)
class KernelStatusHistoryGQL:
    """Status history containing multiple entries."""

    entries: list[KernelStatusHistoryEntryGQL] = strawberry.field(
        description="List of status history entries in chronological order."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> KernelStatusHistoryGQL | None:
        """Convert a status history mapping to GraphQL type."""
        if data is None:
            return None
        entries = []
        for status, timestamp in data.items():
            if timestamp is None:
                continue
            if isinstance(timestamp, datetime):
                entries.append(KernelStatusHistoryEntryGQL(status=status, timestamp=timestamp))
            elif isinstance(timestamp, str):
                entries.append(
                    KernelStatusHistoryEntryGQL(
                        status=status,
                        timestamp=datetime.fromisoformat(timestamp),
                    )
                )
            else:
                raise InvalidKernelData(
                    f"Invalid timestamp type for status '{status}': "
                    f"expected datetime or str, got {type(timestamp).__name__}"
                )
        return cls(entries=entries)


# ========== Kernel Status Data Types ==========


@strawberry.type(
    name="KernelStatusErrorInfo",
    description=(
        "Added in 26.1.0. Error information when a kernel enters an error state. "
        "Contains details about the source and nature of the error."
    ),
)
class KernelStatusErrorInfoGQL:
    """Error information in kernel status_data."""

    src: str = strawberry.field(
        description="Source of the error: 'agent' for agent errors, 'other' for other errors."
    )
    agent_id: str | None = strawberry.field(
        description="ID of the agent where the error occurred. Only present for agent errors in debug mode."
    )
    name: str = strawberry.field(description="Name of the exception class.")
    repr: str = strawberry.field(description="String representation of the exception.")


@strawberry.type(
    name="KernelStatusData",
    description="Added in 26.1.0. Kernel-specific status data during lifecycle transitions.",
)
class KernelStatusDataGQL:
    """Kernel status data."""

    exit_code: int | None = strawberry.field(
        description="Exit code of the kernel process. Null if not yet terminated."
    )


@strawberry.type(
    name="SessionStatusData",
    description="Added in 26.1.0. Session-specific status data during lifecycle transitions.",
)
class SessionStatusDataGQL:
    """Session status data."""

    status: str | None = strawberry.field(
        description="Status string of the session (e.g., 'terminating')."
    )


@strawberry.type(
    name="StatusData",
    description=(
        "Added in 26.1.0. Structured status data containing error, scheduler, or lifecycle information. "
        "The populated fields depend on the kernel's current status and recent state transitions."
    ),
)
class KernelStatusDataContainerGQL:
    """Structured status data with optional sections."""

    error: KernelStatusErrorInfoGQL | None = strawberry.field(
        description="Error information when the kernel is in an error state."
    )
    scheduler: SchedulerInfoGQL | None = strawberry.field(
        description="Scheduler information during pending/scheduling states."
    )
    kernel: KernelStatusDataGQL | None = strawberry.field(
        description="Kernel-specific status data during lifecycle transitions."
    )
    session: SessionStatusDataGQL | None = strawberry.field(
        description="Session-specific status data during lifecycle transitions."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> KernelStatusDataContainerGQL | None:
        """Convert a status_data mapping to GraphQL type."""
        if data is None or not data:
            return None

        error = None
        scheduler = None
        kernel = None
        session = None

        # Parse error section
        if "error" in data:
            err = data["error"]
            error = KernelStatusErrorInfoGQL(
                src=err["src"],
                agent_id=err.get("agent_id"),
                name=err["name"],
                repr=err["repr"],
            )

        # Parse scheduler section (can be nested under "scheduler" or at top level)
        scheduler_data = data.get("scheduler", {})
        # Also check for top-level scheduler fields
        if not scheduler_data and any(
            k in data for k in ["retries", "last_try", "failed_predicates", "passed_predicates"]
        ):
            scheduler_data = data

        if scheduler_data:
            failed_predicates = None
            passed_predicates = None

            if "failed_predicates" in scheduler_data:
                failed_predicates = [
                    SchedulerPredicateGQL(name=p["name"], msg=p["msg"])
                    for p in scheduler_data["failed_predicates"]
                ]

            if "passed_predicates" in scheduler_data:
                passed_predicates = [
                    SchedulerPredicateGQL(name=p["name"], msg=None)
                    for p in scheduler_data["passed_predicates"]
                ]

            if any(
                k in scheduler_data
                for k in ["retries", "last_try", "msg", "failed_predicates", "passed_predicates"]
            ):
                scheduler = SchedulerInfoGQL(
                    retries=scheduler_data.get("retries"),
                    last_try=scheduler_data.get("last_try"),
                    msg=scheduler_data.get("msg"),
                    failed_predicates=failed_predicates,
                    passed_predicates=passed_predicates,
                )

        # Parse kernel section
        if "kernel" in data:
            kernel = KernelStatusDataGQL(exit_code=data["kernel"].get("exit_code"))

        # Parse session section
        if "session" in data:
            session = SessionStatusDataGQL(status=data["session"].get("status"))

        # Return None if all sections are empty
        if error is None and scheduler is None and kernel is None and session is None:
            return None

        return cls(error=error, scheduler=scheduler, kernel=kernel, session=session)


# ========== Kernel Statistics Types ==========


@strawberry.type(
    name="KernelStatEntry",
    description=(
        "Added in 26.1.0. A single kernel statistic entry with metric key and value. "
        "Common keys include: cpu_util, cpu_used, mem, io_read, io_write, net_rx, net_tx."
    ),
)
class KernelStatEntryGQL:
    """Single kernel statistic entry."""

    key: str = strawberry.field(description="Metric key name (e.g., 'cpu_util', 'mem', 'io_read').")
    value: MetricValueGQL = strawberry.field(description="The metric measurement value.")


@strawberry.type(
    name="KernelStat",
    description=(
        "Added in 26.1.0. Collection of kernel resource statistics. "
        "Contains utilization metrics for CPU, memory, I/O, network, and accelerators."
    ),
)
class KernelStatGQL:
    """Kernel statistics containing multiple metric entries."""

    entries: list[KernelStatEntryGQL] = strawberry.field(
        description="List of metric entries for this kernel."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> KernelStatGQL | None:
        """Convert a stat mapping to GraphQL type."""
        if data is None:
            return None
        entries = []
        for key, metric_value in data.items():
            if not isinstance(metric_value, dict):
                raise InvalidKernelData(
                    f"Invalid metric value type for key '{key}': "
                    f"expected dict, got {type(metric_value).__name__}"
                )
            # Extract stats if present
            stats = None
            stat_keys = ["min", "max", "sum", "avg", "diff", "rate"]
            stat_data = {}
            for stat_key in stat_keys:
                # Stats can be prefixed with "stats." in the serialized format
                prefixed_key = f"stats.{stat_key}"
                if prefixed_key in metric_value:
                    stat_data[stat_key] = metric_value[prefixed_key]
                elif stat_key in metric_value:
                    stat_data[stat_key] = metric_value[stat_key]

            if stat_data:
                stats = MetricStatGQL(
                    min=stat_data.get("min"),
                    max=stat_data.get("max"),
                    sum=stat_data.get("sum"),
                    avg=stat_data.get("avg"),
                    diff=stat_data.get("diff"),
                    rate=stat_data.get("rate"),
                )

            entries.append(
                KernelStatEntryGQL(
                    key=key,
                    value=MetricValueGQL(
                        current=str(metric_value["current"]),
                        capacity=str(metric_value["capacity"])
                        if metric_value.get("capacity") is not None
                        else None,
                        pct=str(metric_value["pct"])
                        if metric_value.get("pct") is not None
                        else None,
                        unit_hint=metric_value.get("unit_hint"),
                        stats=stats,
                    ),
                )
            )
        return cls(entries=entries) if entries else None


# ========== Kernel Internal Data Types ==========


@strawberry.type(
    name="KernelInternalData",
    description="Added in 26.1.0. Internal data stored with the kernel for system use.",
)
class KernelInternalDataGQL:
    dotfiles: list[DotfileInfoGQL] | None = strawberry.field(
        default=None,
        description="List of dotfiles to be provisioned in the kernel's filesystem.",
    )
    ssh_keypair: SSHKeypairGQL | None = strawberry.field(
        default=None, description="SSH keypair for secure access to the kernel."
    )
    model_definition_path: str | None = strawberry.field(
        default=None, description="Path to the model definition file for inference services."
    )
    runtime_variant: str | None = strawberry.field(
        default=None, description="Runtime variant identifier (e.g., 'custom')."
    )
    sudo_session_enabled: bool | None = strawberry.field(
        default=None, description="Whether sudo is enabled for this session."
    )
    block_service_ports: bool | None = strawberry.field(
        default=None,
        description="Whether to block service ports. If true, no services can be started.",
    )
    prevent_vfolder_mounts: bool | None = strawberry.field(
        default=None,
        description="Whether to prevent vfolder mounts (except .logs directory).",
    )
    docker_credentials: JSON | None = strawberry.field(
        default=None, description="Docker credentials for private registry access."
    )
    domain_socket_proxies: list[str] | None = strawberry.field(
        default=None,
        description="List of domain socket paths to proxy into the container.",
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> KernelInternalDataGQL | None:
        if not data:
            return None

        dotfiles = None
        if dotfiles_data := data.get("dotfiles"):
            if not isinstance(dotfiles_data, Sequence):
                raise InvalidKernelData(
                    f"Invalid dotfiles type: expected Sequence, got {type(dotfiles_data).__name__}"
                )
            dotfiles = []
            for df in dotfiles_data:
                if not isinstance(df, dict):
                    raise InvalidKernelData(
                        f"Invalid dotfile entry type: expected dict, got {type(df).__name__}"
                    )
                dotfiles.append(
                    DotfileInfoGQL(
                        path=df["path"],
                        data=df["data"],
                        perm=df["perm"],
                    )
                )

        ssh_keypair = None
        if keypair_data := data.get("ssh_keypair"):
            if not isinstance(keypair_data, dict):
                raise InvalidKernelData(
                    f"Invalid ssh_keypair type: expected dict, got {type(keypair_data).__name__}"
                )
            ssh_keypair = SSHKeypairGQL(
                public_key=keypair_data["public_key"],
                private_key=keypair_data["private_key"],
            )

        return cls(
            dotfiles=dotfiles,
            ssh_keypair=ssh_keypair,
            model_definition_path=data.get("model_definition_path"),
            runtime_variant=data.get("runtime_variant"),
            sudo_session_enabled=data.get("sudo_session_enabled"),
            block_service_ports=data.get("block_service_ports"),
            prevent_vfolder_mounts=data.get("prevent_vfolder_mounts"),
            docker_credentials=data.get("docker_credentials"),
            domain_socket_proxies=data.get("domain_socket_proxies"),
        )


# ========== Kernel Sub-Info Types ==========


@strawberry.type(
    name="KernelSessionInfo",
    description="Added in 26.1.0. Information about the session this kernel belongs to.",
)
class KernelSessionInfoGQL:
    session_id: UUID = strawberry.field(
        description="The unique identifier of the session this kernel belongs to."
    )
    creation_id: str | None = strawberry.field(
        description="The creation ID used when creating the session."
    )
    name: str | None = strawberry.field(description="The name of the session.")
    session_type: SessionTypesGQL = strawberry.field(
        description="The type of session (INTERACTIVE, BATCH, INFERENCE, SYSTEM)."
    )


@strawberry.type(
    name="KernelClusterInfo",
    description="Added in 26.1.0. Cluster configuration for a kernel in distributed sessions.",
)
class KernelClusterInfoGQL:
    cluster_mode: str = strawberry.field(
        description="The clustering mode (e.g., single-node, multi-node)."
    )
    cluster_size: int = strawberry.field(description="Total number of nodes in the cluster.")
    cluster_role: str = strawberry.field(
        description="The role of this kernel in the cluster (e.g., main, sub)."
    )
    cluster_idx: int = strawberry.field(
        description="The index of this kernel within the cluster (0-based)."
    )
    local_rank: int = strawberry.field(
        description="The local rank of this kernel for distributed computing."
    )
    cluster_hostname: str = strawberry.field(
        description="The hostname assigned to this kernel within the cluster network."
    )


@strawberry.type(
    name="KernelUserPermissionInfo",
    description="Added in 26.1.0. User permission and ownership information for a kernel.",
)
class KernelUserPermissionInfoGQL:
    user_uuid: UUID = strawberry.field(description="The UUID of the user who owns this kernel.")
    access_key: str = strawberry.field(description="The access key used to create this kernel.")
    domain_name: str = strawberry.field(description="The domain this kernel belongs to.")
    group_id: UUID = strawberry.field(description="The group (project) ID this kernel belongs to.")
    uid: int | None = strawberry.field(
        description="The Unix user ID for the kernel's container process."
    )
    main_gid: int | None = strawberry.field(
        description="The primary Unix group ID for the kernel's container process."
    )
    gids: list[int] | None = strawberry.field(
        description="Additional Unix group IDs for the kernel's container process."
    )


@strawberry.type(
    name="KernelImageInfo",
    description="Added in 26.1.0. Container image information for a kernel.",
)
class KernelImageInfoGQL:
    reference: str | None = strawberry.field(
        description="The canonical reference of the container image (e.g., registry/repo:tag). May be null for legacy kernels with missing image data."
    )
    registry: str | None = strawberry.field(description="The container registry hosting the image.")
    tag: str | None = strawberry.field(description="The tag of the container image.")
    architecture: str | None = strawberry.field(
        description="The CPU architecture the image is built for (e.g., x86_64, aarch64). May be null for legacy kernels."
    )


@strawberry.type(
    name="KernelDeviceModelInfo",
    description=(
        "Added in 26.1.0. Information about a specific device model attached to a kernel. "
        "Contains device identification and capacity information."
    ),
)
class KernelDeviceModelInfoGQL:
    """Device model information with ID, name, and capacity data."""

    device_id: str = strawberry.field(description="Unique identifier for the device instance.")
    model_name: str = strawberry.field(
        description="Model name of the device (e.g., 'NVIDIA A100', 'AMD MI250')."
    )
    data: JSON = strawberry.field(
        description="Device-specific capacity and capability information."
    )


@strawberry.type(
    name="KernelAttachedDeviceEntry",
    description=(
        "Added in 26.1.0. A collection of devices of a specific type attached to a kernel. "
        "Groups devices by their device type (e.g., 'cuda', 'rocm')."
    ),
)
class KernelAttachedDeviceEntryGQL:
    """Entry for a device type with its attached device instances."""

    device_type: str = strawberry.field(
        description="Type of the device (e.g., 'cuda', 'rocm', 'tpu')."
    )
    devices: list[KernelDeviceModelInfoGQL] = strawberry.field(
        description="List of device instances of this type."
    )


@strawberry.type(
    name="KernelAttachedDevices",
    description=(
        "Added in 26.1.0. A collection of all devices attached to a kernel. "
        "Organized by device type, each containing multiple device instances."
    ),
)
class KernelAttachedDevicesGQL:
    """Attached devices organized by device type."""

    entries: list[KernelAttachedDeviceEntryGQL] = strawberry.field(
        description="List of device type entries, each containing attached device instances."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> Self | None:
        """Convert an attached devices mapping to GraphQL type."""
        if data is None:
            return None
        entries = []
        for device_type, devices in data.items():
            if not isinstance(devices, Sequence):
                raise InvalidKernelData(
                    f"Invalid devices type for device_type '{device_type}': "
                    f"expected Sequence, got {type(devices).__name__}"
                )
            device_infos = []
            for device in devices:
                if not isinstance(device, dict):
                    raise InvalidKernelData(
                        f"Invalid device entry type for device_type '{device_type}': "
                        f"expected dict, got {type(device).__name__}"
                    )
                device_infos.append(
                    KernelDeviceModelInfoGQL(
                        device_id=str(device["device_id"]),
                        model_name=device["model_name"],
                        data=device.get("data", {}),
                    )
                )
            entries.append(
                KernelAttachedDeviceEntryGQL(
                    device_type=device_type,
                    devices=device_infos,
                )
            )
        return cls(entries=entries)


@strawberry.type(
    name="KernelResourceInfo",
    description="Added in 26.1.0. Resource allocation information for a kernel.",
)
class KernelResourceInfoGQL:
    scaling_group: str | None = strawberry.field(
        description="The scaling group this kernel is assigned to."
    )
    agent_id: str | None = strawberry.field(
        description="The ID of the agent running this kernel. Null if not yet assigned or hidden."
    )
    agent_addr: str | None = strawberry.field(
        description="The network address of the agent. Null if not yet assigned or hidden."
    )
    container_id: str | None = strawberry.field(
        description="The container ID on the agent. Null if container not yet created or hidden."
    )
    occupied_slots: ResourceSlotGQL = strawberry.field(
        description=dedent_strip("""
            The resource slots currently occupied by this kernel.
            Contains entries with resource types (e.g., cpu, mem, cuda.shares) and their quantities.
        """)
    )
    requested_slots: ResourceSlotGQL = strawberry.field(
        description=dedent_strip("""
            The resource slots originally requested for this kernel.
            May differ from occupied_slots due to scheduling adjustments.
        """)
    )
    occupied_shares: ResourceSlotGQL = strawberry.field(
        description="The fractional resource shares occupied by this kernel."
    )
    attached_devices: KernelAttachedDevicesGQL | None = strawberry.field(
        description="Information about attached devices (e.g., GPUs) allocated to this kernel."
    )
    resource_opts: ResourceOptsGQL | None = strawberry.field(
        description="Additional resource options and configurations for this kernel."
    )


@strawberry.type(
    name="KernelRuntimeInfo",
    description="Added in 26.1.0. Runtime configuration for a kernel.",
)
class KernelRuntimeInfoGQL:
    environ: list[str] | None = strawberry.field(
        description="Environment variables set for this kernel."
    )
    vfolder_mounts: list[VFolderMountGQL] | None = strawberry.field(
        description="List of virtual folders mounted to this kernel."
    )
    bootstrap_script: str | None = strawberry.field(
        description="Bootstrap script executed when the kernel starts."
    )
    startup_command: str | None = strawberry.field(
        description="Startup command executed after bootstrap."
    )


@strawberry.type(
    name="KernelNetworkInfo",
    description="Added in 26.1.0. Network configuration for a kernel.",
)
class KernelNetworkInfoGQL:
    kernel_host: str | None = strawberry.field(
        description="The hostname or IP address where the kernel is accessible."
    )
    repl_in_port: int = strawberry.field(description="The port for REPL input stream.")
    repl_out_port: int = strawberry.field(description="The port for REPL output stream.")
    service_ports: ServicePortsGQL | None = strawberry.field(
        description="Collection of service ports exposed by this kernel."
    )
    preopen_ports: list[int] | None = strawberry.field(
        description="List of ports that are pre-opened for this kernel."
    )
    use_host_network: bool = strawberry.field(
        description="Whether the kernel uses host network mode."
    )


@strawberry.type(
    name="KernelLifecycleInfo",
    description="Added in 26.1.0. Lifecycle and status information for a kernel.",
)
class KernelLifecycleInfoGQL:
    status: KernelStatusGQL = strawberry.field(
        description=dedent_strip("""
            Current status of the kernel (e.g., PENDING, RUNNING, TERMINATED).
            Indicates the kernel's position in its lifecycle.
        """)
    )
    result: SessionResultGQL = strawberry.field(
        description="The result of the kernel execution (UNDEFINED, SUCCESS, FAILURE)."
    )
    status_changed: datetime | None = strawberry.field(
        description="Timestamp when the kernel last changed status."
    )
    status_info: str | None = strawberry.field(
        description="Human-readable information about the current status."
    )
    status_data: KernelStatusDataContainerGQL | None = strawberry.field(
        description="Structured data about the current status including error, scheduler, or lifecycle information."
    )
    status_history: KernelStatusHistoryGQL | None = strawberry.field(
        description="History of status transitions with timestamps."
    )
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the kernel was created."
    )
    terminated_at: datetime | None = strawberry.field(
        description="Timestamp when the kernel was terminated. Null if still active."
    )
    starts_at: datetime | None = strawberry.field(
        description="Scheduled start time for the kernel, if applicable."
    )
    last_seen: datetime | None = strawberry.field(
        description="Timestamp when the kernel was last seen active."
    )


@strawberry.type(
    name="KernelMetricsInfo",
    description="Added in 26.1.0. Metrics and statistics for a kernel.",
)
class KernelMetricsInfoGQL:
    num_queries: int = strawberry.field(
        description="The number of queries/executions performed by this kernel."
    )
    last_stat: KernelStatGQL | None = strawberry.field(
        description="The last collected statistics for this kernel including CPU, memory, I/O, and network metrics."
    )


@strawberry.type(
    name="KernelMetadataInfo",
    description="Added in 26.1.0. Additional metadata for a kernel.",
)
class KernelMetadataInfoGQL:
    callback_url: str | None = strawberry.field(
        description="URL to call back when kernel status changes."
    )
    internal_data: KernelInternalDataGQL | None = strawberry.field(
        description="Internal data stored with the kernel for system use."
    )


# ========== Main Kernel Type ==========


@strawberry.type(
    name="KernelV2",
    description="Added in 26.1.0. Represents a kernel (compute container) in Backend.AI.",
)
class KernelV2GQL(Node):
    """Kernel type representing a compute container."""

    id: NodeID[str]

    session: KernelSessionInfoGQL = strawberry.field(
        description="Information about the session this kernel belongs to."
    )
    user_permission: KernelUserPermissionInfoGQL = strawberry.field(
        description="User permission and ownership information."
    )
    image: KernelImageInfoGQL = strawberry.field(description="Container image information.")
    network: KernelNetworkInfoGQL = strawberry.field(
        description="Network configuration and exposed ports."
    )
    cluster: KernelClusterInfoGQL = strawberry.field(
        description="Cluster configuration for distributed computing."
    )
    resource: KernelResourceInfoGQL = strawberry.field(
        description="Resource allocation and agent information."
    )
    runtime: KernelRuntimeInfoGQL = strawberry.field(
        description="Runtime configuration (environment, scripts)."
    )
    lifecycle: KernelLifecycleInfoGQL = strawberry.field(
        description="Lifecycle status and timestamps."
    )
    metrics: KernelMetricsInfoGQL = strawberry.field(
        description="Execution metrics and statistics."
    )
    metadata: KernelMetadataInfoGQL = strawberry.field(
        description="Additional metadata and internal data."
    )

    @classmethod
    def from_kernel_info(cls, kernel_info: KernelInfo, hide_agents: bool = False) -> Self:
        """Create KernelGQL from KernelInfo dataclass."""
        # Extract image reference from ImageInfo (may be None for legacy kernels)
        image_canonical: str | None = None
        architecture: str | None = None
        if kernel_info.image.identifier:
            image_canonical = kernel_info.image.identifier.canonical
            architecture = kernel_info.image.identifier.architecture
        registry = kernel_info.image.registry
        tag = kernel_info.image.tag
        if kernel_info.image.architecture:
            architecture = kernel_info.image.architecture

        return cls(
            id=ID(str(kernel_info.id)),
            session=KernelSessionInfoGQL(
                session_id=UUID(kernel_info.session.session_id),
                creation_id=kernel_info.session.creation_id,
                name=kernel_info.session.name,
                session_type=SessionTypesGQL(kernel_info.session.session_type),
            ),
            user_permission=KernelUserPermissionInfoGQL(
                user_uuid=kernel_info.user_permission.user_uuid,
                access_key=kernel_info.user_permission.access_key,
                domain_name=kernel_info.user_permission.domain_name,
                group_id=kernel_info.user_permission.group_id,
                uid=kernel_info.user_permission.uid,
                main_gid=kernel_info.user_permission.main_gid,
                gids=kernel_info.user_permission.gids,
            ),
            image=KernelImageInfoGQL(
                reference=image_canonical,
                registry=registry,
                tag=tag,
                architecture=architecture,
            ),
            network=KernelNetworkInfoGQL(
                kernel_host=kernel_info.network.kernel_host,
                repl_in_port=kernel_info.network.repl_in_port,
                repl_out_port=kernel_info.network.repl_out_port,
                service_ports=ServicePortsGQL.from_mapping(kernel_info.network.service_ports),
                preopen_ports=kernel_info.network.preopen_ports,
                use_host_network=kernel_info.network.use_host_network,
            ),
            cluster=KernelClusterInfoGQL(
                cluster_mode=kernel_info.cluster.cluster_mode,
                cluster_size=kernel_info.cluster.cluster_size,
                cluster_role=kernel_info.cluster.cluster_role,
                cluster_idx=kernel_info.cluster.cluster_idx,
                local_rank=kernel_info.cluster.local_rank,
                cluster_hostname=kernel_info.cluster.cluster_hostname,
            ),
            resource=KernelResourceInfoGQL(
                scaling_group=kernel_info.resource.scaling_group,
                agent_id=kernel_info.resource.agent if not hide_agents else None,
                agent_addr=kernel_info.resource.agent_addr if not hide_agents else None,
                container_id=kernel_info.resource.container_id if not hide_agents else None,
                occupied_slots=ResourceSlotGQL.from_resource_slot(
                    kernel_info.resource.occupied_slots
                )
                if kernel_info.resource.occupied_slots
                else ResourceSlotGQL(entries=[]),
                requested_slots=ResourceSlotGQL.from_resource_slot(
                    kernel_info.resource.requested_slots
                )
                if kernel_info.resource.requested_slots
                else ResourceSlotGQL(entries=[]),
                occupied_shares=ResourceSlotGQL.from_resource_slot(
                    kernel_info.resource.occupied_shares or {}
                ),
                attached_devices=KernelAttachedDevicesGQL.from_mapping(
                    kernel_info.resource.attached_devices
                ),
                resource_opts=ResourceOptsGQL.from_mapping(kernel_info.resource.resource_opts),
            ),
            runtime=KernelRuntimeInfoGQL(
                environ=kernel_info.runtime.environ,
                vfolder_mounts=[
                    VFolderMountGQL.from_dict(m) for m in kernel_info.runtime.vfolder_mounts
                ]
                if kernel_info.runtime.vfolder_mounts
                else None,
                bootstrap_script=kernel_info.runtime.bootstrap_script,
                startup_command=kernel_info.runtime.startup_command,
            ),
            lifecycle=KernelLifecycleInfoGQL(
                status=KernelStatusGQL(kernel_info.lifecycle.status),
                result=SessionResultGQL(kernel_info.lifecycle.result),
                status_changed=kernel_info.lifecycle.status_changed,
                status_info=kernel_info.lifecycle.status_info,
                status_data=KernelStatusDataContainerGQL.from_mapping(
                    kernel_info.lifecycle.status_data
                ),
                status_history=KernelStatusHistoryGQL.from_mapping(
                    kernel_info.lifecycle.status_history
                ),
                created_at=kernel_info.lifecycle.created_at,
                terminated_at=kernel_info.lifecycle.terminated_at,
                starts_at=kernel_info.lifecycle.starts_at,
                last_seen=kernel_info.lifecycle.last_seen,
            ),
            metrics=KernelMetricsInfoGQL(
                num_queries=kernel_info.metrics.num_queries,
                last_stat=KernelStatGQL.from_mapping(kernel_info.metrics.last_stat),
            ),
            metadata=KernelMetadataInfoGQL(
                callback_url=kernel_info.metadata.callback_url,
                internal_data=KernelInternalDataGQL.from_mapping(
                    kernel_info.metadata.internal_data
                ),
            ),
        )


KernelEdgeGQL = Edge[KernelV2GQL]


@strawberry.type(
    name="KernelConnectionV2",
    description="Added in 26.1.0. Connection type for paginated kernel results.",
)
class KernelConnectionV2GQL(Connection[KernelV2GQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
