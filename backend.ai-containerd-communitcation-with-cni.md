# Backend.AI containerd 컨테이너 네트워킹 전략

## 1. 배경

Backend.AI containerd 기반 agent에서 컨테이너는 **K8s Pod가 아닌 containerd 워크로드로 직접 생성**된다. 이로 인해 표준 K8s 네트워킹(NetworkPolicy 등) 위에 자동으로 얹어지지 않는다.

이 문서의 목표는 **K8s 정책 enforcement가 아니라 통신 편의성과 성능**을 만족하는 네트워킹 구조를 정리하는 것이다.

## 2. 요구사항

| # | 요구사항 | 용도 |
|---|---|---|
| R1 | containerd로 뜬 BAI 컨테이너끼리 overlay 통신이 가능해야 함 | 다중 노드 학습 |
| R2 | K8s Pod에서 BAI 컨테이너로 접속할 때 hop 최소, 대역폭 최대 | 추론 |

## 3. 핵심 원칙

> **양쪽 워크로드(BAI 컨테이너, K8s Pod)가 동일한 네트워크 fabric 또는 직접 라우팅 가능한 fabric에 있어야 R2의 "hop 없이"가 성립한다.**

서로 다른 fabric에 있으면 둘 사이를 잇는 gateway/proxy가 끼게 되어 hop이 늘어나고 대역폭이 깎인다.

## 4. 추천 구조: Dual-attach (Multus 스타일)

학습용과 추론용은 트래픽 특성이 다르다. 단일 인터페이스로 묶지 말고 **컨테이너에 두 개의 네트워크 인터페이스**를 부여한다.

```
[BAI agent host]
 │
 ├─ eth0 (관리/제어)
 │
 ├─ [BAI 학습 컨테이너]
 │    └─ eth0 (Net A: 학습 overlay)
 │
 ├─ [BAI 추론 endpoint 컨테이너]
 │    └─ eth0 (Net B: K8s 공유 fabric)
 │
 └─ [BAI 학습+서빙 동시 컨테이너]
      ├─ eth0 (Net A)
      └─ eth1 (Net B)
```

- **Net A**: BAI 컨테이너끼리만 참여하는 학습 전용 네트워크
- **Net B**: K8s Pod와 같은 fabric에 들어가는 서빙용 네트워크

다중 인터페이스 부여는 CRI 단계에서 직접 CNI 호출을 두 번 하거나, Multus-CNI를 도입하거나, 자체 CNI chaining으로 구현 가능.

## 5. Net A (학습 overlay) 옵션

### A-1. 자체 vxlan 또는 Flannel vxlan

학습 호스트들끼리 가벼운 L3 overlay를 만든다.

**필요한 것:**
- vxlan 인터페이스 관리 도구 (택 1)
  - `flanneld` + etcd 백엔드
  - 자체 스크립트로 `ip link add type vxlan`
- CNI plugin: `flannel` 또는 `bridge` plugin + 사전 셋업한 vxlan
- IPAM: 호스트별 서브넷 분배 정책 (ex: 호스트 N → `10.244.N.0/24`)
- BAI agent가 컨테이너 생성 시 CNI 호출 코드

**특성:**
- 운영 부담: 작음
- 성능: 중간 (vxlan encap ~5% 손실, MTU 50바이트 차감)
- 다중 노드 GPU 학습 NCCL 트래픽엔 적합하지 않을 수 있음

### A-2. RDMA (RoCE v2 / InfiniBand) + SR-IOV

GPU production 학습 수준의 대역폭/지연이 필요할 때.

**필요한 것:**
- 하드웨어
  - RDMA NIC (Mellanox ConnectX 등)
  - RoCE라면 lossless ethernet (PFC/ECN 활성화된 스위치)
  - InfiniBand라면 IB 스위치
- 호스트 소프트웨어
  - 커널 RDMA stack (`rdma-core`, `MLNX_OFED`)
  - SR-IOV VF pre-create
  - IOMMU on, 적절한 BIOS 설정
- CNI plugin
  - `sriov-cni` (VF 할당)
  - `rdma-cni` (RDMA device 컨테이너 노출)
  - 보통 Multus chained
- 컨테이너
  - `/dev/infiniband/*` 노출
  - `IPC_LOCK` capability
  - GPUDirect RDMA 사용 시 GPU 드라이버 + nv_peer_mem 모듈

**특성:**
- 운영 부담: 큼
- 성능: 최상 (line rate, GPUDirect로 GPU memory ↔ NIC 직접)
- VF 수 한계 존재 (NIC당 보통 64개 정도)

## 6. Net B (K8s와 공유 fabric) 옵션

K8s 측이 어떤 CNI를 쓰는지가 절반을 결정한다.

### B-1. Cilium native routing + BGP (encap 없음)

