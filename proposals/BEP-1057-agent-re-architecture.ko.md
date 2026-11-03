# Agent 재설계

## 관련 이슈

- Epic **BA-6684**, 이 BEP **BA-6686**
- Kernel lifecycle (참조만 하고 확장하지 않음): **[BEP-1002](BEP-1002-agent-architecture.md)** (runner 모델), **BA-6074**/BEP-1687 (실행)
- 인접: BEP-1024 (RPC pool), BEP-1028 (K8s bridge), BEP-1044 (device split), BEP-1051 (Kata)

## 1. 목표

Agent 를 세 단계로 재설계한다.

| 단계 | 작업 | 완료 조건 |
|-------|------|-----------|
| **1. backend 추상화** | backend 를 god class 에서 분리한다. generic parameter 대신 단일 `ComputeBackend` 인터페이스를 둔다. **container 뿐 아니라 VM 도 범위**이므로 이름에 "container" 를 넣지 않는다. service 분해로 런타임과 자원 상태를 **Manager event 로** 노출한다. | 외부 RPC 계약 불변(동작 보존). 가시성 egress 구축 |
| **2. controller 와 worker 분리** | 네트워크 경계를 따라 controller(**네트워크 처리를 소유**)와 worker(backend 실행)로 나눈다. controller 진입점은 Callosum RPC 가 아니라 **HTTP 엔드포인트**다. | 네트워크 소유가 controller 로 이동. Manager↔Agent 는 HTTP |
| **3. containerd 이관** | `ComputeBackend` 의 containerd 구현을 추가한다. **인터페이스는 그대로**지만 네트워크가 Swarm 을 사용할 수 없어 non-Swarm 네트워크 driver 가 필요하다. | containerd backend 와 non-Swarm overlay 동작 |

**범위 경계**: 단일 kernel 의 create→terminate 안쪽은 BEP-1002/BA-6074 에 속하고, Agent 전체를 어떻게 조립하고 계층으로 나누고 분리하는지는 이 BEP 가 다룬다. BEP-1002 의 **runner 는 black box 로 소비한다**.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 있음 / ➕ 추가** 로 적는다.

### 2.1 Agent core 와 backend 추상화 (1단계)

| | 항목 |
|---|---|
| ✅ | `AbstractAgent[KernelType, CtxType](aobject)`. `agent.py` 약 3,700 줄이고, 클래스 하나가 30여 개 field 와 100여 개 method 를 가진다 |
| ✅ | Docker/K8s/Dummy 가 **generic parameter** 로 전체 표면을 다시 구현한다 (`docker/agent.py` 약 2,300 줄) |
| ✅ | 목표 구조의 seed 가 있다: `stage/`, `kernel_registry/`, `tasks/`, `health/` |
| ➕ | generic 을 단일 `ComputeBackend` ABC(container/VM 공통)로 대체하고 조립 시점에 고른다 (3.a) |
| ➕ | method 묶음을 `KernelService`/`ImageService`/`ResourceService`/`StatsService`/`LifecycleService` 로 추출하고 Agent 를 얇은 coordinator 로 만든다 (3.a) |
| ➕ | composer 가 그래프 전체를 조립한다. `infrastructure/composer.py` 의 `aiodocker.Docker` 하드코딩을 backend 선택으로 교체하고 `__ainit__` 을 없앤다 (3.a) |

### 2.2 가시성 (Manager egress, 1단계)

| | 항목 |
|---|---|
| ✅ | AGENTS.md 가 "Agent→Manager 는 event system 만 사용한다" 고 선언한다. agent heartbeat 가 있다 |
| ✅ | 런타임과 자원 상태가 `AbstractAgent` field 에 흩어져 있다. agent heartbeat 밖에서는 관측할 수 없다 |
| ➕ | `ObservabilityProducer` 를 단일 egress 로 둔다. 자원 할당, 사용량, 런타임 상태(container/VM 공통)를 Manager event 로 발행한다 (3.a) |

### 2.3 자원 lifecycle 과 복구 (1단계, 공통)

