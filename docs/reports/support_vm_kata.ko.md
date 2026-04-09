# Backend.AI VM 런타임 지원: Kata Containers와 KubeVirt

| 항목 | 값 |
|---|---|
| **문서 ID** | TR-2026-003 |
| **작성일** | 2026-04-08 |
| **작성자** | Backend.AI Architecture Team |
| **상태** | 초안 |
| **분류** | 내부 기술 참조 문서 |
| **관련 문서** | `k8s-control-plane-dood-agent-architecture.ko.md`, `kata-containers-feature-parity-analysis.md` |
| **범위** | 기본 DooD 아키텍처에 대한 대안으로 VM 기반 격리 런타임(Kata Containers, KubeVirt)을 지원하기 위한 고려사항 및 필요 변경 사항 |

---

## 목차

1. [요약](#1-요약)
2. [배경 및 동기](#2-배경-및-동기)
   - 2.1 [DooD가 기본인 이유](#21-dood가-기본인-이유)
   - 2.2 [VM 격리가 반드시 지원되어야 하는 이유](#22-vm-격리가-반드시-지원되어야-하는-이유)
3. [VM 런타임 옵션](#3-vm-런타임-옵션)
   - 3.1 [Kata Containers](#31-kata-containers)
   - 3.2 [KubeVirt](#32-kubevirt)
   - 3.3 [DooD와의 비교](#33-dood와의-비교)
4. [GPU + VM 제약](#4-gpu--vm-제약)
   - 4.1 [Firecracker는 GPU 워크로드에 사용 불가](#41-firecracker는-gpu-워크로드에-사용-불가)
   - 4.2 [GPU의 VM 정적 바인딩](#42-gpu의-vm-정적-바인딩)
   - 4.3 GPU에서 VM 풀링이 작동하지 않는 이유
   - 4.4 GPU VM Cold Start 현실
5. 운영 전략
   - 5.1 세션별 Runtime Class 선택
   - 5.2 전용 GPU 풀 (사전 커밋 VM)
   - 5.3 NVIDIA vGPU 및 MIG 통합
   - 5.4 혼합 노드를 위한 GPU별 드라이버 바인딩
6. 언제 VM 기반 격리를 선택해야 하는가
7. 하이브리드 런타임 아키텍처 설계
8. 시스템 전반 변경 사항
   - 8.1 Agent 코어 아키텍처
   - 8.2 커널 통신
   - 8.3 GPU 할당
   - 8.4 스토리지
   - 8.5 네트워킹
   - 8.6 이미지 관리
   - 8.7 Manager 및 스케줄러
   - 8.8 노드 인프라
   - 8.9 모니터링 및 관측성
   - 8.10 Helm Chart 및 배포
   - 8.11 API / CLI / UI
   - 8.12 테스트 인프라
9. 재사용 가능 vs 재작성 필요 요약
10. 핵심 아키텍처 결정
11. 점진적 구현 로드맵
12. 공수 추정
13. 결론 및 권고사항
14. 참고 문헌

---

## 1. 요약

이 문서는 `k8s-control-plane-dood-agent-architecture.ko.md`에서 확립된 기본 Docker-out-of-Docker(DooD) 아키텍처와 함께 VM 기반 격리 런타임 — Kata Containers와 KubeVirt — 을 지원하기 위한 요구사항과 트레이드오프를 분석한다.

**핵심 발견 사항:**

- **VM 기반 격리는 옵션으로 지원되어야 한다** — 공유 커널 컨테이너로는 부족한 엄격한 보안, 멀티테넌시, 규제 요구사항을 가진 환경을 위해.
- **GPU 워크로드는 대부분의 VM 최적화 기법을 무력화한다**: Firecracker는 GPU 패스스루 불가, VM 풀링은 GPU 낭비, GPU 초기화 오버헤드로 인해 Cold Start가 30초~수 분.
- **GPU별 드라이버 바인딩**은 하이브리드 노드(일부 GPU는 DooD, 다른 일부는 VM)를 가능하게 하나, GPU 단위 스케줄러 추적이 필요하다.
- **VM에서 분할 GPU는 동작하지 않음** — Backend.AI의 CUDA 훅 라이브러리 메커니즘이 VM 경계를 넘을 수 없음. NVIDIA vGPU(Enterprise 라이선스) 또는 MIG가 유일한 대안.
- **시스템 전반 변경**은 12개 아키텍처 레이어에 걸쳐 있으며 풀타임 엔지니어 2-3명으로 12-18개월의 엔지니어링 노력이 필요하다.
- **점진적 도입** 권장: 기반 → Kata → KubeVirt → VM에서 분할 GPU.

---

## 2. 배경 및 동기

### 2.1 DooD가 기본인 이유

주 아키텍처(`k8s-control-plane-dood-agent-architecture.ko.md`에 기술됨)는 커널 컨테이너 관리를 위해 Docker-out-of-Docker(DooD)를 사용한다. 이 선택의 장점:

- **완전한 GPU 기능 지원**: 멀티 GPU, CUDA 훅 라이브러리를 통한 분할 GPU, MIG, NUMA 인식
- **베어메탈과 동일한 성능**: VM 오버헤드 없음
- **최소한의 Backend.AI 코드 변경**: 기존 `DockerAgent`가 변경 없이 동작
- **빠른 시작**: 커널 컨테이너 생성에 ~1-3초
- **네이티브 바인드 마운트**: vfolder 접근에 오버헤드 없음

대다수의 Backend.AI 워크로드(단일 테넌트 또는 신뢰 가능한 테넌트의 AI/ML 학습 및 추론)에서 DooD는 기능, 성능, 운영 단순성의 최적 균형을 제공한다.

### 2.2 VM 격리가 반드시 지원되어야 하는 이유

DooD의 장점에도 불구하고, 많은 실제 배포에서 VM 기반 격리는 **선택 사항이 아니다**:

| 동기 | 설명 |
|---|---|
| **신뢰할 수 없는 코드의 멀티테넌시** | 사용자가 임의 코드 실행 가능; 커널 CVE를 통한 컨테이너 탈출이 허용 불가 |
| **규제 준수** | PCI-DSS, HIPAA, FedRAMP, ISO 27001은 하드웨어 강제 격리를 요구할 수 있음 |
| **기밀 컴퓨팅** | Intel TDX, AMD SEV-SNP를 통한 사용 중 데이터 보호는 VM 기반 실행 필요 |
| **보안 연구** | 악성코드 분석, 취약점 연구, 신뢰할 수 없는 실험 |
| **정부/국방** | 엄격한 격리 요구사항을 가진 기밀 워크로드 |
| **고객 요구사항** | 엔터프라이즈 고객이 계약상 명시적으로 VM 격리 요구 |

이러한 시나리오에서 "DooD가 더 빠르다"는 유효한 논거가 아니다 — VM 격리는 전제 조건이며, 시스템이 이를 수용해야 한다. 질문은 VM 런타임을 *지원할지 말지*가 아니라, DooD 사용자에게 최소한의 disruption으로 *어떻게 통합할지*이다.

---

## 3. VM 런타임 옵션

### 3.1 Kata Containers

Kata Containers는 각 Kubernetes Pod을 경량 VM 안에서 실행하여 Pod 레벨 하드웨어 격리를 제공한다. 기존 OCI 컨테이너 이미지는 변경 없이 실행되지만, 각 Pod은 자체 게스트 커널과 하이퍼바이저 경계를 갖는다.

**아키텍처:**

```
┌─── K8s 노드 ─────────────────────────────────────────────┐
│                                                           │
│  호스트 OS                                               │
│    ├── containerd + kata-runtime                         │
│    └── kata-shim이 VM 라이프사이클 관리                  │
│                                                           │
│  ┌── 커널 컨테이너 (Kata 경유) ──────────────────────┐  │
│  │  경량 VM (Cloud Hypervisor / QEMU)                 │  │
│  │  ┌─── 게스트 커널 (최소) ─────────────────────┐   │  │
│  │  │  kata-agent                                 │   │  │
│  │  │  컨테이너 런타임                            │   │  │
│  │  │    └── 커널 워크로드                        │   │  │
│  │  │         └── VFIO를 통한 GPU                 │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

**GPU 지원 제한** (전체 분석은 `kata-containers-feature-parity-analysis.md` 참조):

- VFIO 패스스루를 통해 컨테이너당 **단일 GPU만**
- 단일 컨테이너에 **멀티 GPU 할당 불가**
- **분할 GPU 불가** — VFIO는 디바이스 전체를 패스함, CUDA 훅 라이브러리는 VM 경계를 넘지 못함
- **NVIDIA Container Toolkit 통합 불가** — 호스트 쪽 디바이스 매핑이 VM 경계를 넘지 못함
- 하이퍼바이저에 따라 부분적 MIG 지원
- 프라이버시 민감 워크로드를 위한 기밀 컴퓨팅 지원 (TDX, SEV-SNP)

**Backend.AI DooD 모델과의 통합**: Kata는 커널 컨테이너가 K8s Pod이 아니기 때문에 DooD 아키텍처와 직접 호환되지 않는다. Kata 도입은 다음 중 하나를 요구한다:

- K8s 네이티브 커널 모델(커널을 Pod으로)로 전환, DooD 포기
- 또는 선택적 사용: 대부분 워크로드는 DooD, 강한 격리가 필요한 특정 옵트인 세션에만 Kata

### 3.2 KubeVirt

KubeVirt는 `VirtualMachine` 커스텀 리소스로 Kubernetes를 확장하여, 일반 Pod과 함께 동일 노드에서 전체 VM을 실행한다. Kata가 VM을 Pod으로 가장하는 것과 달리, KubeVirt VM은 전체 라이프사이클 관리를 가진 일급 K8s 리소스이다.

**GPU 지원:**

- 전용 GPU를 위한 **VFIO PCI 패스스루** (베어메탈 VM 패스스루와 유사)
- **VM당 멀티 GPU** — 여러 PCI 디바이스를 단일 VM에 패스 가능
- **NVIDIA vGPU (Enterprise)** — NVIDIA vGPU Manager를 통한 하이퍼바이저 레벨 time-slicing 및 메모리 파티셔닝
- 네트워크/FPGA 디바이스를 위한 **SR-IOV**
- **CUDA 훅 라이브러리 불가** — Backend.AI의 유저스페이스 분할 GPU 메커니즘이 VM 컨텍스트에서 동작하지 않음

**Backend.AI와의 통합**: 완전한 KubeVirt 통합은 상당한 아키텍처 변경을 요구한다:

- 각 세션이 컨테이너가 아닌 VM이 됨
- Agent가 Docker 컨테이너 대신 `VirtualMachine` 리소스를 생성/관리해야 함
- 커널 러너가 VM 이미지에 사전 설치되어야 함 (cloud-init 또는 이미지에 포함)
- CDI (Containerized Data Importer) 또는 PVC 백업 디스크를 통한 스토리지
- 다중 네트워크 연결을 위한 Multus CNI를 통한 네트워킹
- 다른 메트릭/모니터링 경로 (컨테이너 cgroup 대신 libvirt 메트릭)

### 3.3 DooD와의 비교

| 기능 | DooD (기본) | Kata Containers | KubeVirt |
|---|---|---|---|
| 격리 경계 | cgroup/namespace (소프트) | 하드웨어 VM (하드, Pod당) | 하드웨어 VM (하드, VM당) |
| GPU 할당 메커니즘 | Docker 디바이스 패스스루 | VFIO 패스스루 | VFIO 패스스루 |
| 단일 GPU | 완전 지원 | 지원 | 지원 |
| 인스턴스당 멀티 GPU | 완전 지원 | **미지원** | 지원 (다중 VFIO) |
| 분할 GPU (cuda.shares) | 완전 지원 (CUDA 훅 라이브러리) | **미지원** | NVIDIA vGPU (Enterprise 라이선스) |
| MIG 지원 | 완전 지원 | 제한적 | 지원 |
| NVIDIA Container Toolkit | 완전 지원 | 해당 없음 | 해당 없음 |
| 기존 컨테이너 이미지 | 변경 없음 | 변경 없음 | VM 이미지 변환 필요 |
| Agent 코드 변경 | 없음 | 중간 (K8s 네이티브 커널) | 대규모 (VM 라이프사이클 관리) |
| 시작 레이턴시 | ~1-3초 | ~30초 (GPU 포함) | 1-2분 (GPU 포함) |
| 메모리 오버헤드 | ~5-20MB | Pod당 ~50-150MB | VM당 ~500MB-1GB |
| CVE 폭발 반경 | 컨테이너 경계 | Pod 경계 | VM 경계 |
| 기밀 컴퓨팅 (TDX, SEV) | 불가 | 지원 (CoCo) | 지원 |

---

## 4. GPU + VM 제약

VM 기반 격리에는 잘 알려진 최적화 기법(Firecracker, VM 풀, 템플릿팅, 스냅샷/재개)이 있다. **GPU 워크로드에서는 거의 전부 작동하지 않으며**, CPU 전용 VM 시나리오 대비 비용/이점 분석이 근본적으로 달라진다.

### 4.1 Firecracker는 GPU 워크로드에 사용 불가

Firecracker — AWS의 ~125ms 부팅 시간을 가진 미니멀 VMM — 은 Kata에서 가장 빠른 하이퍼바이저 옵션이다. 그러나:

- Firecracker는 설계상 **VFIO 지원을 명시적으로 제외**
- CPU 전용 서버리스 워크로드를 위해 설계됨 (AWS Lambda, Fargate)
- VFIO는 공격 표면을 크게 확대하여 Firecracker의 미니멀리즘 목표와 모순
- **결과**: Backend.AI GPU 워크로드에 Firecracker는 옵션이 아님

이는 Kata의 가장 빠른 VMM 옵션을 제거한다. GPU 워크로드의 경우 현실적인 Kata 선택지는 Cloud Hypervisor 또는 QEMU이며, 둘 다 시작이 눈에 띄게 느리다.

### 4.2 GPU의 VM 정적 바인딩

VFIO 패스스루는 다음과 같이 동작한다:

```
VM 생성 시:
  ├── 호스트가 GPU를 nvidia 드라이버에서 unbind
  ├── 호스트가 vfio-pci 드라이버에 bind
  ├── IOMMU 그룹 설정
  ├── VM에 PCI 디바이스 노출
  └── VM이 PCI 디바이스 부팅 및 초기화

VM 실행 중:
  ├── GPU가 VM에 "소유됨"
  ├── 호스트는 이 GPU를 볼 수 없음
  └── 다른 VM에 동시 할당 불가
```

**PCI Hot-plug?** 이론적으론 가능하지만 실제로는:

- NVIDIA 드라이버가 런타임 PCI 토폴로지 변경을 잘 처리하지 못함
- CUDA 컨텍스트가 디바이스 재초기화를 견디지 못함
- 게스트 커널이 디바이스 제거 시 자주 패닉
- 프로덕션에서 사실상 사용 불가

**결론**: GPU를 다른 VM에 재할당하려면 현재 VM 종료, GPU unbind, 새 VM 생성, GPU bind가 필요. VM 재시작이 필수.

### 4.3 GPU에서 VM 풀링이 작동하지 않는 이유

CPU 전용 워크로드의 표준 최적화는 사전 부팅된 VM의 "warm pool"을 유지하는 것이다:

```
일반 CPU 전용 워크로드 (풀링 가능):
┌──── Warm Pool ────┐
│  VM 1 (idle) ☉   │  ← 요청 도착
│  VM 2 (idle) ☉   │    할당만 하면 됨
│  VM 3 (idle) ☉   │
└────────────────────┘

GPU 워크로드 (풀링 불가능):
┌──── "Warm Pool"? ───────────────┐
│  VM 1 (idle, GPU 0 점유) ⚠️     │  ← GPU가 이 VM에 묶여있음
│  VM 2 (idle, GPU 1 점유) ⚠️     │    유휴 상태에서도
│  VM 3 (idle, GPU 2 점유) ⚠️     │
└────────────────────────────────┘
     → 유휴 VM이 GPU를 점유하여 다른 곳에서 사용 불가
     → $20K-30K H100에 대해 극도로 낭비
     → "사전 할당"에 불과한 "사전 워밍"
```

GPU는 너무 비싸서 유휴 VM에 묶어두기 어렵다. VM 사용을 위해 예약된 8 H100 풀은 $200K의 하드웨어가 요청을 기다리며 대기하는 것을 의미한다. 이는 거의 정당화되지 않는다.

### 4.4 GPU VM Cold Start 현실

GPU 워크로드의 VM cold start 레이턴시는 VMM 선택이 아닌 **GPU 하드웨어 초기화**에 의해 근본적으로 제약된다:

```
CPU 전용 VM 부팅:
  커널 부팅 ──▶ init ──▶ 준비 (수 초)

GPU VM 부팅:
  커널 부팅 ──▶ init ──▶ NVIDIA 드라이버 로드 ──▶ 
  GPU 초기화 (PCI scan, VBIOS, ECC init) ──▶ 준비
  (GPU 종류와 개수에 따라 30초~수 분)
```

특히 H100 GPU는 ECC 메모리 초기화만으로도 수십 초가 걸린다. **GPU 자체가 병목**이며, VMM이 아니다. QEMU에서 Cloud Hypervisor로 전환해도 수백 ms만 절약될 뿐 — GPU init 비용 대비 무의미.

**전체 비교:**

| 시나리오 | Cold Start 시간 |
|---|---|
| 캐시된 이미지의 DooD 컨테이너 | 1-3초 |
| Kata + Cloud Hypervisor + GPU | 30-60초 |
| Kata + QEMU + GPU | 45-90초 |
| KubeVirt 전체 VM + GPU | 1-3분 |

---

## 5. 운영 전략

Cold start 비용에도 불구하고, 적절한 운영 전략으로 VM 격리를 실용적으로 만들 수 있다. Backend.AI의 일반적인 워크로드 패턴(장시간 세션)이 시작 레이턴시를 흡수하며, 여러 기법으로 추가 완화가 가능하다.

### 5.1 세션별 Runtime Class 선택

런타임 선택을 일급 API 파라미터로 노출하여, 사용자가 필요할 때 더 강한 격리를 옵트인할 수 있게 한다:

```
POST /sessions
{
  "image": "python:3.11",
  "runtime_class": "secure",  // "standard" | "secure" | "confidential"
  "resources": {"cuda.device": 1}
}
```

| runtime_class | 백엔드 | Cold Start | 격리 | 사용 사례 |
|---|---|---|---|---|
| `standard` | DooD | ~1초 | cgroup/namespace | 일반 학습/추론 |
| `secure` | Kata + CHV | ~30초 | 하드웨어 VM | 멀티테넌시, 신뢰 불가 코드 |
| `confidential` | Kata + CoCo (TDX/SEV) | ~60초 | TEE 암호화 메모리 | 민감 데이터, 규제 준수 |

사용자가 명시적으로 격리 수준을 선택하면 UX 기대치가 그에 맞게 조정된다. 사용자가 하드웨어 격리를 받는다는 것을 이해할 때 30초 대기는 허용 가능하다.

### 5.2 전용 GPU 풀 (사전 커밋 VM)

비용을 감수할 수 있는 환경의 경우, 사전 커밋된 VM을 가진 전용 GPU 풀이 사용자가 인지하는 cold start를 제거한다:

```
┌─── 보안 GPU 풀 (전용 노드) ──────────────────────────────┐
│                                                            │
│  Cold VM Pool (사전 생성, GPU 커밋)                       │
│    ├── Kata VM 1 + GPU 0  (idle, 사용자 대기)            │
│    ├── Kata VM 2 + GPU 1  (idle)                          │
│    └── Kata VM 3 + GPU 2  (idle)                          │
│                                                            │
│  요청 시:                                                 │
│    1. 사용자가 secure runtime_class로 세션 요청           │
│    2. Agent가 풀에서 하나 선택 → 즉시 할당                │
│    3. 세션 초기화 (Jupyter 등) 수초 소요                  │
│                                                            │
│  세션 종료 시:                                            │
│    1. VM 완전 파기 (메모리 + GPU 상태 삭제)               │
│    2. 새 VM 생성 및 GPU 재바인딩 → 풀에 복귀              │
│    3. (30초~1분, 사용자는 이미 작업 중)                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

- **비용**: 풀 크기 GPU가 커밋되지만 사용 안 할 때 유휴
- **이점**: 사용자 체감 cold start = 0
- **적합**: 금융, 의료, 정부 — 높은 보안 요구와 GPU 기회비용 감수 의향

### 5.3 NVIDIA vGPU 및 MIG 통합

"VFIO 전체 GPU" 제약을 우회하기 위해, 두 가지 NVIDIA 기술이 VM 간 GPU 공유를 가능하게 한다:

**NVIDIA vGPU (Enterprise 라이선스)**:

```
H100 ──분할──▶ vGPU 인스턴스 4개
                ├── VM 1 (vGPU 1)
                ├── VM 2 (vGPU 2)
                ├── VM 3 (vGPU 3)
                └── VM 4 (vGPU 4)
                
  → 여러 VM이 하나의 GPU 공유 (time-slicing + 메모리 분할)
  → VM 환경에서 분할 GPU 동작
```

**NVIDIA MIG (하드웨어 파티셔닝)**:

```
H100 ──하드웨어 분할──▶ 7개 MIG 인스턴스
                          ├── VM 1 (MIG slice 1)
                          ├── VM 2 (MIG slice 2)
                          └── ... (각 VM이 전용 MIG)
                          
  → 하드웨어 격리 + VM 격리 = 이중 보안
  → Cold start는 변하지 않으나 GPU 공유됨
```

vGPU는 라이선스 비용이 크지만 **VM 환경에서 분할 GPU를 가능하게 하는 유일한 방법**이다. 이것이 필요한 보안 중요 배포에서는 비용이 일반적으로 정당화된다.

### 5.4 혼합 노드를 위한 GPU별 드라이버 바인딩

흔한 오해는 노드 전체가 nvidia 드라이버 또는 vfio-pci 중 하나로 바인딩되어야 한다는 것이다. 실제로 바인딩은 **GPU별**이다:

```
┌─── 8-GPU 노드 (예: H100 8장) ────────────────────────────┐
│                                                            │
│  부팅 시 udev/modprobe로 정적 바인딩:                     │
│                                                            │
│  GPU 0-5 ──▶ nvidia 드라이버                              │
│      └── DooD 컨테이너용 (6개)                            │
│                                                            │
│  GPU 6-7 ──▶ vfio-pci 드라이버                            │
│      └── Kata/KubeVirt VM용 (2개)                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**구성:**

```bash
# /etc/modprobe.d/vfio.conf
# 특정 PCI 슬롯을 nvidia 대신 vfio-pci에 바인딩

# /etc/default/grub
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"

# /etc/udev/rules.d/10-vfio.rules
ACTION=="add", KERNEL=="0000:81:00.0", DRIVERS=="vfio-pci"
ACTION=="add", KERNEL=="0000:82:00.0", DRIVERS=="vfio-pci"
```

**제약:**

- 바인딩은 **정적**, 부팅 시점에 설정
- IOMMU 그룹이 분할을 허용해야 함 (각 GPU가 자체 그룹에 있어야 함)
- NVLink로 연결된 GPU는 보통 모두 같은 진영에 있어야 함
- Backend.AI 스케줄러가 노드별이 아닌 **GPU별로** runtime capability 추적
- VFIO 바인딩된 GPU는 여전히 분할 GPU 불가 (vGPU 사용 시 예외)

**유용한 경우:**

- 비용 최적화: H100 노드 전체를 DooD 또는 VM 워크로드에 전용으로 두는 것 회피
- 전용 VM 노드가 GPU 용량을 낭비할 작은 클러스터
- 점진적 마이그레이션: 모든 GPU 노드 재구성 없이 VM 지원 도입

---

## 6. 언제 VM 기반 격리를 선택해야 하는가

| 시나리오 | 권장 접근 |
|---|---|
| 일반 AI/ML 학습/추론 | **DooD** (기본) |
| 신뢰 가능한 사용자의 멀티테넌시 | **DooD** |
| 신뢰할 수 없는 코드의 멀티테넌시 | Kata (옵트인) |
| 하드웨어 격리가 필요한 규정 준수 (PCI-DSS, HIPAA) | Kata 또는 KubeVirt |
| 기밀 컴퓨팅 (TEE) | Kata (CoCo 포함) |
| 보안 연구 / 악성코드 분석 | KubeVirt (최강 격리) |
| 전체 VM이 필요한 레거시 워크로드 | KubeVirt |
| 비용 민감한 작은 클러스터 | DooD (VM 오버헤드 회피) |
| GPU 집약적 분산 학습 | DooD (Kata 멀티 GPU 제한 회피) |
| 대규모 단일 GPU 추론 | Kata 허용, DooD 선호 |

---

## 7. 하이브리드 런타임 아키텍처 설계

Backend.AI는 단일 클러스터 내에서 다음을 사용하여 여러 런타임 클래스를 지원할 수 있다:

```
┌─── 컨트롤 플레인 ──────────────────────────────────────────┐
│                                                             │
│  Manager ── Sokovan 스케줄러                                │
│    ├── 세션 runtime_class: "dood" 요청  → Agent Pool A     │
│    ├── 세션 runtime_class: "kata" 요청  → Agent Pool B     │
│    └── 세션 runtime_class: "kvm" 요청   → Agent Pool C     │
│                                                             │
└──────────────┬───────────┬───────────┬─────────────────────┘
               │           │           │
               ▼           ▼           ▼
    ┌─── Pool A ───┐ ┌─── Pool B ───┐ ┌─── Pool C ───┐
    │ DooD 에이전트│ │ Kata 에이전트│ │ KubeVirt     │
    │ (전체 GPU    │ │ (VFIO 단일   │ │ (vGPU 있는   │
    │  기능)       │ │  GPU만)      │ │  VM)         │
    └──────────────┘ └──────────────┘ └──────────────┘
```

구현 전제 조건:

1. **Taint 기반 풀 분리**: 각 런타임 클래스는 고유 taint(`backendai.io/runtime=dood`, `backendai.io/runtime=kata`, `backendai.io/runtime=kvm`)를 가진 자체 전용 노드 풀
2. **Manager 세션 라우팅**: Sokovan 스케줄러가 `runtime_class` 세션 속성에 따라 에이전트 풀 선택
3. **기능 capability 플래그**: 가속기 플러그인이 런타임 클래스별 capability 노출 (예: `runtime_class != "dood"`일 때 분할 GPU 비활성화)
4. **런타임별 에이전트 구현**: 공유 추상 인터페이스를 가진 별도 에이전트 백엔드 (`DockerAgent`, `KataAgent`, `KubeVirtAgent`)
5. **이미지 관리**: DooD/Kata용 컨테이너 이미지, KubeVirt용 VM 이미지(qcow2) — 별도 레지스트리와 pull 전략

---

## 8. 시스템 전반 변경 사항

DooD와 함께 VM 기반 격리를 일급 옵션으로 지원하려면 Backend.AI의 거의 모든 레이어에 변경이 필요하다. 아래 12개 레이어는 난이도 추정과 함께 필요한 변경 사항을 나열한다.

### 8.1 Agent 코어 아키텍처

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 1 | Agent 백엔드 추상화 | `DockerAgent`, `KubernetesAgent`, `DummyAgent` | `KataAgent`, `KubeVirtAgent` 추가. `AbstractAgent` 인터페이스 일반화 | 중간 |
| 2 | 커널 생성 경로 | `docker.containers.create()` | 런타임별 분기 | 높음 |
| 3 | 커널 ≠ 컨테이너 추상화 | "커널 = Docker 컨테이너" 가정 | 커널 = 런타임 독립 엔티티 | 높음 |
| 4 | 커널 라이프사이클 상태 머신 | `created`, `running`, `exited` | VM 상태 포함 | 중간 |
| 5 | 커널 복구 | `DockerKernelRegistryRecovery` | 런타임별 복구 로직 | 중간 |

### 8.2 커널 통신

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 6 | 통신 트랜스포트 | TCP via Docker port mapping | Kata: vsock 또는 virtio-serial / KubeVirt: 게스트 네트워크 | 높음 |
| 7 | `kernel_host` 계산 | 호스트 loopback | VM IP 또는 vsock CID | 중간 |
| 8 | 포트 풀 관리 | 호스트 포트 풀 | VM 환경에서는 다른 의미 | 중간 |

### 8.3 GPU 할당

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 9 | GPU 디바이스 매핑 | `--device /dev/nvidia0` | VFIO, vGPU, MIG UUID | 높음 |
| 10 | 분할 GPU | CUDA 훅 `LD_PRELOAD` | VM 경계 넘을 수 없음. NVIDIA vGPU 또는 MIG로 대체 | 매우 높음 |
| 11 | 멀티 GPU | 다중 `--device` | VFIO 다중 패스스루, IOMMU 그룹 | 높음 |
| 12 | NUMA 배치 | CPU 피닝 + GPU affinity | VM vCPU 피닝 + VFIO NUMA | 중간 |
| 13 | GPU 드라이버 바인딩 | 모든 GPU가 nvidia | **GPU별 바인딩** (5.4 참조) | 높음 |
| 14 | accelerator plugin API | `generate_docker_args()` | 런타임별 메서드 | 중간 |

### 8.4 스토리지

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 15 | vfolder 마운트 | Docker bind mount | Kata: virtio-fs / KubeVirt: PVC 또는 virtio-fs | 중간 |
| 16 | 스크래치 공간 | hostPath | VM은 게스트 디스크 또는 virtio-fs | 중간 |
| 17 | VFolderMount 추상화 | 호스트 → 컨테이너 경로 | 런타임 독립 추상화 | 중간 |
| 18 | 성능 차이 UX | 네이티브 I/O | virtio-fs 3-10배 느림 | 낮음 |

### 8.5 네트워킹

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 19 | 단일 노드 세션 네트워크 | Docker bridge | Kata: K8s pod 네트워크 / KubeVirt: 게스트 네트워크 | 중간 |
| 20 | 멀티 노드 세션 네트워크 | Docker Swarm overlay | CNI 기반 (Multus) | 높음 |
| 21 | 서비스 포트 노출 | Docker 포트 매핑 → AppProxy | K8s Service → AppProxy | 중간 |
| 22 | 클러스터 SSH | Swarm overlay L3 | 동등한 인터노드 L3 보장 | 높음 |

### 8.6 이미지 관리

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 23 | 커널 이미지 | OCI 컨테이너 이미지 | DooD/Kata 동일. KubeVirt는 qcow2 | 중간 |
| 24 | 이미지 빌드 파이프라인 | Dockerfile | KubeVirt용 VM 이미지 빌드 | 중간 |
| 25 | 이미지 배포 | Docker registry | KubeVirt는 CDI 또는 다른 레지스트리 | 중간 |
| 26 | 이미지 메타데이터 | OCI 라벨 | VM 호환성 메타데이터 추가 | 낮음 |

### 8.7 Manager 및 스케줄러

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 27 | Session API | `resources`, `image` | `runtime_class` 추가 | 낮음 |
| 28 | Sokovan 스케줄러 | 리소스 매칭 | runtime-aware, GPU 단위 추적 | 중간 |
| 29 | 리소스 회계 | GPU/CPU/메모리 슬롯 | VM 오버헤드 포함 | 중간 |
| 30 | Cold start 예측 | 없음 | VM 시작 시간 예측 | 낮음 |
| 31 | 세션 마이그레이션 | 미지원 | KubeVirt live migration | 높음 |
| 32 | Agent 등록 스키마 | `slots`, `capabilities` | `runtime_classes` 추가 | 낮음 |

### 8.8 노드 인프라

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 33 | 노드 풀 분리 | 단일 에이전트 노드 | 런타임별 풀 또는 GPU별 분할 | 중간 |
| 34 | GPU 드라이버 바인딩 | 모든 GPU가 nvidia | GPU별 정적 바인딩 | 높음 |
| 35 | 커널 부팅 파라미터 | 기본 | `intel_iommu=on` 또는 `amd_iommu=on` | 낮음 |
| 36 | IOMMU 그룹 | 해당 없음 | VFIO 격리 | 중간 |
| 37 | Kata 런타임 설치 | 없음 | containerd + kata-runtime | 중간 |
| 38 | KubeVirt 설치 | 없음 | kubevirt-operator, virt-handler | 중간 |
| 39 | NVIDIA vGPU 드라이버 | 없음 | Enterprise 라이선스 | 높음 |

### 8.9 모니터링 및 관측성

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 40 | 컨테이너 메트릭 | Docker stats | Kata: kata-agent / KubeVirt: libvirt | 중간 |
| 41 | GPU 메트릭 | nvidia-smi / DCGM | 게스트 내부 수집 필요 | 높음 |
| 42 | 로그 수집 | Docker logs | 런타임별 | 중간 |
| 43 | 커널 health check | Docker inspect | 런타임별 health probe | 중간 |
| 44 | 이벤트 파이프라인 | Redis pub/sub | 동일하나 소스 다름 | 낮음 |

### 8.10 Helm Chart 및 배포

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 45 | 다중 Agent DaemonSet | 단일 DaemonSet | 런타임별 DaemonSet | 중간 |
| 46 | 런타임 설치 dependency | 없음 | Kata/KubeVirt subchart | 낮음 |
| 47 | values.yaml 구조 | 단순 | `runtimeClasses` 구조 | 낮음 |
| 48 | feature flag | 없음 | 런타임별 enable/disable | 낮음 |

### 8.11 API / CLI / UI

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 49 | Session 생성 CLI | `./bai session create` | `--runtime-class` 옵션 | 낮음 |
| 50 | Capability discovery | 없음 | `./bai runtime list` | 낮음 |
| 51 | Web UI 세션 생성 | 런타임 선택 없음 | 드롭다운 + 시작 시간 표시 | 낮음 |
| 52 | Admin UI | 세션 목록 | runtime_class 컬럼 | 낮음 |

### 8.12 테스트 인프라

| # | 변경 항목 | 현재 | 필요 변경 | 난이도 |
|---|---|---|---|---|
| 53 | CI 환경 | Docker 기반 | Kata/KubeVirt 가능 노드 | 높음 |
| 54 | Agent 백엔드 테스트 | DockerAgent 통합 테스트 | 백엔드별 통합 테스트 | 중간 |
| 55 | End-to-end 시나리오 | 기본 세션 | 런타임별 시나리오 | 중간 |

---

## 9. 재사용 가능 vs 재작성 필요 요약

```
┌─── 재사용 (변경 없거나 미미) ────────────────────────────┐
│  - Manager API 기본 구조                                  │
│  - 사용자/권한/프로젝트 모델                              │
│  - vfolder 메타데이터 관리                                │
│  - Web UI 코어                                            │
│  - 이벤트 시스템 (Redis pub/sub)                          │
│  - etcd 서비스 디스커버리                                 │
│  - AppProxy (서비스 포트 노출)                            │
└────────────────────────────────────────────────────────────┘

┌─── 중간 수정 (추상화 레이어 추가) ────────────────────────┐
│  - Sokovan 스케줄러 (runtime-aware 라우팅)                │
│  - Session 생성 API (runtime_class 파라미터)              │
│  - Helm chart (다중 DaemonSet)                            │
│  - 커널 라이프사이클 상태 머신                            │
│  - 모니터링 파이프라인                                    │
└────────────────────────────────────────────────────────────┘

┌─── 대규모 재작성 / 신규 구현 ─────────────────────────────┐
│  - Agent 백엔드 (KataAgent, KubeVirtAgent 신규)           │
│  - 커널 생성 경로 (runtime-agnostic)                      │
│  - GPU 할당 로직 (런타임별 분기)                          │
│  - 분할 GPU 전략 (CUDA 훅 → vGPU/MIG)                     │
│  - 커널 통신 트랜스포트 (TCP → vsock/virtio-serial)       │
│  - 네트워크 플러그인 (Swarm → CNI 기반)                   │
│  - 스토리지 마운트 (bind → virtio-fs/PVC)                 │
│  - 이미지 빌드 파이프라인 (OCI + qcow2)                   │
└────────────────────────────────────────────────────────────┘

┌─── 인프라 레벨 변경 ──────────────────────────────────────┐
│  - 노드 풀 분리 (taint per runtime class)                 │
│  - GPU 드라이버 바인딩 (nvidia vs vfio-pci, GPU별)        │
│  - IOMMU 활성화, kernel boot params                       │
│  - Kata/KubeVirt 런타임 설치                              │
│  - NVIDIA vGPU 라이선스 도입 (선택)                       │
└────────────────────────────────────────────────────────────┘
```

---

## 10. 핵심 아키텍처 결정

전체 변경을 관통하는 몇 가지 근본 결정이 필요하다:

1. **Agent 백엔드 모델**: 런타임별 별도 백엔드 또는 단일 에이전트에 전략 패턴 주입.

2. **커널 개념 재정의**: "커널 = 컨테이너" 가정을 전 코드베이스에서 제거.

3. **분할 GPU의 운명**: VM 환경에서 동작하지 않는 CUDA 훅 기반 분할 GPU의 대안 결정 (NVIDIA vGPU, MIG, 또는 미지원).

4. **노드 공유 전략**: GPU별 바인딩으로 같은 노드에서 DooD와 VM 워크로드 혼합. 스케줄러가 GPU 단위로 추적.

5. **멀티 노드 세션 네트워킹 통합**: DooD는 Swarm overlay, Kata/KubeVirt는 CNI. 멀티 노드 세션은 같은 런타임 클래스 내에서만 가능.

---

## 11. 점진적 구현 로드맵

전체 재작성은 비현실적. 권장 단계적 접근:

**Phase 1 (3-6개월): 기반**
- Agent 백엔드 추상화 리팩터링
- API/CLI에 `runtime_class` 개념 도입
- 노드 풀 분리 인프라
- 스케줄러의 GPU별 runtime capability 추적

**Phase 2 (6-12개월): Kata 지원**
- `KataAgent` 구현 (K8s runtimeClass 활용)
- VFIO 기반 단일/멀티 GPU
- virtio-fs 스토리지
- 분할 GPU는 VM에서 **초기 미지원**

**Phase 3 (12-18개월): KubeVirt 지원**
- `KubeVirtAgent` 구현
- VM 이미지 빌드/배포 파이프라인
- vGPU 통합 (라이선스 보유 조직)
- Live migration 등 고급 기능

**Phase 4 (장기): VM에서 분할 GPU**
- NVIDIA vGPU 또는 MIG 기반 대안
- 런타임별 capability matrix 완성

---

## 12. 공수 추정

| 레이어 | 예상 노력 |
|---|---|
| Agent 추상화 + Kata 기본 | 3-4개월 (엔지니어 2-3명) |
| KubeVirt 기본 | 4-6개월 |
| GPU 할당 로직 통합 | 3-4개월 |
| 네트워킹 통합 | 2-3개월 |
| 스토리지 통합 | 2개월 |
| 이미지 파이프라인 | 2-3개월 |
| 스케줄러 / Manager | 2-3개월 |
| Helm / 인프라 | 1-2개월 |
| 테스트 / CI | 2개월 (지속) |
| **합계** | **약 12-18개월 (풀타임 2-3명)** |

이 추정은 병렬 작업과 팀의 K8s/Kata/KubeVirt 사전 전문성을 가정한다. 사전 전문성이 없으면 학습 곡선으로 30-50% 추가.

---

## 13. 결론 및 권고사항

### 요약

VM 기반 격리(Kata Containers, KubeVirt)는 보안 민감 배포에서 Backend.AI의 **필수 기능**이다 — 신뢰 불가 코드의 멀티테넌시 환경, 규제 준수 시나리오, 기밀 컴퓨팅 워크로드. 그러나 GPU 워크로드는 가용한 최적화 기법을 근본적으로 제약한다: Firecracker 사용 불가, VM 풀링은 GPU 낭비, Cold Start 시간이 GPU 하드웨어 초기화에 의해 좌우됨 (30초~수 분).

### 권고

1. **DooD를 기본으로**: 대다수 Backend.AI 워크로드(단일 테넌트, 신뢰 가능한 멀티 테넌트, 성능 중요 학습)에서 DooD가 옳은 선택. 기존 워크로드를 VM 기반 런타임으로 마이그레이션하지 말 것.

2. **VM 지원을 옵트인으로 추가**: VM 기반 런타임(Kata부터 시작)을 옵트인 대안으로 구현하고, 세션별로 `runtime_class` 파라미터로 선택. 사용자가 격리 vs 성능을 명시적으로 선택.

3. **현실적 UX 기대치 설정**: VM 기반 세션은 30초 이상의 cold start. 이는 본질적이지 버그가 아님. CLI/UI에서 명확히 전달.

4. **유연성을 위한 GPU별 바인딩**: 멀티 GPU를 가진 노드에서 GPU별 드라이버 바인딩을 지원하여 하이브리드 구성을 가능하게 함. 스케줄러가 GPU별로 runtime capability를 추적.

5. **단계적 롤아웃**: 기반 → Kata → KubeVirt → VM에서 분할 GPU. 한 번에 모든 것을 전달하려 하지 말 것.

6. **분할 GPU를 초기에 DooD 전용 기능으로 유지**. NVIDIA vGPU 도입은 고객 요구와 라이선스 예산에 따라.

7. **2-3명의 전담 엔지니어로 12-18개월의 집중적 엔지니어링 노력 계획**. 이는 상당한 투자이며, 구체적 고객 요구사항에 의해서만 정당화 가능.

### 결정 게이트

VM 런타임 지원에 착수하기 전에 확인:

- [ ] 구체적 고객 또는 규제 요구사항이 존재
- [ ] 고객이 cold start UX 트레이드오프 수용
- [ ] 고객이 초기 분할 GPU 부재 수용
- [ ] 엔지니어링 팀이 K8s + Kata/KubeVirt 전문성 보유 (또는 확보 예산)
- [ ] 지원 팀이 이중 런타임 운영 복잡도 처리 가능

이 중 하나라도 충족되지 않으면 충족될 때까지 VM 런타임 지원을 연기.

---

## 14. 참고 문헌

### Backend.AI 내부
1. K8s 컨트롤 플레인 + DooD 에이전트 아키텍처. `docs/reports/k8s-control-plane-dood-agent-architecture.ko.md`
2. Kata Containers 기능 동등성 분석. `docs/reports/kata-containers-feature-parity-analysis.md`
3. Backend.AI Agent Docker 구현. `src/ai/backend/agent/docker/agent.py`

### Kata Containers
4. Kata Containers Architecture. https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/README.md
5. Kata Containers Hypervisor Comparison. https://github.com/kata-containers/kata-containers/blob/main/docs/hypervisors.md
6. Confidential Containers Project. https://confidentialcontainers.org/

### KubeVirt
7. KubeVirt Documentation. https://kubevirt.io/user-guide/
8. KubeVirt GPU Passthrough. https://kubevirt.io/user-guide/virtual_machines/host-devices/

### NVIDIA Virtualization
9. NVIDIA vGPU Documentation. https://docs.nvidia.com/grid/
10. NVIDIA MIG User Guide. https://docs.nvidia.com/datacenter/tesla/mig-user-guide/
11. NVIDIA Container Toolkit. https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/

### Linux Virtualization
12. VFIO Documentation. https://docs.kernel.org/driver-api/vfio.html
13. Firecracker (no VFIO). https://github.com/firecracker-microvm/firecracker/blob/main/docs/device-api.md
14. Cloud Hypervisor. https://www.cloudhypervisor.org/