**전제:** K8s가 Cilium을 native routing 모드로 운영하고 BGP로 Pod CIDR을 announce.

**필요한 것:**
- K8s 측
  - Cilium 설정: `routing-mode: native`, `ipam: cluster-pool` 또는 동등
  - Cilium BGP control plane 또는 외부 BGP daemon (FRR, MetalLB BGP)
- BAI 호스트 측
  - BGP daemon (FRR, GoBGP, BIRD)
  - 호스트별 컨테이너 CIDR 할당
  - CNI plugin: `bridge` + `host-local` IPAM (단순)
  - 호스트 라우팅 테이블 정리 + 컨테이너 CIDR을 BGP로 announce
- 네트워크 인프라
  - BGP-aware ToR/Leaf 스위치, 또는 Linux router와 peering
  - 동일 AS 내 iBGP 또는 eBGP 설계

**특성:**
- 성능: 최상 (encap 0, 순수 L3 라우팅, ECMP 가능)
- 운영: 네트워크팀 협조 필수
- 정책: 별도 (Cilium policy는 BAI 컨테이너에 자동 적용 안 됨)

### B-2. Cilium vxlan/geneve fabric에 BAI 호스트 join

**전제:** K8s가 Cilium을 overlay 모드로 운영. BAI 호스트도 같은 overlay에 끼워 넣는다.

**필요한 것:**
- BAI 호스트에 cilium-agent 실행
  - 옵션 a) 호스트를 K8s 노드로 등록(가벼운 kubelet 또는 슬림 VK) 후 cilium DaemonSet
  - 옵션 b) `CiliumExternalWorkload` CRD로 외부 워크로드로 참여
- BAI 컨테이너의 endpoint 등록
  - `cilium-cni`를 직접 호출하거나
  - cilium-agent의 endpoint API (`PUT /v1/endpoint/`)에 직접 등록
- Identity 메타데이터
  - BAI agent가 컨테이너에 부여할 라벨(session_id, user, kernel_type 등) 정의
  - cilium-agent가 라벨 → identity 매핑하도록 K8s 측에 CRD 또는 외부 라벨 source 구성
- 키/암호화
  - vxlan tunnel key, IPSec/WireGuard 사용 시 키 공유

**특성:**
- 성능: 중상 (vxlan encap)
- 운영: 큼 (Cilium 자체 운영 부담 + 외부 워크로드 통합 부담)
- 정책: Cilium NetworkPolicy를 그대로 활용 가능 (덤)

### B-3. Flannel vxlan 공유 (가장 가벼움)

**전제:** K8s가 Flannel vxlan을 사용하거나, 신규 환경에서 단순함을 우선시.

**필요한 것:**
- BAI 호스트에 `flanneld` 실행
- K8s와 동일한 backend
  - etcd backend면 같은 etcd 클러스터
  - Kubernetes API backend면 같은 클러스터에 ServiceAccount로 접근
- 호스트별 subnet 할당 정책 (Flannel이 자동으로 처리)
- CNI plugin: `flannel` (`/opt/cni/bin/flannel`) + `bridge`
- BAI agent의 CNI 호출 시 flannel conflist 사용

**특성:**
- 성능: 중간 (vxlan encap)
- 운영: 작음
- 정책: 없음 (Flannel은 정책 미지원, L3 연결만)

### B-4. Macvlan / IPvlan (LAN 직결)

**전제:** BAI 호스트와 K8s 노드가 동일 L2 또는 L3 라우팅 가능한 LAN에 있고, IP 대역 여유가 있음.

**필요한 것:**
- 네트워크 인프라
  - BAI/K8s 노드들이 같은 L2 segment (또는 L3 routable한 동일 sub-pool)
  - 스위치에서 promisc 허용 (macvlan) 또는 IPvlan L3 모드 사용
- IPAM
  - 충돌 없는 컨테이너 IP 풀
  - DHCP 사용 시 DHCP 서버 + `dhcp` IPAM plugin
  - host-local 분리 시 호스트별 sub-pool 사전 분배
- CNI plugin
  - `macvlan` 또는 `ipvlan`
  - K8s 측: Multus로 macvlan/ipvlan attachment 추가 (`NetworkAttachmentDefinition`)
- 양쪽이 동일한 macvlan/ipvlan 네트워크에 attach

**특성:**
- 성능: 최상 (NIC 직결, 호스트 bridge 거의 안 거침)
- 운영: 작음
- 한계: IP 관리 부담, L2 제약, 호스트 ↔ 자기 macvlan 컨테이너 간 통신은 별도 트릭 필요

### B-5. SR-IOV (전용 NIC VF)

**전제:** 추론 페이로드가 매우 크거나(LLM streaming 등) 추론 컨테이너 수가 NIC VF 한계 안에 들어옴.

