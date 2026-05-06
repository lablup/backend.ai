# Backend.AI containerd 컨테이너 네트워킹 전략

## 1. 배경

Backend.AI containerd 기반 agent에서 컨테이너는 **K8s Pod가 아닌 containerd 워크로드로 직접 생성**된다. 이 문서는 K8s 정책 enforcement가 아니라 **통신 편의성, 성능, 격리**를 만족하는 네트워킹 구조를 정리한다.

### 1.1. baseline

기존 BAI 다중 노드 통신은 Docker Swarm overlay (vxlan + libnetwork) 기반이었고, 10G NIC 환경에서 측정 시 **line rate의 30-40% (약 3-4 Gbps)** 만 나온다. 학습 시 모델/그래디언트 복사가 병목이 되어 CNI 기반으로 전환하려는 것이 출발점.

### 1.2. "CNI를 쓴다"의 의미

CNI는 **컨테이너 네트워크 셋업 plugin 인터페이스**이지 dataplane이 아니다. 실제 패킷 흐름의 속도/격리는 그 위에 깔린 **dataplane(vxlan, native routing, eBPF, macvlan, RDMA 등)** 과 **정책 엔진**이 결정한다.

따라서 "CNI를 쓴다"는 결정만으론 부족하고, **어떤 CNI plugin이 어떤 dataplane을 사용할지**까지 정해야 한다.

## 2. 요구사항

| # | 요구사항 | 용도 |
|---|---|---|
| R1 | BAI 컨테이너끼리 cross-host 통신 가능 | 다중 노드 학습 (모델/그래디언트 복사) |
| R2 | K8s Pod → BAI 컨테이너 접근 시 hop 최소, 대역폭 최대 | 추론 |
| R3 | 같은 세션 그룹 멤버끼리만 통신, 외부 컨테이너 차단 | 사용자/세션 격리 |

R3는 단순 차단이 아니라 **"그룹 단위 멤버십에 따라 자동 격리"** 를 의미한다.

## 3. 핵심 원칙: 단일 CNI fabric

> **K8s Pod와 BAI 컨테이너를 동일한 CNI fabric에 둔다. 운영 대상은 1개의 CNI.**

학습용/추론용 fabric을 분리하지 않는다. 단일 fabric만으로 R1/R2/R3 모두 충족 가능하다. 분리는 RDMA/SR-IOV 같은 특수 HW가 필요한 예외 상황에서만 도입한다 (섹션 6).

## 4. 두 가지 디폴트 옵션

R3까지 디폴트 안에서 풀어내는 두 후보를 제시한다.

- **Option 1: Cilium 단일 fabric** — 정책 엔진 내장, 표현력 강함
- **Option 2: Flannel 단일 fabric + nftables 자체 격리** — 가벼움 우선, BAI agent가 정책 책임

### 4.1. Option 1: Cilium 단일 fabric

```
[K8s 컨트롤 플레인]
   apiserver, cilium-operator
        ▲
        │ watch (Pod, CiliumNetworkPolicy, CiliumIdentity)
        │
[모든 노드 (K8s 노드 + BAI agent 호스트)]
   ├─ cilium-agent
   ├─ kernel eBPF programs
   ├─ K8s Pod        ─── cilium endpoint
   └─ BAI 컨테이너    ─── cilium endpoint
```

#### R1 분석 (BAI ↔ BAI cross-host)

- **메커니즘**: BAI 호스트에 cilium-agent 배치, BAI 컨테이너 sandbox 생성 시 cilium-cni 호출 → cilium-agent에 endpoint 등록 → 다른 호스트의 cilium-agent들과 자동 라우팅 합의
- **dataplane 두 모드**
  - **native routing (BGP)**: encap 0, 10G에서 9.4 Gbps near line rate
  - **vxlan/geneve**: encap 있음, 튜닝(NIC offload + jumbo MTU) 시 7-9 Gbps
- **결과**: Swarm 대비 2-3x

#### R2 분석 (K8s Pod → BAI)

- **메커니즘**: K8s Pod도 같은 cilium fabric의 endpoint이므로 Pod ↔ BAI는 같은 dataplane을 공유
- **hop**: 0 추가 hop. NAT 없음. eBPF가 라우팅 + 정책 평가를 한 번에 처리
- **결과**: R1과 동일한 dataplane 성능 (native routing이면 line rate)

#### R3 분석 (세션 그룹 격리)