instance 생성 시 잡는 부수 자원(**획득/해제**: network attach, port 예약, `alloc_map` 할당, scratch 등)과 **agent 재시작 시 복구**를 다룬다.

| | 항목 |
|---|---|
| ✅ | 복구가 `AbstractAgent` 에 모여 있다: `_load_kernel_registry_from_recovery`(**pickle 기반**), `reconstruct_resource_usage()`(container 에서 alloc 재구성), `_restore_ports()`, dangling 정리(`registered - alive`), `OrphanKernelCleanupObserver` |
| ✅ | BEP-1002 가 이것을 **구조적 teardown 과 label 기반 dangling 복구**로 대체하려 한다(pickle 제거는 BA-6074 담당이다) |
| ➕ | `ComputeBackend` 는 instance 만 맡는다. **자원(network/port/alloc)은 대칭적인 획득/해제를 가진 별도 manager 가 맡는다**. 순서는 BEP-1002 의 runner 가 정한다 (3.a) |
| ➕ | 재시작하면 각 manager 가 kernel id 로 `list_instances()` 를 맞춰 독립적으로 복구한다. `LifecycleService` 가 orphan/dangling 을 Manager event 로 보고한다 (3.d) |

### 2.4 진입, RPC, 네트워크 토폴로지 (2단계)

| | 항목 |
|---|---|
| ✅ | Manager↔Agent 는 **Callosum RPC** 다(`AgentRPCServer(aobject)` 약 1,800 줄). business logic 이 handler 안에 있고 **registry 두 개가 공존한다**(V1+V2). RPC connection pooling 은 BEP-1024 다 |
| ✅ | 프로세스 하나가 네트워크와 workload 실행을 함께 맡는다 |
| ✅ | 네트워크는 **이미 plugin** 이다(`agent/plugin/network.py` 와 manager `OverlayNetworkPlugin`). 다만 orchestration 은 Agent 안에 들어 있다 |
| ➕ | controller(**HTTP 엔드포인트** ingress, routing, 네트워크 소유, 단일 egress)와 worker(backend 실행)로 나눈다. RPC 진입점을 HTTP 로 교체하면 Manager 의 agent client 가 RPC 에서 HTTP 로 이전한다 (3.b) |

### 2.5 네트워크 driver (3단계)

| | 항목 |
|---|---|
| ✅ | multi-node cluster-session overlay 는 **Docker Swarm 기반**이다 (`swarm-manager/host`, `swarm-worker/token`, `docker_gwbridge`) |
| ✅ | 네트워크 설정 일부는 `stage/kernel_lifecycle/docker/network.py` 에 있다(BA-6074 영역) |
| ➕ | containerd backend 에서는 Swarm overlay 를 대체할 **non-Swarm cross-node 네트워크** driver(CNI 등)가 필요하다. 기존 네트워크 plugin 인터페이스 뒤에 새 구현을 둔다 (3.c) |

## 3. 구현 설계

### (a) 1단계: backend 추상화, service 분해, 가시성

- service 호출은 가벼운 `service.method(args)` 다(Manager 식 Action/ActionResult 는 없다. Agent 에 processor 계층이 없다).
- `KernelService` 는 BEP-1002 의 `runner` 만 구동한다(black box). runner 계약을 안정적으로 유지하면 BA-6074 를 병행할 수 있다.
- **이름**: "container" 에 묶지 않고 `ComputeBackend`(가칭)로 둔다. **네트워크는 backend 인터페이스에서 제외한다**. 2단계에서 controller 가 맡으므로 backend 는 instance lifecycle 만 책임진다.

```python
class ComputeBackend(ABC):  # name is an Open Question — container/VM common
    async def create_instance(self, spec: InstanceSpec) -> InstanceHandle: ...
    async def destroy_instance(self, handle: InstanceHandle) -> None: ...  # idempotent
    async def inspect_instance(self, handle: InstanceHandle) -> InstanceInfo: ...
    async def list_instances(self) -> Sequence[InstanceInfo]: ...  # self-described by labels
    async def collect_stats(self, handle: InstanceHandle) -> InstanceStat: ...
```

