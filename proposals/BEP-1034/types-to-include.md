# KernelV2 GQL - Types to Include

This document lists all types to be implemented with their fields.

---

## Input Types

### KernelStatusFilterGQL
```python
class KernelStatusFilterGQL:
    in_: list[KernelStatus] | None
    not_in: list[KernelStatus] | None
```

### KernelFilterGQL
```python
class KernelFilterGQL:
    id: UUID | None
    status: KernelStatusFilterGQL | None
    session_id: UUID | None
```

### KernelOrderByGQL
```python
class KernelOrderByGQL:
    field: KernelOrderField
    direction: OrderDirection
```

---

## Status Data Types

### KernelStatusErrorInfoGQL
```python
class KernelStatusErrorInfoGQL:
    src: str
    agent_id: uuid.UUID | None
    agent: AgentNode | None
    name: str
    repr: str
```

### KernelStatusDataGQL
```python
class KernelStatusDataGQL:
    exit_code: int | None
```

### KernelSessionStatusDataGQL
```python
class KernelSessionStatusDataGQL:
    status: str | None
```

### KernelStatusDataContainerGQL

> **Note**: `scheduler` field is **omitted** (see types-to-skip.md)

```python
class KernelStatusDataContainerGQL:
    error: KernelStatusErrorInfoGQL | None
    kernel: KernelStatusDataGQL | None
    session: KernelSessionStatusDataGQL | None
```

---

## Internal Data Types

### KernelInternalDataGQL
```python
class KernelInternalDataGQL:
    dotfiles: list[DotfileInfoGQL] | None
    ssh_keypair: SSHKeypairGQL | None
    model_definition_path: str | None
    runtime_variant: str | None
    sudo_session_enabled: bool | None
    block_service_ports: bool | None
    prevent_vfolder_mounts: bool | None
    docker_credentials: JSON | None
    domain_socket_proxies: list[str] | None
```

---

## Sub-Info Types

### KernelSessionInfoGQL

> **Note**: `session: SessionNode` is **deferred** (see types-to-defer.md)

```python
class KernelSessionInfoGQL:
    session_id: uuid.UUID | None
    creation_id: str | None
    name: str | None
    session_type: SessionTypes
```

### KernelClusterInfoGQL
```python
class KernelClusterInfoGQL:
    cluster_mode: str
    cluster_size: int
    cluster_role: str
    cluster_idx: int
    local_rank: int
    cluster_hostname: str
```

### KernelUserPermissionInfoGQL

> **Note**: `user: UserNode`, `keypair: KeypairNode`, `domain: DomainNode`, `project: GroupNode` are **deferred** (see types-to-defer.md)

```python
class KernelUserPermissionInfoGQL:
    user_id: uuid.UUID | None
    access_key: str | None
    domain_name: str | None
    group_id: uuid.UUID | None
    uid: int | None
    main_gid: int | None
    gids: list[int] | None
```

### KernelDeviceModelInfoGQL
```python
class KernelDeviceModelInfoGQL:
    device_id: str
    model_name: str
    data: JSON
```

### KernelAttachedDeviceEntryGQL
```python
class KernelAttachedDeviceEntryGQL:
    device_type: str
    devices: list[KernelDeviceModelInfoGQL]
```

### KernelAttachedDevicesGQL
```python
class KernelAttachedDevicesGQL:
    entries: list[KernelAttachedDeviceEntryGQL]
```

### KernelResourceInfoGQL

> **Note**: `scaling_group: ScalingGroupNode` is **deferred** (see types-to-defer.md)
>
> **Field Renames**: `occupied_slots` → `used`, `requested_slots` → `requested`, `occupied_shares` → `shares`

```python
class KernelResourceInfoGQL:
    agent_id: uuid.UUID | None
    agent: AgentNode | None
    scaling_group_name: str | None
    container_id: str | None
    used: ResourceSlotGQL
    requested: ResourceSlotGQL
    shares: ResourceSlotGQL
    attached_devices: KernelAttachedDevicesGQL | None
    resource_opts: ResourceOptsGQL | None
```

### KernelRuntimeInfoGQL

> **Note**: `vfolders: list[VFolderNode]` is **deferred** (see types-to-defer.md)

```python
class KernelRuntimeInfoGQL:
    vfolder_ids: list[uuid.UUID] | None
    environ: EnvironmentVariables | None
    bootstrap_script: str | None
    startup_command: str | None
```

### KernelNetworkInfoGQL
```python
class KernelNetworkInfoGQL:
    kernel_host: str | None
    repl_in_port: int
    repl_out_port: int
    service_ports: ServicePortsGQL | None
    preopen_ports: list[int] | None
    use_host_network: bool
```

### KernelLifecycleInfoGQL

> **Note**: `status_history`, `status_info`, `status_data`, `status_changed` are **omitted** (see types-to-skip.md)

```python
class KernelLifecycleInfoGQL:
    status: KernelStatus
    result: SessionResult
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
    last_seen: datetime | None
```

### KernelMetricsInfoGQL

> **Note**: `last_stat` is **removed**

```python
class KernelMetricsInfoGQL:
    num_queries: int
```

### KernelMetadataInfoGQL
```python
class KernelMetadataInfoGQL:
    callback_url: str | None
    internal_data: KernelInternalDataGQL | None
```

---

## Main Types

### KernelV2GQL

> **Note**: `image: ImageNode` is **deferred** (see types-to-defer.md)

```python
class KernelV2GQL(Node):
    id: NodeID[str]
    image_id: str | None
    session: KernelSessionInfoGQL
    user_permission: KernelUserPermissionInfoGQL
    network: KernelNetworkInfoGQL
    cluster: KernelClusterInfoGQL
    resource: KernelResourceInfoGQL
    runtime: KernelRuntimeInfoGQL
    lifecycle: KernelLifecycleInfoGQL
    metrics: KernelMetricsInfoGQL
    metadata: KernelMetadataInfoGQL
```

### KernelEdgeGQL
```python
KernelEdgeGQL = Edge[KernelV2GQL]
```

### KernelConnectionV2GQL
```python
class KernelConnectionV2GQL(Connection[KernelV2GQL]):
    count: int
```

---

## Common Types

### Service Port Types
```python
class ServicePortEntryGQL:
    name: str
    protocol: ServicePortProtocol
    container_ports: list[int]
    host_ports: list[int | None]
    is_inference: bool

class ServicePortsGQL:
    entries: list[ServicePortEntryGQL]
```

### Resource Options Types

> **Note**: `ResourceOptsEntryGQL`, `ResourceOptsGQL`, `ResourceOptsEntryInput`, `ResourceOptsInput` already exist in `deployment/types/revision.py`

### Internal Data Types
```python
class DotfileInfoGQL:
    path: str
    data: str
    perm: str

class SSHKeypairGQL:
    public_key: str
    private_key: str
```
