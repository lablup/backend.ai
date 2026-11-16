<!-- context-for-ai
type: detail-doc
parent: BEP-1051 (Kata Containers Agent Backend)
scope: Manager and scheduler changes for Kata backend selection and resource accounting
depends-on: [kata-agent-backend.md, vfio-accelerator-plugin.md]
key-decisions:
  - Backend selection via homogeneous scaling groups
  - VM overhead deducted from agent available_slots at registration
  - backend column added to AgentRow (default "docker")
-->
# BEP-1051: 스케줄러 통합

## 요약

agent 의 backend 종류를 추적하고, 자원 그룹 배정으로 세션을 Kata agent 로 라우팅하며, VM 별 메모리 오버헤드를 자원 스케줄링에 반영하도록 manager 와 scheduler 를 변경한다. 모든 변경은 추가형이며 기존 Docker 스케줄링 동작은 그대로다.

## 현재 설계

### agent 등록

agent 는 heartbeat event 로 등록한다. manager 가 `AgentRow` 를 생성하거나 변경한다(`src/ai/backend/manager/models/agent/row.py:62`).

```python
class AgentRow(Base):
    id: Mapped[str]                    # Agent ID
    status: Mapped[AgentStatus]
    region: Mapped[str]
    scaling_group: Mapped[str]         # FK to scaling_groups.name
    available_slots: Mapped[ResourceSlot]   # Total capacity
    occupied_slots: Mapped[ResourceSlot]    # Currently used
    architecture: Mapped[str]          # e.g., "x86_64"
    compute_plugins: Mapped[dict]      # Loaded plugin metadata
    # No backend type field exists
```

### agent 선택

scheduler 는 `AgentSelector` 구현으로 agent 를 선택한다. `AgentInfo`(`src/ai/backend/manager/sokovan/scheduler/provisioner/selectors/selector.py`)는 다음과 같다.

```python
@dataclass
class AgentInfo:
    id: AgentId
    available_slots: ResourceSlot
    occupied_slots: ResourceSlot
    architecture: str
    # No backend type field
```

selector 는 대상 자원 그룹 안에서 `available_slots >= requested_slots` 조건으로 필터링한다.

### 자원 그룹

`ScalingGroupOpts`(`src/ai/backend/manager/models/scaling_group/row.py`)가 다음을 구성한다.

```python
class ScalingGroupOpts:
    allowed_session_types: list[SessionTypes]
    agent_selection_strategy: AgentSelectionStrategy  # DISPERSED, CONCENTRATED, etc.
    # No backend preference
```

세션은 자원 그룹에 배정되고, scheduler 가 그 그룹 안에서 agent 를 선택한다.

## 제안 설계

### agent backend 추적

`AgentRow` 에 `backend` column 을 추가한다.

```python
class AgentRow(Base):
    # ... existing columns ...
    backend: Mapped[str] = mapped_column(
        "backend",
        sa.String(length=16),
        nullable=False,
        server_default="docker",
        default="docker",
    )
```

**Alembic migration:**

```python
def upgrade():
    op.add_column(
        "agents",
        sa.Column(
            "backend",
            sa.String(length=16),
            nullable=False,
            server_default="docker",
        ),
    )
```

비파괴 변경이다. 기존 agent 는 모두 server default 로 `backend="docker"` 값을 받는다.

### agent heartbeat 확장

agent heartbeat payload 에는 이미 메타데이터(architecture, version, compute_plugins)가 들어 있다. `backend` 를 추가한다.

```python
# In agent heartbeat handler (manager side)
async def handle_agent_heartbeat(self, agent_id, heartbeat_data):
    backend = heartbeat_data.get("backend", "docker")  # backward-compatible default
    await self._update_agent_row(agent_id, backend=backend, ...)
```

agent 측 heartbeat 에는 `AgentBackend.value` 가 포함된다.

```python
# In AbstractAgent heartbeat sender
heartbeat_data = {
    "backend": self.local_config.agent_common.backend.value,
    "architecture": platform.machine(),
    # ... existing fields ...
}
```

### 동종 자원 그룹

권장 방식에서는 자원 그룹마다 backend 종류가 하나인 agent 만 둔다. `ScalingGroupRow` 에 column 을 추가하지 않는다.

**동종 그룹을 고르는 이유:**

1. **단순함**: 기존 스케줄링 흐름을 변경하지 않는다. 세션은 자원 그룹을 대상으로 하고 scheduler 가 그 안에서 agent 를 선택한다. backend 종류는 그룹에서 드러난다.
2. **운영 명확성**: 운영자는 어느 그룹이 Kata 를 실행하고 어느 그룹이 Docker 를 실행하는지 정확히 안다.
3. **agent 필터링 변경 없음**: `AgentSelector` 에 backend 인식 필터가 필요 없다.
4. **자원 의미 일치**: `cuda.device` 는 두 backend 에서 같은 의미(GPU 하나)이지만 연결 방식은 다르다. backend 를 그룹으로 나누면 섞이지 않는다.

**배포 예시:**

```
Scaling Groups:
├── default          → DockerAgent instances (general compute)
├── gpu-docker       → DockerAgent instances with GPUs (NVIDIA runtime)
└── gpu-kata         → KataAgent instances with GPUs (VFIO + CoCo, always confidential)
```

