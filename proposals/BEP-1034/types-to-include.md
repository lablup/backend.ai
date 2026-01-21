# KernelV2 GQL - Types to Include

This document contains detailed specifications of all types to be implemented.

## Table of Contents

1. [Enums](#enums)
2. [Input Types](#input-types)
3. [Status Data Types](#status-data-types)
4. [Statistics Types](#statistics-types)
5. [Internal Data Types](#internal-data-types)
6. [Sub-Info Types](#sub-info-types)
7. [Main Types](#main-types)
8. [Common Types](#common-types)

---

## Enums

### KernelStatusGQL

```python
KernelStatusGQL = strawberry.enum(
    KernelStatus, 
    name="KernelStatus", 
    description="Added in 26.1.0"
)
```

### KernelOrderFieldGQL

```python
@strawberry.enum(
    name="KernelOrderField", 
    description="Added in 26.1.0. Fields available for ordering kernels."
)
class KernelOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"
```

---

## Input Types

### KernelStatusFilterGQL

```python
@strawberry.input(
    name="KernelStatusFilter", 
    description="Added in 26.1.0. Filter for kernel status."
)
class KernelStatusFilterGQL:
    in_: list[KernelStatusGQL] | None = strawberry.field(name="in", default=None)
    not_in: list[KernelStatusGQL] | None = None

    def build_condition(self) -> QueryCondition | None:
        if self.in_:
            return KernelConditions.by_statuses(self.in_)
        if self.not_in:
            all_statuses = set(KernelStatus)
            allowed_statuses = all_statuses - set(self.not_in)
            return KernelConditions.by_statuses(list(allowed_statuses))
        return None
```

### KernelFilterGQL

```python
@strawberry.input(
    name="KernelFilter", 
    description="Added in 26.1.0. Filter criteria for querying kernels."
)
class KernelFilterGQL(GQLFilter):
    id: UUID | None = None
    status: KernelStatusFilterGQL | None = None
    session_id: UUID | None = None

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.id:
            conditions.append(KernelConditions.by_id(KernelId(self.id)))
        if self.status:
            condition = self.status.build_condition()
            if condition:
                conditions.append(condition)
        if self.session_id:
            conditions.append(KernelConditions.by_session_ids([SessionId(self.session_id)]))
        return conditions
```

### KernelOrderByGQL

```python
@strawberry.input(
    name="KernelOrderBy", 
    description="Added in 26.1.0. Ordering specification for kernels."
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
```

---

## Status Data Types

### KernelStatusErrorInfoGQL

```python
@strawberry.type(
    name="KernelStatusErrorInfo",
    description=(
        "Added in 26.1.0. Error information when a kernel enters an error state. "
        "Contains details about the source and nature of the error."
    ),
)
class KernelStatusErrorInfoGQL:
    src: str = strawberry.field(
        description="Source of the error: 'agent' for agent errors, 'other' for other errors."
    )
    agent_id: str | None = strawberry.field(
        description="ID of the agent where the error occurred. Only present for agent errors in debug mode."
    )
    name: str = strawberry.field(description="Name of the exception class.")
    repr: str = strawberry.field(description="String representation of the exception.")
```

### KernelStatusDataGQL

```python
@strawberry.type(
    name="KernelStatusDataKernel",
    description="Added in 26.1.0. Kernel-specific status data during lifecycle transitions.",
)
class KernelStatusDataGQL:
    exit_code: int | None = strawberry.field(
        description="Exit code of the kernel process. Null if not yet terminated."
    )
```

### KernelSessionStatusDataGQL

```python
@strawberry.type(
    name="KernelSessionStatusData",
    description="Added in 26.1.0. Session-specific status data during kernel lifecycle transitions.",
)
class KernelSessionStatusDataGQL:
    status: str | None = strawberry.field(
        description="Status string of the session (e.g., 'terminating')."
    )
```

### KernelStatusDataContainerGQL

> **Note**: `scheduler` field is **omitted** (see types-to-skip.md)

```python
@strawberry.type(
    name="KernelStatusData",
    description=(
        "Added in 26.1.0. Structured status data containing error or lifecycle information. "
        "The populated fields depend on the kernel's current status and recent state transitions."
    ),
)
class KernelStatusDataContainerGQL:
    error: KernelStatusErrorInfoGQL | None = strawberry.field(
        description="Error information when the kernel is in an error state."
    )
    # scheduler field OMITTED - see types-to-skip.md
    kernel: KernelStatusDataGQL | None = strawberry.field(
        description="Kernel-specific status data during lifecycle transitions."
    )
    session: KernelSessionStatusDataGQL | None = strawberry.field(
        description="Session-specific status data during lifecycle transitions."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> KernelStatusDataContainerGQL:
        error = None
        kernel = None
        session = None

        if not data:
            return cls(error=error, kernel=kernel, session=session)

        # Parse error section
        if "error" in data:
            err = data["error"]
            error = KernelStatusErrorInfoGQL(
                src=err["src"],
                agent_id=err.get("agent_id"),
                name=err["name"],
                repr=err["repr"],
            )

        # Parse kernel section
        if "kernel" in data:
            kernel = KernelStatusDataGQL(exit_code=data["kernel"].get("exit_code"))

        # Parse session section
        if "session" in data:
            session = KernelSessionStatusDataGQL(status=data["session"].get("status"))

        return cls(error=error, kernel=kernel, session=session)
```

---

## Statistics Types

### KernelStatEntryGQL

```python
@strawberry.type(
    name="KernelStatEntry",
    description=(
        "Added in 26.1.0. A single kernel statistic entry with metric key and value. "
        "Common keys include: cpu_util, cpu_used, mem, io_read, io_write, net_rx, net_tx."
    ),
)
class KernelStatEntryGQL:
    key: str = strawberry.field(
        description="Metric key name (e.g., 'cpu_util', 'mem', 'io_read')."
    )
    value: MetricValueGQL = strawberry.field(description="The metric measurement value.")
```

### KernelStatGQL

```python
@strawberry.type(
    name="KernelStat",
    description=(
        "Added in 26.1.0. Collection of kernel resource statistics. "
        "Contains utilization metrics for CPU, memory, I/O, network, and accelerators."
    ),
)
class KernelStatGQL:
    entries: list[KernelStatEntryGQL] = strawberry.field(
        description="List of metric entries for this kernel."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> KernelStatGQL:
        entries = []
        for key, metric_value in data.items():
            if not isinstance(metric_value, dict):
                raise InvalidKernelData(
                    f"Invalid metric value type for key '{key}': "
                    f"expected dict, got {type(metric_value).__name__}"
                )
            stats = None
            stat_keys = ["min", "max", "sum", "avg", "diff", "rate"]
            stat_data = {}
            for stat_key in stat_keys:
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
        return cls(entries=entries)
```

---

## Internal Data Types

### KernelInternalDataGQL

```python
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
        default=None, 
        description="SSH keypair for secure access to the kernel."
    )
    model_definition_path: str | None = strawberry.field(
        default=None, 
        description="Path to the model definition file for inference services."
    )
    runtime_variant: str | None = strawberry.field(
        default=None, 
        description="Runtime variant identifier (e.g., 'custom')."
    )
    sudo_session_enabled: bool | None = strawberry.field(
        default=None, 
        description="Whether sudo is enabled for this session."
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
        default=None, 
        description="Docker credentials for private registry access."
    )
    domain_socket_proxies: list[str] | None = strawberry.field(
        default=None,
        description="List of domain socket paths to proxy into the container.",
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> KernelInternalDataGQL:
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
```

---

## Sub-Info Types

### KernelSessionInfoGQL

```python
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
```

### KernelClusterInfoGQL

```python
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
```

### KernelUserPermissionInfoGQL

> **Note**: `user_uuid` and `group_id` fields are **omitted** (see types-to-defer.md)

```python
@strawberry.type(
    name="KernelUserPermissionInfo",
    description="Added in 26.1.0. User permission and ownership information for a kernel.",
)
class KernelUserPermissionInfoGQL:
    # user_uuid field OMITTED - will be UserNode connection
    # group_id field OMITTED - will be GroupNode connection
    access_key: str = strawberry.field(
        description="The access key used to create this kernel."
    )
    domain_name: str = strawberry.field(
        description="The domain this kernel belongs to."
    )
    uid: int | None = strawberry.field(
        description="The Unix user ID for the kernel's container process."
    )
    main_gid: int | None = strawberry.field(
        description="The primary Unix group ID for the kernel's container process."
    )
    gids: list[int] | None = strawberry.field(
        description="Additional Unix group IDs for the kernel's container process."
    )
```

### KernelDeviceModelInfoGQL

```python
@strawberry.type(
    name="KernelDeviceModelInfo",
    description=(
        "Added in 26.1.0. Information about a specific device model attached to a kernel. "
        "Contains device identification and capacity information."
    ),
)
class KernelDeviceModelInfoGQL:
    device_id: str = strawberry.field(
        description="Unique identifier for the device instance."
    )
    model_name: str = strawberry.field(
        description="Model name of the device (e.g., 'NVIDIA A100', 'AMD MI250')."
    )
    data: JSON = strawberry.field(
        description="Device-specific capacity and capability information."
    )
```

### KernelAttachedDeviceEntryGQL

```python
@strawberry.type(
    name="KernelAttachedDeviceEntry",
    description=(
        "Added in 26.1.0. A collection of devices of a specific type attached to a kernel. "
        "Groups devices by their device type (e.g., 'cuda', 'rocm')."
    ),
)
class KernelAttachedDeviceEntryGQL:
    device_type: str = strawberry.field(
        description="Type of the device (e.g., 'cuda', 'rocm', 'tpu')."
    )
    devices: list[KernelDeviceModelInfoGQL] = strawberry.field(
        description="List of device instances of this type."
    )
```

### KernelAttachedDevicesGQL

```python
@strawberry.type(
    name="KernelAttachedDevices",
    description=(
        "Added in 26.1.0. A collection of all devices attached to a kernel. "
        "Organized by device type, each containing multiple device instances."
    ),
)
class KernelAttachedDevicesGQL:
    entries: list[KernelAttachedDeviceEntryGQL] = strawberry.field(
        description="List of device type entries, each containing attached device instances."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
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
```

### KernelResourceInfoGQL

```python
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
        description="The resource slots currently occupied by this kernel."
    )
    requested_slots: ResourceSlotGQL = strawberry.field(
        description="The resource slots originally requested for this kernel."
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
```

### KernelRuntimeInfoGQL

> **Note**: `vfolder_mounts` field is **omitted** (see types-to-defer.md)

```python
@strawberry.type(
    name="KernelRuntimeInfo",
    description="Added in 26.1.0. Runtime configuration for a kernel.",
)
class KernelRuntimeInfoGQL:
    environ: list[str] | None = strawberry.field(
        description="Environment variables set for this kernel."
    )
    # vfolder_mounts field OMITTED - will be VFolderNode connection
    bootstrap_script: str | None = strawberry.field(
        description="Bootstrap script executed when the kernel starts."
    )
    startup_command: str | None = strawberry.field(
        description="Startup command executed after bootstrap."
    )
```

### KernelNetworkInfoGQL

```python
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
```

### KernelLifecycleInfoGQL

> **Note**: `status_history` field is **omitted** (see types-to-skip.md)

```python
@strawberry.type(
    name="KernelLifecycleInfo",
    description="Added in 26.1.0. Lifecycle and status information for a kernel.",
)
class KernelLifecycleInfoGQL:
    status: KernelStatusGQL = strawberry.field(
        description="Current status of the kernel (e.g., PENDING, RUNNING, TERMINATED)."
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
        description="Structured data about the current status including error or lifecycle information."
    )
    # status_history field OMITTED - see types-to-skip.md
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
```

### KernelMetricsInfoGQL

```python
@strawberry.type(
    name="KernelMetricsInfo",
    description="Added in 26.1.0. Metrics and statistics for a kernel.",
)
class KernelMetricsInfoGQL:
    num_queries: int = strawberry.field(
        description="The number of queries/executions performed by this kernel."
    )
    last_stat: KernelStatGQL | None = strawberry.field(
        description="The last collected statistics for this kernel."
    )
```

### KernelMetadataInfoGQL

```python
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
```

---

## Main Types

### KernelV2GQL

> **Note**: `image` field is **omitted** (see types-to-defer.md)

```python
@strawberry.type(
    name="KernelV2",
    description="Added in 26.1.0. Represents a kernel (compute container) in Backend.AI.",
)
class KernelV2GQL(Node):
    id: NodeID[str]

    session: KernelSessionInfoGQL = strawberry.field(
        description="Information about the session this kernel belongs to."
    )
    user_permission: KernelUserPermissionInfoGQL = strawberry.field(
        description="User permission and ownership information."
    )
    # image field OMITTED - will be ImageNode connection
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
        # Implementation details...
        pass
```

### KernelEdgeGQL

```python
KernelEdgeGQL = Edge[KernelV2GQL]
```

### KernelConnectionV2GQL

```python
@strawberry.type(
    name="KernelConnectionV2",
    description="Added in 26.1.0. Connection type for paginated kernel results.",
)
class KernelConnectionV2GQL(Connection[KernelV2GQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
```

---

## Common Types

These types are defined in `common/types.py` and shared across multiple domains.

### Session Enums

```python
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
```

### VFolder Enums

```python
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
```

### Service Port Enum

```python
ServicePortProtocolGQL = strawberry.enum(
    ServicePortProtocols,
    name="ServicePortProtocol",
    description="Added in 26.1.0. Protocol types for service ports.",
)
```

### ResourceOptsGQL

```python
@strawberry.type(name="ResourceOptsEntry")
class ResourceOptsEntryGQL:
    name: str = strawberry.field(description="The name of this resource option (e.g., 'shmem').")
    value: str = strawberry.field(description="The value for this resource option (e.g., '64m').")

@strawberry.type(name="ResourceOpts")
class ResourceOptsGQL:
    entries: list[ResourceOptsEntryGQL] = strawberry.field(
        description="List of resource option entries."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> ResourceOptsGQL | None:
        if data is None:
            return None
        entries = [ResourceOptsEntryGQL(name=k, value=str(v)) for k, v in data.items()]
        return cls(entries=entries)
```

### ResourceOptsInput

```python
@strawberry.input
class ResourceOptsEntryInput:
    name: str
    value: str

@strawberry.input
class ResourceOptsInput:
    entries: list[ResourceOptsEntryInput]
```

### ServicePortsGQL

```python
@strawberry.type(name="ServicePortEntry")
class ServicePortEntryGQL:
    name: str
    protocol: ServicePortProtocolGQL
    container_ports: list[int]
    host_ports: list[int | None]
    is_inference: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServicePortEntryGQL:
        return cls(
            name=data["name"],
            protocol=ServicePortProtocolGQL(data["protocol"]),
            container_ports=list(data["container_ports"]),
            host_ports=list(data["host_ports"]),
            is_inference=data["is_inference"],
        )

@strawberry.type(name="ServicePorts")
class ServicePortsGQL:
    entries: list[ServicePortEntryGQL]
```

### MetricValueGQL

```python
@strawberry.type(name="MetricStat")
class MetricStatGQL:
    min: str | None
    max: str | None
    sum: str | None
    avg: str | None
    diff: str | None
    rate: str | None

@strawberry.type(name="MetricValue")
class MetricValueGQL:
    current: str
    capacity: str | None
    pct: str | None
    unit_hint: str | None
    stats: MetricStatGQL | None
```

### DotfileInfoGQL & SSHKeypairGQL

```python
@strawberry.type(name="DotfileInfo")
class DotfileInfoGQL:
    path: str
    data: str
    perm: str

@strawberry.type(name="SSHKeypair")
class SSHKeypairGQL:
    public_key: str
    private_key: str
```