- **메커니즘**: CiliumNetworkPolicy + identity 라벨
- **BAI agent 책임**: 컨테이너에 `session_group=<id>`, `user=<name>` 등 라벨 부여
- **정책 표현**: 라벨 셀렉터 한 개로 멤버십 격리
  ```yaml
  apiVersion: cilium.io/v2
  kind: CiliumNetworkPolicy
  spec:
    endpointSelector:
      matchLabels: {session_group: G123}
    ingress:
    - fromEndpoints:
      - matchLabels: {session_group: G123}
  ```
- **enforcement**: 커널 eBPF, 정책 룰 수에 거의 영향 없음
- **결과**: 같은 그룹끼리만 자동 통신, 다른 그룹은 차단, K8s Pod에서의 추론 접근은 별도 정책 한 줄로 허용

#### 필요한 것

- **BAI 호스트**
  - cilium-agent 실행
  - cilium-cni binary 배치 (`/opt/cni/bin/cilium-cni`)
  - 호스트를 K8s 노드로 등록하거나, Cilium ClusterMesh의 external workload로 편입
- **K8s 측**
  - 클러스터에 Cilium 설치 (이미 깔려 있다면 재사용)
  - 모드 선택: native routing(BGP 가능 시) 또는 vxlan
- **BAI agent 측**
  - sandbox 생성 시 cilium-cni 호출 또는 cilium-agent endpoint API (`PUT /v1/endpoint/`) 사용
  - 컨테이너에 식별 라벨 부여 규칙
  - 세션 그룹 lifecycle에 맞춰 CiliumNetworkPolicy CRD 생성/삭제

#### 특성

- 운영 부담: 중 (Cilium 운영 + BAI 통합)
- 성능: native routing이면 최상, vxlan이어도 Swarm 대비 2x+
- 정책 표현력: 강함 (identity, 라벨 셀렉터)
- 외부 의존: K8s 컨트롤 플레인 (apiserver) 필요

### 4.2. Option 2: Flannel 단일 fabric + nftables 자체 격리

```
[모든 노드 (K8s 노드 + BAI agent 호스트)]
   ├─ flanneld           (etcd 또는 K8s API 백엔드)
   ├─ flannel CNI plugin
   ├─ K8s Pod        ─── Flannel 네트워크
   ├─ BAI 컨테이너    ─── Flannel 네트워크
   └─ nftables 룰셋 (BAI agent가 관리, R3 전용)
```

#### R1 분석 (BAI ↔ BAI cross-host)

- **메커니즘**: Flannel이 호스트별 subnet 분배 + cross-host 연결
- **dataplane backend 두 모드**
  - **vxlan**: 표준, 튜닝 시 7-9 Gbps
  - **host-gw**: encap 0, line rate 9.4 Gbps (단, 모든 호스트가 같은 L2)
- **결과**: Swarm 대비 2-2.5x (vxlan), 2.7x (host-gw)

#### R2 분석 (K8s Pod → BAI)

- **메커니즘**: K8s Pod와 BAI 컨테이너가 같은 Flannel 네트워크에 속하면 직접 라우팅
- **hop**: 0 (Flannel 라우팅이 호스트 간 직결)
- **결과**: dataplane 한도

#### R3 분석 (세션 그룹 격리)

- **메커니즘**: Flannel은 NetworkPolicy 미지원 → **BAI agent가 호스트 nftables 룰을 직접 관리**
- **BAI agent 책임**
  - 세션 그룹별 IP set 유지: `nft add set inet bai grp123 { type ipv4_addr; }`
  - 세션 시작 시 멤버 컨테이너 IP를 set에 추가
  - 기본 정책: 그룹 IP set 외부에서 들어오는 트래픽 DROP
  - K8s Pod에서의 정상 접근은 명시 allow 룰 (Pod CIDR 또는 라벨 매칭 어려우니 IP 기반)
  - 종료 시 set/룰 정리
- **enforcement**: 호스트 nftables, 룰 수가 수천을 넘으면 성능 측정 필요
- **한계**
  - 라벨/identity 표현 불가, IP 기반만
  - 호스트 단위 룰셋 — 컨테이너 이동 시 reconcile 필요
  - 정책 권한 모델은 BAI agent가 책임짐

#### 필요한 것

- **BAI 호스트**
  - flanneld 실행
  - flannel CNI plugin + bridge plugin (`/opt/cni/bin/flannel`, `bridge`)
  - nftables (커널 4.x+ 권장)
