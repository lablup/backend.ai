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

from ai.backend.common.types import (
    MountPermission,
    ServicePortProtocols,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderUsageMode,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduler.options import KernelConditions, KernelOrders

KernelStatusGQL = strawberry.enum(KernelStatus, name="KernelStatus", description="Added in 26.1.0")

SessionTypesGQL = strawberry.enum(
    SessionTypes,
    name="SessionType",
    description="Added in 26.1.0. Type of compute session.",
)

SessionResultGQL = strawberry.enum(
    SessionResult,
    name="SessionResult",
    description="Added in 26.1.0. Result status of a session execution.",
)

MountPermissionGQL = strawberry.enum(
    MountPermission,
    name="MountPermission",
    description="Added in 26.1.0. Permission level for virtual folder mounts.",
)

VFolderUsageModeGQL = strawberry.enum(
    VFolderUsageMode,
    name="VFolderUsageMode",
    description="Added in 26.1.0. Usage mode of a virtual folder.",
)


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


# ========== Resource Options Types ==========


@strawberry.type(
    name="ResourceOptsEntry",
    description=(
        "Added in 26.1.0. A single resource option entry with name and value. "
        "Resource options provide additional configuration like shared memory settings."
    ),
)
class ResourceOptsEntryGQL:
    """Single resource option entry with name and value."""

    name: str = strawberry.field(description="The name of this resource option (e.g., 'shmem').")
    value: str = strawberry.field(description="The value for this resource option (e.g., '64m').")


@strawberry.type(
    name="ResourceOpts",
    description=(
        "Added in 26.1.0. A collection of additional resource options. "
        "Contains configuration like shared memory and other resource-specific settings."
    ),
)
class ResourceOptsGQL:
    """Resource options containing multiple entries."""

    entries: list[ResourceOptsEntryGQL] = strawberry.field(
        description="List of resource option entries."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> ResourceOptsGQL | None:
        """Convert a Mapping to GraphQL type."""
        if data is None:
            return None
        entries = [ResourceOptsEntryGQL(name=k, value=str(v)) for k, v in data.items()]
        return cls(entries=entries)


# ========== Service Port Types ==========


ServicePortProtocolGQL = strawberry.enum(
    ServicePortProtocols,
    name="ServicePortProtocol",
    description="Added in 26.1.0. Protocol types for service ports.",
)


@strawberry.type(
    name="ServicePortEntry",
    description=(
        "Added in 26.1.0. A single service port entry representing an exposed service. "
        "Contains port mapping and protocol information for accessing kernel services."
    ),
)
class ServicePortEntryGQL:
    """Single service port entry with name, protocol, and port mappings."""

    name: str = strawberry.field(
        description="Name of the service (e.g., 'jupyter', 'tensorboard', 'ssh')."
    )
    protocol: ServicePortProtocolGQL = strawberry.field(
        description="Protocol type for this service port (http, tcp, preopen, internal)."
    )
    container_ports: list[int] = strawberry.field(description="Port numbers inside the container.")
    host_ports: list[int | None] = strawberry.field(
        description="Mapped port numbers on the host. May be null if not yet assigned."
    )
    is_inference: bool = strawberry.field(
        description="Whether this port is used for inference endpoints."
    )


@strawberry.type(
    name="ServicePorts",
    description=(
        "Added in 26.1.0. A collection of service ports exposed by a kernel. "
        "Each entry defines a service accessible through the kernel."
    ),
)
class ServicePortsGQL:
    """Service ports containing multiple port entries."""

    entries: list[ServicePortEntryGQL] = strawberry.field(
        description="List of service port entries."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> ServicePortsGQL | None:
        """Convert a service ports mapping to GraphQL type."""
        if data is None:
            return None
        entries = []
        for name, port_info in data.items():
            if isinstance(port_info, dict):
                entries.append(
                    ServicePortEntryGQL(
                        name=name,
                        protocol=ServicePortProtocolGQL(port_info.get("protocol", "tcp")),
                        container_ports=list(port_info.get("container_ports", [])),
                        host_ports=list(port_info.get("host_ports", [])),
                        is_inference=port_info.get("is_inference", False),
                    )
                )
        return cls(entries=entries)


# ========== Status History Types ==========


@strawberry.type(
    name="StatusHistoryEntry",
    description=(
        "Added in 26.1.0. A single status history entry recording a status transition. "
        "Contains the status name and the timestamp when the kernel entered that status."
    ),
)
class StatusHistoryEntryGQL:
    """Single status history entry with status and timestamp."""

    status: str = strawberry.field(
        description="The kernel status name (e.g., 'PENDING', 'RUNNING', 'TERMINATED')."
    )
    timestamp: datetime = strawberry.field(
        description="Timestamp when the kernel entered this status."
    )


@strawberry.type(
    name="StatusHistory",
    description=(
        "Added in 26.1.0. A collection of status history entries for a kernel. "
        "Records the progression of status changes throughout the kernel's lifecycle."
    ),
)
class StatusHistoryGQL:
    """Status history containing multiple entries."""

    entries: list[StatusHistoryEntryGQL] = strawberry.field(
        description="List of status history entries in chronological order."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> StatusHistoryGQL | None:
        """Convert a status history mapping to GraphQL type."""
        if data is None:
            return None
        entries = []
        for status, timestamp in data.items():
            if timestamp is not None:
                if isinstance(timestamp, datetime):
                    entries.append(StatusHistoryEntryGQL(status=status, timestamp=timestamp))
                elif isinstance(timestamp, str):
                    entries.append(
                        StatusHistoryEntryGQL(
                            status=status,
                            timestamp=datetime.fromisoformat(timestamp),
                        )
                    )
        return cls(entries=entries)


# ========== Status Data Types ==========


@strawberry.type(
    name="StatusErrorInfo",
    description=(
        "Added in 26.1.0. Error information when a kernel enters an error state. "
        "Contains details about the source and nature of the error."
    ),
)
class StatusErrorInfoGQL:
    """Error information in status_data."""

    src: str = strawberry.field(
        description="Source of the error: 'agent' for agent errors, 'other' for other errors."
    )
    agent_id: str | None = strawberry.field(
        description="ID of the agent where the error occurred. Only present for agent errors."
    )
    name: str | None = strawberry.field(description="Name of the exception class.")
    repr: str | None = strawberry.field(description="String representation of the exception.")


@strawberry.type(
    name="SchedulerPredicate",
    description=(
        "Added in 26.1.0. A scheduler predicate result from scheduling attempts. "
        "Predicates are conditions checked during session scheduling."
    ),
)
class SchedulerPredicateGQL:
    """A scheduler predicate entry."""

    name: str = strawberry.field(
        description="Name of the predicate (e.g., 'concurrency', 'reserved_time')."
    )
    msg: str | None = strawberry.field(
        description="Message explaining why the predicate failed. Null for passed predicates."
    )


@strawberry.type(
    name="SchedulerInfo",
    description=(
        "Added in 26.1.0. Scheduler information including retry attempts and predicate results. "
        "Contains details about scheduling attempts when a session is pending."
    ),
)
class SchedulerInfoGQL:
    """Scheduler information in status_data."""

    retries: int | None = strawberry.field(
        description="Number of scheduling attempts made for this session."
    )
    last_try: str | None = strawberry.field(
        description="ISO 8601 timestamp of the last scheduling attempt."
    )
    msg: str | None = strawberry.field(description="Message from the last scheduling attempt.")
    failed_predicates: list[SchedulerPredicateGQL] | None = strawberry.field(
        description="List of predicates that failed during scheduling."
    )
    passed_predicates: list[SchedulerPredicateGQL] | None = strawberry.field(
        description="List of predicates that passed during scheduling."
    )


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
class StatusDataGQL:
    """Structured status data with optional sections."""

    error: StatusErrorInfoGQL | None = strawberry.field(
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
    def from_mapping(cls, data: Mapping[str, Any] | None) -> StatusDataGQL | None:
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
            error = StatusErrorInfoGQL(
                src=err.get("src", ""),
                agent_id=err.get("agent_id"),
                name=err.get("name"),
                repr=err.get("repr"),
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
                    SchedulerPredicateGQL(name=p.get("name", ""), msg=p.get("msg"))
                    for p in scheduler_data["failed_predicates"]
                ]

            if "passed_predicates" in scheduler_data:
                passed_predicates = [
                    SchedulerPredicateGQL(name=p.get("name", ""), msg=None)
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
    name="MetricStat",
    description=(
        "Added in 26.1.0. Statistical aggregation values for a metric over time. "
        "Contains min, max, sum, average, difference, and rate calculations."
    ),
)
class MetricStatGQL:
    """Statistical values for a metric."""

    min: str | None = strawberry.field(description="Minimum observed value.")
    max: str | None = strawberry.field(description="Maximum observed value.")
    sum: str | None = strawberry.field(description="Sum of all observed values.")
    avg: str | None = strawberry.field(description="Average of observed values.")
    diff: str | None = strawberry.field(description="Difference from previous measurement.")
    rate: str | None = strawberry.field(description="Rate of change per second.")


@strawberry.type(
    name="MetricValue",
    description=(
        "Added in 26.1.0. A metric measurement with current value, capacity, and statistics. "
        "Used for resource utilization metrics like CPU, memory, and I/O."
    ),
)
class MetricValueGQL:
    """A single metric measurement."""

    current: str = strawberry.field(description="Current measured value.")
    capacity: str | None = strawberry.field(
        description="Maximum capacity for this metric. Null for unbounded metrics."
    )
    pct: str | None = strawberry.field(
        description="Percentage utilization (current/capacity * 100)."
    )
    unit_hint: str | None = strawberry.field(
        description="Unit hint for display (e.g., 'bytes', 'msec', 'percent')."
    )
    stats: MetricStatGQL | None = strawberry.field(
        description="Statistical aggregation values over time."
    )


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
            if isinstance(metric_value, dict):
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
                            current=str(metric_value.get("current", "0")),
                            capacity=str(metric_value["capacity"])
                            if metric_value.get("capacity") is not None
                            else None,
                            pct=str(metric_value.get("pct")),
                            unit_hint=metric_value.get("unit_hint"),
                            stats=stats,
                        ),
                    )
                )
        return cls(entries=entries) if entries else None


# ========== Attached Device Types ==========


@strawberry.type(
    name="DeviceModelInfo",
    description=(
        "Added in 26.1.0. Information about a specific device model attached to a kernel. "
        "Contains device identification and capacity information."
    ),
)
class DeviceModelInfoGQL:
    """Device model information with ID, name, and capacity data."""

    device_id: str = strawberry.field(description="Unique identifier for the device instance.")
    model_name: str = strawberry.field(
        description="Model name of the device (e.g., 'NVIDIA A100', 'AMD MI250')."
    )
    data: JSON = strawberry.field(
        description="Device-specific capacity and capability information."
    )


@strawberry.type(
    name="AttachedDeviceEntry",
    description=(
        "Added in 26.1.0. A collection of devices of a specific type attached to a kernel. "
        "Groups devices by their device type (e.g., 'cuda', 'rocm')."
    ),
)
class AttachedDeviceEntryGQL:
    """Entry for a device type with its attached device instances."""

    device_type: str = strawberry.field(
        description="Type of the device (e.g., 'cuda', 'rocm', 'tpu')."
    )
    devices: list[DeviceModelInfoGQL] = strawberry.field(
        description="List of device instances of this type attached to the kernel."
    )


@strawberry.type(
    name="AttachedDevices",
    description=(
        "Added in 26.1.0. A collection of all devices attached to a kernel. "
        "Organized by device type, each containing multiple device instances."
    ),
)
class AttachedDevicesGQL:
    """Attached devices organized by device type."""

    entries: list[AttachedDeviceEntryGQL] = strawberry.field(
        description="List of device type entries, each containing attached device instances."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> AttachedDevicesGQL | None:
        """Convert an attached devices mapping to GraphQL type."""
        if data is None:
            return None
        entries = []
        for device_type, devices in data.items():
            if isinstance(devices, Sequence):
                device_infos = []
                for device in devices:
                    if isinstance(device, dict):
                        device_infos.append(
                            DeviceModelInfoGQL(
                                device_id=str(device.get("device_id", "")),
                                model_name=device.get("model_name", ""),
                                data=device.get("data", {}),
                            )
                        )
                entries.append(
                    AttachedDeviceEntryGQL(
                        device_type=device_type,
                        devices=device_infos,
                    )
                )
        return cls(entries=entries)


# ========== VFolder Mount Types ==========


@strawberry.type(
    name="VFolderMount",
    description=(
        "Added in 26.1.0. Information about a virtual folder mounted to a kernel. "
        "Contains mount path, permissions, and usage mode details."
    ),
)
class VFolderMountGQL:
    """Virtual folder mount information."""

    name: str = strawberry.field(description="Name of the virtual folder.")
    vfid: str = strawberry.field(description="Unique identifier of the virtual folder.")
    vfsubpath: str = strawberry.field(description="Subpath within the virtual folder to mount.")
    host_path: str = strawberry.field(
        description="Path on the host where the virtual folder is stored."
    )
    kernel_path: str = strawberry.field(
        description="Path inside the kernel container where the folder is mounted."
    )
    mount_perm: MountPermissionGQL = strawberry.field(
        description="Permission level for this mount (ro, rw, wd)."
    )
    usage_mode: VFolderUsageModeGQL = strawberry.field(
        description="Usage mode of the virtual folder (general, model, data)."
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VFolderMountGQL:
        """Convert a dict to VFolderMountGQL."""
        return cls(
            name=data.get("name", ""),
            vfid=str(data.get("vfid", "")),
            vfsubpath=str(data.get("vfsubpath", ".")),
            host_path=str(data.get("host_path", "")),
            kernel_path=str(data.get("kernel_path", "")),
            mount_perm=MountPermissionGQL(data.get("mount_perm", "ro")),
            usage_mode=VFolderUsageModeGQL(data.get("usage_mode", "general")),
        )


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
    reference: str = strawberry.field(
        description="The canonical reference of the container image (e.g., registry/repo:tag)."
    )
    registry: str | None = strawberry.field(description="The container registry hosting the image.")
    tag: str | None = strawberry.field(description="The tag of the container image.")
    architecture: str = strawberry.field(
        description="The CPU architecture the image is built for (e.g., x86_64, aarch64)."
    )


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
    attached_devices: AttachedDevicesGQL | None = strawberry.field(
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
    status_data: StatusDataGQL | None = strawberry.field(
        description="Structured data about the current status including error, scheduler, or lifecycle information."
    )
    status_history: StatusHistoryGQL | None = strawberry.field(
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
    internal_data: JSON | None = strawberry.field(
        description="Internal data stored with the kernel for system use."
    )


@strawberry.type(
    name="KernelV2",
    description="Added in 26.1.0. Represents a kernel (compute container) in Backend.AI.",
)
class KernelGQL(Node):
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
        # Extract image reference from ImageInfo
        image_ref = ""
        architecture = ""
        registry = None
        tag = None
        if kernel_info.image.identifier:
            image_ref = kernel_info.image.identifier.canonical
            architecture = kernel_info.image.identifier.architecture
        if kernel_info.image.registry:
            registry = kernel_info.image.registry
        if kernel_info.image.tag:
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
                reference=image_ref,
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
                attached_devices=AttachedDevicesGQL.from_mapping(
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
                status_data=StatusDataGQL.from_mapping(kernel_info.lifecycle.status_data),
                status_history=StatusHistoryGQL.from_mapping(kernel_info.lifecycle.status_history),
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
                internal_data=kernel_info.metadata.internal_data,
            ),
        )


KernelEdgeGQL = Edge[KernelGQL]


@strawberry.type(
    name="KernelConnectionV2",
    description="Added in 26.1.0. Connection type for paginated kernel results.",
)
class KernelConnectionV2GQL(Connection[KernelGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