**필요한 것:**
- 하드웨어: SR-IOV 지원 NIC, 충분한 VF 수
- 호스트: BIOS에서 SR-IOV/VT-d 활성화, VF pre-create
- CNI plugin
  - `sriov-cni`
  - `sriov-network-device-plugin` (K8s 노드 자원 광고용)
- K8s 측: Multus + `SriovNetwork` CRD
- BAI 측: 같은 VF 풀에서 할당받도록 device-plugin 또는 직접 할당 로직

**특성:**
- 성능: 최상 (PF 우회, 거의 line rate, kernel bypass with DPDK 가능)
- 운영: 큼 (HW 종속, capacity planning 필요)
- VF 수 한계로 컨테이너 수 제한

## 7. 옵션 비교 요약

### Net A (학습)

| 옵션 | 성능 | HW 요구 | 운영 부담 | 추천 상황 |
|---|---|---|---|---|
| A-1 vxlan | 중 | 일반 NIC | 작음 | 학생/연구실, 소규모 |
| A-2 RDMA+SR-IOV | 최상 | RDMA NIC | 큼 | Production GPU 학습 |

### Net B (K8s 공유)

| 옵션 | 성능 | 전제 | 운영 부담 |
|---|---|---|---|
| B-1 Cilium native + BGP | 최상 | K8s가 Cilium native routing, BGP 환경 | 중-큼 |
| B-2 Cilium overlay join | 중상 | K8s가 Cilium overlay | 큼 |
| B-3 Flannel 공유 | 중 | K8s가 Flannel 또는 신규 환경 | 작음 |
| B-4 Macvlan | 최상 | 동일 LAN, IP 여유 | 작음 |
| B-5 SR-IOV | 최상 | SR-IOV NIC | 큼 |

## 8. 결정에 필요한 입력

다음 항목이 정해지면 구체 조합을 확정할 수 있다.

1. **K8s 측 현재 CNI**: Cilium / Calico / Flannel / 기타
2. **K8s가 overlay 모드인지 native routing 모드인지**
3. **학습 워크로드 규모**: 단일 노드인지 다중 노드 GPU인지, NCCL/MPI 사용 여부
4. **추론 트래픽 특성**: 응답 페이로드 크기, 동시 연결 수, 지연 요구
5. **BAI 호스트와 K8s 노드의 네트워크 위치**: 동일 L2인지, 라우팅 hop이 있는지
6. **하드웨어 가용성**: RDMA NIC, SR-IOV 가능 NIC 보유 여부
7. **네트워크팀 협조 여부**: BGP/스위치 설정 변경 가능 여부

## 9. 일반적인 조합별 권장

### 9-1. 학생/연구실, K8s Cilium 환경, 일반 GPU
- Net A: A-1 (자체 vxlan)
- Net B: B-2 또는 B-3
- Multus로 dual-attach

### 9-2. Production 학습 + 추론 혼재, 충분한 인프라
- Net A: A-2 (RDMA+SR-IOV)
- Net B: B-1 (Cilium native + BGP) 또는 B-5 (SR-IOV)
- 인터페이스 분리, 학습 NIC와 서빙 NIC를 물리적으로 다른 NIC에 둠

### 9-3. 단순함 우선, 정책 enforcement 불필요
- Net A: A-1 (Flannel vxlan)
- Net B: B-3 (같은 Flannel) 또는 B-4 (macvlan)
- 사실상 단일 fabric로 통합 가능

### 9-4. 추론 대역폭이 critical (LLM 서빙 등)
- Net A: 별도 (학습 워크로드 분리)
- Net B: B-4 (macvlan) 또는 B-5 (SR-IOV)
- 호스트 커널 스택을 가능한 한 우회

## 10. 구현 시 BAI agent 변경 포인트

선택한 조합과 무관하게 BAI containerd agent에 공통적으로 필요한 작업:

1. **CNI 호출 통합**
   - PodSandboxConfig 생성 시 CRI runtime이 자동 호출하는 CNI conflist 준비
   - 또는 sandbox 생성 후 agent가 직접 CNI plugin 호출
2. **다중 인터페이스 지원**
   - Multus 채택 또는 자체 CNI chaining
   - 컨테이너 spec에서 어떤 net에 attach할지 선언적으로 표현
3. **IPAM 정책**
   - 호스트별 subnet 분배 또는 외부 IPAM(DHCP, Calico IPAM 등) 연동
4. **메타데이터 라벨링**
   - Cilium 등 정책 fabric을 쓸 경우 식별 라벨(session_id, user, image, kernel_type) 부여 규칙
5. **lifecycle 정리**
   - 컨테이너 종료 시 CNI DEL, IP 반환, endpoint 등록 해제 보장
6. **장애/재시작 처리**
   - agent 재시작 후 기존 컨테이너의 네트워크 상태 reconcile