- **K8s 측**
  - Flannel CNI 사용 (BAI 호스트와 같은 backend, 같은 etcd 또는 같은 K8s API)
  - 신규 환경이면 K8s에 Flannel 설치
- **BAI agent 측**
  - flannel CNI 호출 통합
  - nftables 관리 모듈 (세션 그룹 ↔ IP set ↔ 룰 매핑)
  - 그룹 lifecycle hook: 시작/종료 시 룰 add/del
  - reconcile 로직: agent 재시작 후 기존 룰 vs 실제 컨테이너 정합성

#### 특성

- 운영 부담: 작음 (Flannel 자체) + BAI agent 코드 추가
- 성능: vxlan 한도 또는 host-gw 시 line rate
- 정책 표현력: 제한적 (IP set 기반)
- 외부 의존: etcd 또는 K8s API (Flannel backend)

## 5. 두 디폴트 비교

| 항목 | Option 1: Cilium | Option 2: Flannel + nftables |
|---|---|---|
| R1 cross-host throughput (10G) | 7-9 Gbps (vxlan) / 9.4 Gbps (native) | 7-9 Gbps (vxlan) / 9.4 Gbps (host-gw) |
| R2 Pod → BAI hop | 0 | 0 |
| R2 throughput | R1과 동일 | R1과 동일 |
| R3 enforcement | CiliumNetworkPolicy (라벨/identity) | BAI agent 관리 nftables (IP 기반) |
| R3 표현력 | 강함 | 제한적 |
| R3 성능 영향 | eBPF, 거의 free | nftables 룰 수에 비례 |
| K8s 통합 | 필수 (apiserver 의존) | 약함 (Flannel backend만 공유) |
| BAI agent 코드 변경량 | 작음 (CNI + 라벨) | 중간 (CNI + nftables 모듈) |
| 운영 도구 | cilium CLI, Hubble | flanneld, BAI agent 자체 |
| 적합한 상황 | K8s가 이미 Cilium / 정책 풍부히 / 대규모 | 단순함 / 외부 의존 최소 / 소~중규모 |

## 6. 디폴트가 부족할 때 (특수 케이스)

단일 fabric으로 부족한 케이스에서만 **보조 fabric을 추가** (컨테이너에 두 번째 인터페이스 attach).

### 6.1. Production 다중 노드 GPU 학습 (NCCL line rate)

- 보조 fabric: **RDMA (RoCE/InfiniBand) + SR-IOV**
- CNI: `sriov-cni` + `rdma-cni` (Multus chained)
- 격리: **P_Key (IB)** 또는 **VLAN (RoCE)** — HW 레벨, 성능 손해 0
- 디폴트 fabric은 제어/일반 통신용으로 유지

### 6.2. LLM 추론 line rate (페이로드 큰 스트리밍)

- 보조 fabric: **SR-IOV** (NIC VF 직접 부여)
- CNI: `sriov-cni`
- 격리: VF별 VLAN
- 추론 endpoint 컨테이너만 dual-attach

### 6.3. cross-L2 환경에서 line rate

- Option 1: native routing 모드 + BGP 도입
- Option 2: host-gw는 같은 L2 필요 → vxlan으로 후퇴 (line rate 포기) 또는 별도 BGP 셋업

## 7. 결정 가이드

> **단일 질문: "K8s 측 CNI가 무엇인가?"**

| K8s CNI | 권장 |
|---|---|
| Cilium | Option 1 (그대로 통합) |
| Calico | Option 1과 유사한 통합 가능 (Calico 정책 + WorkloadEndpoint), 또는 Cilium으로 마이그레이션 |
| Flannel | Option 2 (그대로 통합) |
| 미정 / 신규 | **Option 1 권장** (정책 표현력 + 모던 stack) |
| 없음 (BAI 단독 운영) | **Option 2 권장** (가장 가벼움, 외부 의존 최소) |

## 8. BAI agent 구현 포인트

선택한 옵션과 무관하게 공통적으로 필요한 작업:

1. **CNI 호출 통합**
   - containerd CRI plugin이 PodSandbox 생성 시 conflist 기반으로 CNI 자동 호출
   - 또는 BAI agent가 sandbox 생성 후 직접 CNI binary 호출
   - 옵션별 conflist 사전 배치 (`/etc/cni/net.d/`)
2. **메타데이터/라벨 부여**
   - 컨테이너에 `session_group`, `user`, `kernel` 등 식별 라벨/주석
   - Option 1: cilium identity 매핑 키
   - Option 2: nftables set 매핑 키 (IP 추적용)