- 구현: `docker/`, `kubernetes/`, `dummy/`, (향후) `containerd/`, `vm/`. Dummy 는 AGENTS.md 규칙에 따라 같은 시점에 함께 갱신한다.
- **backend 는 instance 생성과 삭제만 책임진다**. network, port, `alloc_map`, scratch 는 **별도 manager**(ResourceService, network plugin)가 맡는다. backend 가 자원을 내부에서 관리하지 않는다.
- 다만 instance 에 **kernel id 상관 키**를 찍어, 재시작할 때 별도 manager 가 실행 중인 instance 를 맞출 수 있게 한다. `destroy_instance` 는 멱등이다(handle 만으로 orphan 정리에서 호출할 수 있다).

**자원 획득/해제 인터페이스**: 1단계는 backend 옆에 다른 자원 manager 도 주입 service 로 정리한다. 새 공통 인터페이스는 도입하지 않고 기존 대칭 primitive 를 그대로 사용한다.

| 자원 | 획득 / 해제 | manager |
|----------|-------------------|---------|
| instance | `create_instance` / `destroy_instance` | `ComputeBackend` |
| alloc | `alloc_map.allocate` / `free` | `ResourceService` |
| port | allocate / free | `PortPool` |
| network | `join_network` / `leave_network` | `NetworkPlugin` (2단계에서는 controller 소유) |

순서대로 획득하고, 종료 시 역순으로 해제하며, 실패하면 rollback 하는 일은 BEP-1002 의 `Provisioner`/`Stage`(setup/teardown)가 조정한다. `release` 는 멱등이라 복구 중에 다시 호출해도 안전하다.

### (b) 2단계: controller 와 worker 분리 (HTTP 엔드포인트, 네트워크는 controller 에)

```
Manager ──HTTP(ingress) / events(egress)── Controller (HTTP endpoint · networking · worker routing · single egress)
                                                │ controller↔worker channel
                                                ▼
                                            Worker 1..N (runs services → ComputeBackend)
```

- controller 진입점을 **Callosum RPC 에서 HTTP 엔드포인트**(REST)로 전환한다. 1단계의 얇은 handler 는 `service.method(args)` 위임으로 HTTP route 뒤로 옮기고 V1/V2 RPC registry 는 없앤다.
- HTTP 는 Manager→Agent 방향뿐이다. **Agent→Manager egress 는 event system 에 그대로 둔다**(AGENTS.md 규칙).
- **네트워크 소유가 controller 로 이동한다**. controller 가 기존 network plugin orchestration 을 호출하고, worker 는 backend instance 만 다룬다.
- Manager 의 agent client 가 RPC 에서 HTTP 로 바뀌므로 **Manager 쪽 변경이 필요하다**. BEP-1024 의 RPC pooling 은 HTTP connection 처리로 대체하거나 다시 검토한다.

### (c) 3단계: containerd 이관

- `ComputeBackend` 의 containerd 구현을 추가한다. **인터페이스는 바뀌지 않는다**(3.a 덕분이다).
- containerd 에는 Swarm 이 없으므로 **overlay 네트워크를 controller 가 맡는 non-Swarm driver 로 교체한다**. 2단계에서 네트워크를 이미 controller 로 옮겼으므로 교체 범위는 controller 와 network plugin 안이다(순서 의존).

### (d) 재시작 복구와 teardown 경계 (공통)

종료와 재시작 시 자원을 **누수 없이 해제하고 복구해야 한다**. 획득/해제 manager 는 (a)에 있고, 순서와 구조적 teardown 은 BEP-1002 의 runner 가 맡으며, 이 BEP 는 복구를 다룬다.