사용자와 project 는 이전처럼 자원 그룹에 배정된다. `gpu-kata` 를 고르면 세션이 Kata agent 로 라우팅된다.

### VM 메모리 오버헤드 계산

Kata VM 은 hypervisor 프로세스, guest 커널, kata-agent 를 위해 호스트 메모리를 소비한다. 이 오버헤드를 스케줄 가능한 자원에 반영해야 한다.

**방식: agent 측 차감**

Kata agent 가 등록 시점에 `available_slots.mem` 에서 VM 오버헤드를 차감한다.

```python
# In KataAgent.scan_available_resources()
async def scan_available_resources(self, compute_device_types):
    base_slots = await super().scan_available_resources(compute_device_types)

    kata_config = self.local_config.kata
    # Reserve memory for max concurrent VMs
    # Each session = 1 VM, so max_sessions * overhead
    max_concurrent = self._estimate_max_concurrent_sessions(base_slots)
    overhead_bytes = max_concurrent * kata_config.vm_overhead_mb * 1024 * 1024

    adjusted_mem = base_slots.get(SlotName("mem"), Decimal(0)) - Decimal(overhead_bytes)
    if adjusted_mem < 0:
        adjusted_mem = Decimal(0)

    result = dict(base_slots)
    result[SlotName("mem")] = adjusted_mem
    return result
```

**agent 측 차감을 고르는 이유:**

1. scheduler 가 정확한 `available_slots` 를 본다. 별도 예외 처리가 필요 없다
2. VM 오버헤드는 세션이 아니라 agent 구성의 속성이다
3. 오버헤드 양은 `kata.vm-overhead-mb` 로 구성한다
4. 사용자나 API 에 보이는 `ResourceSlot` 의미는 변경하지 않는다

### 자원 슬롯 호환성

| Slot 이름 | Docker (CUDAPlugin) | Kata (CUDAVFIOPlugin) | scheduler 관점 |
|-----------|---------------------|------------------------|----------------|
| `cpu` | cgroup CPU share | VM vCPU 할당 | 같다 |
| `mem` | cgroup 메모리 한도 | VM 메모리(오버헤드 차감) | 같다 |
| `cuda.device` | NVIDIA Container Toolkit | VFIO passthrough | 같다 |
| `cuda.shares` | 분할 (hook 라이브러리) | **사용할 수 없음** | Kata agent 에서는 해당 없음 |

scheduler 는 backend 와 무관하게 `cuda.device` 를 같게 다룬다. CUDAVFIOPlugin 이 `cuda.shares` 를 정의하지 않으므로 Kata agent 의 `available_slots` 에 나타나지 않는다.

### AgentMeta / AgentInfo 변경

scheduler 가 사용하는 데이터 전달 객체에 `backend` 를 추가한다.

```python
# src/ai/backend/manager/repositories/scheduler/types/agent.py
@dataclass
class AgentMeta:
    id: AgentId
    addr: str
    architecture: str
    available_slots: ResourceSlot
    scaling_group: str
    backend: str = "docker"  # NEW, backward-compatible default

# src/ai/backend/manager/sokovan/scheduler/provisioner/selectors/selector.py
@dataclass
class AgentInfo:
    id: AgentId
    available_slots: ResourceSlot
    occupied_slots: ResourceSlot
    architecture: str
    backend: str = "docker"  # NEW
```

동종 자원 그룹 모델에서 이 field 는 참고 정보이며 selector 가 backend 로 필터링할 필요는 없다. 다음 용도로 유용하다.

- 관리자 가시성 (GQL 조회: Kata agent 전체 보기)
- 향후 혼합 그룹 지원 (필요해지면)
- 모니터링과 dashboard

### GraphQL 노출

`Agent` GQL type 에 `backend` 를 추가한다.

```python
@strawberry.type
class AgentNode:
    # ... existing fields ...
    backend: str  # "docker" | "kubernetes" | "kata"
```

admin UI 에서 어느 agent 가 어느 backend 를 사용하는지 표시할 수 있다.

## 인터페이스 / API

| 변경 | 위치 | 종류 |
|--------|----------|------|
| `AgentRow.backend` column | `src/ai/backend/manager/models/agent/row.py` | DB schema (Alembic) |
| `AgentMeta.backend` field | `src/ai/backend/manager/repositories/scheduler/types/agent.py` | dataclass |
| `AgentInfo.backend` field | `src/ai/backend/manager/sokovan/scheduler/provisioner/selectors/selector.py` | dataclass |
| heartbeat `backend` field | agent heartbeat sender + manager heartbeat handler | protocol |
| `AgentNode.backend` | GQL Agent type | API |

## 구현 참고 사항

- Alembic migration 은 비파괴 변경이다. `server_default="docker"` 를 가진 column 을 추가한다
- agent heartbeat 하위 호환: heartbeat 에 `backend` 가 없으면 `"docker"` 로 기본값을 준다
- `create_kernel` / `destroy_kernel` 의 manager-agent RPC protocol 은 변경하지 않는다. payload 는 같고 agent 측 처리만 다르다
- `AgentRow` 의 `compute_plugins` JSONB column 은 이미 어떤 plugin(`cuda` 또는 `cuda_vfio`)이 적재됐는지 담고 있어 backend 정보를 간접적으로 준다. 명시적 `backend` column 이 이를 명확히 한다