3. **격리 자원 lifecycle**
   - 그룹 생성 시
     - Option 1: CiliumNetworkPolicy CRD apply
     - Option 2: nftables set 생성 + 기본 DROP 룰
   - 멤버 추가/삭제 시 set/policy 갱신
   - 그룹 종료 시 회수
4. **IPAM**
   - Option 1: Cilium IPAM (cluster-pool 또는 custom)
   - Option 2: Flannel host subnet (자동) + 컨테이너에 host-local 분배
5. **장애/재시작 reconcile**
   - agent 재시작 후 기존 컨테이너의 endpoint/IP/룰 정합성 검증
   - K8s 측 객체와 호스트 상태 mismatch 감지/복구

## 9. 현재 prototype 구현 상태

`feat/containerd-agent-prototype` 브랜치에 14개 커밋으로 추가된 코드의 구조와 진행도. 모든 신규 코드는 `src/ai/backend/agent/containerd/` 하위에 격리되어 있고, 기존 코드 수정은 최소(`types.py`, `runtime.py`, `cli/__main__.py`, `config/unified.py`, `errors/__init__.py`).

### 9.1. 패키지 구조

```
src/ai/backend/agent/
├── containerd/                       # 신규 패키지
│   ├── __init__.py                   # ContainerdAgentDiscovery
│   ├── agent.py                      # ContainerdAgent (스캐폴드)
│   ├── kernel.py                     # ContainerdKernel (스캐폴드)
│   ├── intrinsic.py                  # placeholder
│   ├── resources.py                  # 빈 mapping 리턴
│   ├── preflight.py                  # 시작 시 CNI/binary 검증
│   └── cri/
│       ├── client.py                 # async CriClient
│       ├── proto/api.proto           # k8s cri-api v1.30
│       └── generated/                # protoc 산출물 (sync stubs + .pyi)
├── cli/cri_poc.py                    # PoC 검증 CLI
├── errors/containerd.py              # Cni*/Cri* 예외
├── config/unified.py                 # ContainerdNetworkMode + Config
├── runtime.py                        # backend=containerd 시 preflight hook
└── types.py                          # AgentBackend.CONTAINERD 추가
```

### 9.2. 레이어별 상태

#### L1. CRI gRPC 클라이언트 — 완성

- `containerd/cri/generated/`: k8s cri-api v1.30 `api.proto`에서 protoc로 생성. mypy-protobuf의 `*AsyncStub` 타입 stub(.pyi) 동봉
- `containerd/cri/client.py` `CriClient`: `grpc.aio` 기반 async wrapper
  - 노출 RPC: `Version`, PodSandbox lifecycle (Run/Stop/Remove/Status/List), Container lifecycle (Create/Start/Stop/Remove/List/Status), Image (Pull/Status/List/Remove)
  - 미노출: 스트리밍 RPC (`Exec`/`Attach`/`ContainerStats`), filesystem/runtime-config endpoints — agent 통합 시점에 추가
- 타입 트릭: protoc는 sync stub만 생성 → 런타임은 sync stub 인스턴스화 후 **TYPE_CHECKING 블록의 forward-ref로 AsyncStub 이름 빌려와 `cast()`** (커밋 005bb9fa7, 2ed3cd87a)
- 안전장치: 채널 connect timeout 5s 디폴트 — 무한 hang 방지 (커밋 ac7d7279d)

#### L2. Backend 스캐폴드 — 의도적으로 비어 있음

- `agent.py` `ContainerdAgent`: `AbstractAgent` 추상 메서드 미override → 인스턴스화 불가. docstring에 "package wiring과 discovery 검증용"만 명시
- `kernel.py` `ContainerdKernel`, `ContainerdKernelCreationContext`: 동일
- `resources.py` `load_resources`/`scan_available_resources`: 빈 mapping 리턴
- `intrinsic.py`: CPU/Memory plugin placeholder
- `__init__.py` `ContainerdAgentDiscovery`: `AbstractAgentDiscovery` 구현으로 `AgentBackend.CONTAINERD` 선택 시 wiring 작동

#### L3. Config 스키마 — 완성 (4 모드)

`config/unified.py`에 `ContainerdNetworkMode` enum + `ContainerdNetworkConfig` 추가. **본 문서의 Option 1/2와의 매핑:**