| 관심사 | 담당 | 방식 |
|---------|-------|-----|
| 순서와 구조적 teardown | **BEP-1002 runner** | 각 자원을 runner 에 등록한다. 종료 시 cancel 로 전체를 역순 해제한다(정리가 흩어지지 않는다) |
| 재시작 복구 | `ResourceService`, `LifecycleService` (이 BEP) | 각 manager 가 kernel id 로 `list_instances()` 를 맞춰 **독립적으로** 복구한다. alloc 은 device binding 에서(`reconstruct_resource_usage`), port 는 port binding 에서(`_restore_ports`) 복구한다. dangling 은 Manager 에 **event 로** 보고한다(pickle 과 `OrphanKernelCleanupObserver` 를 대체한다) |

### (e) 재작성 workflow (동작 보존)

| 단계 | 내용 | 게이트 |
|------|---------|------|
| 0단계 | 현재 RPC 동작에 대한 characterization test (BEP-1002 1단계, 아직 하지 않음) | 이후 모든 단계의 동등성 기준 |
| 1단계 | composition root → `ComputeBackend` → service 추출(flag) → 가시성 egress → 얇은 진입점과 registry 통합 | 단계마다 동등성 확인, RPC 계약 불변 |
| 2단계 | controller 와 worker 분리 + 네트워크 소유 이동 | Manager 쪽 최소 변경 |
| 3단계 | containerd backend + non-Swarm 네트워크 | 기능 동등성 |

## 4. 결정 요약

| 결정 | 내용 |
|----------|---------|
| BEP 형태 | 새 BEP-1057. BEP-1002 를 runner 모델로 인용한다 |
| backend 범위 | `ComputeBackend`(가칭)는 instance 생성과 삭제만 한다. container/VM 공통이다. 네트워크와 자원은 제외한다 |
| 단계 | 1) backend 추상화 → 2) controller 와 worker 분리(+네트워크, HTTP 엔드포인트) → 3) containerd 이관 |
| 전송 | controller 진입점은 HTTP(REST)다. HTTP 는 Manager→Agent 방향뿐이고 egress 는 event 로 유지한다. BEP-1024 pooling 은 대체한다 |
| 호출 규약 | 가벼운 `service.method(args)` |
| 안전장치 | 0단계 characterization test + feature flag 이중 실행. RPC 계약 불변 |
| 자원 해제 | 자원별 대칭 획득/해제 manager(alloc_map, PortPool, NetworkPlugin, ComputeBackend). 순서와 teardown 은 BEP-1002 runner 가 맡는다 |
| 경계 | kernel stage 와 자원 teardown 은 BEP-1002/BA-6074, device split 은 BEP-1044 |

## 5. 열린 질문

- `ComputeBackend` 이름과 추상화 수준. container/VM 공통 최소와 backend별 확장 중 어느 쪽인지. Kata(VM 안의 container)와 완전한 VM 을 구분한다.
- backend 와 network 를 진입점 plugin 으로 둘지 compile 시점 구현으로 둘지 (BEP-1051/1028).
- 2단계의 네트워크 소유와 BA-6074 의 네트워크 stage 경계.
- 3단계의 non-Swarm cross-node overlay 방식(CNI 대 자체 구현).
- 자원 teardown 실행의 담당. BEP-1002 runner 와 이 BEP 의 manager 제공 중 어느 쪽인지.
- `ImageService` 에서 backend별 image API(containerd CRI)를 어디까지 다루는지.
- 가시성 event schema. agent heartbeat 확장과 새 타입 중 어느 쪽인지, container/VM 공통 범위.

## 6. 참고

- [BEP-1002](BEP-1002-agent-architecture.md): kernel runner, Provisioner, Stage 모델 (상위)
- [BEP-1024](BEP-1024-agent-rpc-connection-pooling.md), [BEP-1028](BEP-1028-kubernetes-bridge.md), [BEP-1044](BEP-1044-multi-agent-device-split.md), [BEP-1051](BEP-1051-kata-containers-agent.md)
- `src/ai/backend/agent/plugin/network.py`, manager `OverlayNetworkPlugin`: 기존 네트워크 plugin (Swarm overlay)
- `src/ai/backend/agent/AGENTS.md`: 선언한 목표 규칙 (`stage/`, `health/`, event 전용 egress, `alloc_map`)
