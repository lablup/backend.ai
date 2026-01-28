# KernelV2 GQL - Types to Include

This document lists all types to be implemented with their fields.

---

## Enums

### KernelOrderField
```python
class KernelOrderField(StrEnum):
    CREATED_AT = "created_at"
```

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
    id: UUIDFilter | None
    status: KernelStatusFilterGQL | None
    session_id: UUIDFilter | None
```

### KernelOrderByGQL
```python
class KernelOrderByGQL:
    field: KernelOrderField
    direction: OrderDirection
```

---

## Sub-Info Types

### KernelImageInfoGQL

```python
class KernelImageInfoGQL:
    image_id: uuid.UUID | None
```

### KernelSessionInfoGQL

```python
class KernelSessionInfoGQL:
    session_id: uuid.UUID
    creation_id: str | None
    name: str | None
    session_type: SessionTypes
```

### KernelClusterInfoGQL
```python
class KernelClusterInfoGQL:
    cluster_role: str
    cluster_idx: int
    local_rank: int
    cluster_hostname: str
```

### KernelUserInfoGQL

```python
class KernelUserInfoGQL:
    user_id: uuid.UUID | None
    access_key: str | None
    domain_name: str | None
    group_id: uuid.UUID | None
```

### ResourceAllocationGQL
```python
class ResourceAllocationGQL:
    requested: ResourceSlotGQL
    used: ResourceSlotGQL
```

### KernelResourceInfoGQL

> **Field Renames**: `occupied_slots` → `used`, `requested_slots` → `requested`, `occupied_shares` → `shares`

```python
class KernelResourceInfoGQL:
    agent_id: str | None
    resource_group_name: str | None
    container_id: str | None
    allocation: ResourceAllocationGQL
    shares: ResourceSlotGQL
    resource_opts: ResourceOptsGQL | None
```

### KernelRuntimeInfoGQL

```python
class KernelRuntimeInfoGQL:
    startup_command: str | None
```

### KernelNetworkInfoGQL
```python
class KernelNetworkInfoGQL:
    service_ports: ServicePortsGQL | None
    preopen_ports: list[int] | None
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
```

---

## Main Types

### KernelV2GQL

> **Note**: All node references below are **deferred** (see types-to-defer.md)

```python
class KernelV2GQL(Node):
    id: NodeID[str]

    # Node references (deferred)
    image_node: ImageNode | None
    session_node: SessionNode | None
    user_node: UserNode | None
    keypair_node: KeypairNode | None
    domain_node: DomainNode | None
    project_node: GroupNode | None
    agent_node: AgentNode | None
    resource_group_node: ResourceGroupNode | None
    vfolder_nodes: list[VFolderNode] | None

    # Sub-info types
    image: KernelImageInfoGQL
    session: KernelSessionInfoGQL
    user: KernelUserInfoGQL
    network: KernelNetworkInfoGQL
    cluster: KernelClusterInfoGQL
    resource: KernelResourceInfoGQL
    runtime: KernelRuntimeInfoGQL
    lifecycle: KernelLifecycleInfoGQL
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