| `mode` enum | 본 문서 매핑 | 의도 |
|---|---|---|
| `cilium` | **Option 1 (Cilium 단일 fabric)** | K8s 노드, 클러스터 Cilium CNI에 위임. 합성 namespace/name으로 PodSandboxConfig.metadata 채워서 RunPodSandbox 호출 → Cilium이 `reserved:init` identity 부여 + cluster pod CIDR에서 IP 할당 |
| `managed` | (단일 호스트 dev) | standalone 노드, agent가 bridge+portmap conflist 직접 생성/배치. cross-host overlay 없음 — 개발/테스트 또는 단일 호스트용 |
| `host` | **Option 2 (Flannel 등) 진입점** | operator 제공 conflist 사용. Flannel을 클러스터에 깔고 그 conflist 이름을 BAI agent가 참조하면 Option 2 통합 |
| `none` | escape hatch | CNI 우회, host network namespace. 포트 충돌 위험 — service-port allocator가 host-port 충돌 회피 책임 |

설정 필드:
- `cni_conf_dir`, `cni_bin_dir`: CNI conflist/binary 위치
- `network_name`: managed에선 생성될 conflist의 name, host에선 참조할 기존 conflist의 name
- `bridge_name`, `subnet`: managed mode 전용
- `cilium_pod_namespace`, `cilium_pod_name_prefix`: cilium mode에서 합성 metadata 채울 때 사용

`OverridableContainerConfig.containerd`로 Optional 등록, `ContainerdExtraConfig`가 `agent.backend == 'containerd'`일 때 존재 강제.

#### L4. Startup preflight — 완성

`preflight.py` `run_preflight()` — agent 시작 시 mode별로 분기:

- `none`: no-op
- `cilium`: no-op. 클러스터 CNI 설정은 운영자 영역, 런타임 검증(IP 할당/회수, cilium-agent 소켓)은 PoC CLI로 분리
- `managed`: 필수 binary(`bridge`/`portmap`/`host-local`/`loopback`) 존재 + `cni_conf_dir` 쓰기 가능 검증
- `host`: 필수 binary + 이름 매칭되는 conflist 로드 + plugin chain에 `portmap` 포함 검증

I/O는 모두 `asyncio.to_thread`로 dispatch — event loop 블록 방지. 예외는 모두 `BackendAIError` 상속 (`errors/containerd.py`):
- `CniBinaryMissingError`, `CniConfDirNotWritableError`, `CniConflistMissingError`, `CniConflistInvalidError`, `CniPortmapMissingError`
- `CriConnectionError`, `CriRpcError`

`runtime.py`에서 backend가 CONTAINERD면 시작 시 `run_preflight()` 호출.

#### L5. PoC 검증 CLI — 완성 (현재 테스트 surface)

**`bai ag cri-poc run`** — manager/full agent lifecycle 없이 **agent 단독으로 CRI 전체 lifecycle을 한 번 walk**해서 단계별 결과 리포트.

호출 순서:
```
Version → ImageStatus → (Pull) → RunPodSandbox → PodSandboxStatus
   → CreateContainer → StartContainer → ContainerStatus
   → (--pause: ENTER 대기) → StopContainer → RemoveContainer
   → StopPodSandbox → RemovePodSandbox
```

각 step `StepResult(name, ok, duration_ms, detail)` 누적, 마지막에 사람용/JSON 출력.

플래그:
- `--pause`: Start 후 ENTER 대기 — 다른 셸에서 `cilium endpoint list`, `crictl pods`, `nsenter` 등으로 인스펙션
- `--keep`: 정리 스킵 (post-mortem)
- `--json-output`: 기계 파싱

**docstring에 명시된 V1 cilium-mode 검증 목표 3가지:**

1. 합성 `PodSandboxConfig.metadata` (apiserver에 backing Pod 객체 없음) 로도 Cilium CNI가 sandbox를 거부하지 않는지 — `reserved:init` identity로 떨어지면서 cluster pod CIDR에서 IP 할당받는지
2. `RemovePodSandbox`가 CNI DEL을 깔끔하게 트리거해서 IP가 풀로 회수되는지 (leak 없음)
3. agent 프로세스가 containerd CRI 소켓에 적합한 권한으로 도달 가능한지

### 9.3. 진행도 표

