# KernelV2 GQL - 포함할 타입

이 문서는 구현할 타입과 그 필드를 모두 나열한다.

---

## enum

### KernelOrderField
```python
class KernelOrderField(StrEnum):
    CREATED_AT = "created_at"
```

---

## 입력 타입

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

## 하위 정보 타입

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
    used: ResourceSlotGQL | None
```

### KernelResourceInfoGQL

> **필드 이름 변경**: `occupied_slots` → `used`, `requested_slots` → `requested`, `occupied_shares` → `shares`

```python
class KernelResourceInfoGQL:
    agent_id: str | None
    resource_group_name: str | None
    container_id: str | None
    allocation: ResourceAllocationGQL
    shares: ResourceSlotGQL
    resource_opts: ResourceOptsGQL | None
```

### KernelNetworkInfoGQL
```python
class KernelNetworkInfoGQL:
    service_ports: ServicePortsGQL | None
    preopen_ports: list[int] | None
```

### KernelLifecycleInfoGQL

> **참고**: `status_history`, `status_info`, `status_data`, `status_changed` 는 **뺀다**(types-to-skip.md 참고)

```python
class KernelLifecycleInfoGQL:
    status: KernelStatus
    result: SessionResult
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
```

---

## 주요 타입

### KernelV2GQL

> **참고**: 아래 Node 참조는 모두 **미룬다**(types-to-defer.md 참고)

```python
class KernelV2GQL(Node):
    id: NodeID[str]

    # Node references (deferred)
    session_node: SessionNode | None
    user_node: UserNode | None
    keypair_node: KeypairNode | None
    domain_node: DomainNode | None
    project_node: GroupNode | None
    agent_node: AgentNode | None
    resource_group_node: ResourceGroupNode | None
    vfolder_nodes: VFolderConnection

    # Inlined fields (from single-element types)
    startup_command: str | None

    # Sub-info types
    session: KernelSessionInfoGQL
    user: KernelUserInfoGQL
    network: KernelNetworkInfoGQL
    cluster: KernelClusterInfoGQL
    resource: KernelResourceInfoGQL
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

## 공통 타입

### Service Port 타입
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

### Resource Options 타입

> **참고**: `ResourceOptsEntryGQL`, `ResourceOptsGQL`, `ResourceOptsEntryInput`, `ResourceOptsInput` 는 `deployment/types/revision.py` 에 이미 있다