| 영역 | 상태 |
|---|---|
| CRI gRPC 클라이언트 | ✅ 완성 (lifecycle/image, 스트리밍 미노출) |
| Network 모드 4종 config 스키마 | ✅ 완성 |
| Preflight 검증 (managed/host/cilium/none) | ✅ 완성 |
| Backend wiring (Discovery, AgentBackend enum) | ✅ 완성 |
| **PoC 검증 CLI (`bai ag cri-poc run`)** | ✅ **완성 — 현재 테스트 surface** |
| 예외 계층 (BackendAIError 준수) | ✅ 완성 |
| `ContainerdAgent` / `ContainerdKernel` | ⚠ 스캐폴드만 (인스턴스화 불가) |
| 리소스 plugin (CPU/Memory/accelerator) | ⏳ 미작업 (빈 mapping) |
| krunner 이미지 prepare | ⏳ 미작업 (빈 dict) |
| Exec/Attach/Stats 스트리밍 | ⏳ 미작업 |
| 세션 lifecycle 통합 (kernel 생성/실행) | ⏳ 미작업 |
| AppProxy 포트 wiring | ⏳ 미작업 |
| vfolder/storage 마운트 | ⏳ 미작업 |

### 9.4. 코드 품질/컨벤션 준수

- **async-first**: `grpc.aio`, 파일시스템 I/O는 `asyncio.to_thread`
- **모든 예외 `BackendAIError` 상속**: `errors/containerd.py`에 위치 (legacy `exception.py` 회피)
- **절대 import** 일관됨
- **`# noqa` / `# type: ignore` 미사용** — TYPE_CHECKING+cast로 우회
- 의도적 미구현은 명시적: docstring "scaffold", 주석 `TODO(containerd-prototype)`

### 9.5. 다음 단계 후보

PoC가 V1 cilium-mode 검증을 통과한다는 가정하에, 영향 큰 순서:

1. **`ContainerdKernelCreationContext` 채우기** — Docker backend 패턴 참조해서 `KernelCreationConfig` → CRI `ContainerConfig` 변환 (마운트, 포트, env, resources). 이게 들어가야 ContainerdAgent가 인스턴스화 가능
2. **인트린식 plugin (CPU/Memory)** — Docker `intrinsic.py` 패턴, 메트릭은 CRI `ContainerStats`로
3. **포트 매핑 정책 결정** — `cilium` mode는 portmap을 chain하지 않으므로 service 포트 노출 방식이 docker backend와 다름. App Proxy 통합 시점에 설계 필요
4. **Exec 스트리밍** — code-runner 통합 전제
5. **krunner 이미지 prepare** — `ImageService.PullImage`로 부트스트랩
6. **세션 그룹 격리 자원 관리** (섹션 8 항목 3) — Option 1 채택 시 CiliumNetworkPolicy CRD lifecycle, Option 2 채택 시 nftables 모듈

문서화 측면: `cri_poc.py`/`unified.py`/`preflight.py` docstring에 의도/제약/미구현 사유가 잘 적혀 있어 사실상 설계 문서 역할 수행 중.

## 10. 부록 A: dataplane별 10G 실측 참고

| Dataplane | 10G NIC 실측 | line rate 대비 | Swarm 대비 |
|---|---|---|---|
| Docker Swarm overlay | 3-4 Gbps | 30-40% | 1x baseline |
| Flannel vxlan (튜닝) | 7-9 Gbps | 70-90% | 2-2.5x |
| Cilium vxlan (eBPF) | 7-9 Gbps | 70-90% | 2-2.5x |
| Flannel host-gw | 9.4 Gbps | 94% | 2.7x |
| Cilium native routing (BGP) | 9.4 Gbps | 94% | 2.7x |
| Macvlan / IPvlan | 9.4 Gbps | 94% | 2.7x |
| SR-IOV | 9.9 Gbps | 99% | 3x |
| RDMA + GPUDirect | line rate, 낮은 지연 | 100% | 3x+ |

## 11. 부록 B: vxlan 사용 시 필수 튜닝

Option 1/2 모두 vxlan dataplane을 선택할 경우 적용:

- **NIC vxlan offload 활성화**
  ```
  ethtool -K <iface> tx-udp_tnl-segmentation on tx-udp_tnl-csum on
  ```
- **MTU 9000 (jumbo frame)**
  - 호스트 NIC, vxlan device, 컨테이너 인터페이스 모두 정합 필요
  - vxlan inner MTU = outer MTU - 50
- **TCP buffer 증대**
  ```
  sysctl -w net.core.rmem_max=134217728
  sysctl -w net.core.wmem_max=134217728
  sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
  sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"
  ```
- **NIC multi-queue**
  - `ethtool -L <iface> combined <#cores>` 또는 자동
  - IRQ affinity 분산

이 튜닝만으로도 같은 vxlan에서 Swarm 대비 2배 이상 차이 남.
