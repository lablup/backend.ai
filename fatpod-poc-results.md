# Fat-Pod / hostNetwork 중첩-CinC PoC — 실험 결과 종합

> 검증 일자: 2026-08-05
> 대상 가설: Backend.AI 에이전트를 **privileged hostNetwork pod**로 패키징하고 커널을 그 안의
> **중첩 컨테이너(CinC, containerd-in-pod)**로 실행하면, 네트워크가 클러스터 CNI를 우회하고
> **우리 VXLAN을 VTEP=노드 IP로 물리망 위에서 single-encap**으로 돌 때 "베어메탈 BEP-1062"와
> 동일하게 동작한다.
>
> 체크리스트 원본: `fatpod-hostnetwork-poc.md` (각 항목 PASS/FAIL/측정값은 그 문서의 표에 기록).
> 이 문서는 실험 단위의 결과 요약.

**최종 결론: 가설 성립 확인 — hostNetwork/containerd+privnet/중첩-CinC 노선 채택 가능.**

> **핵심 구분:** 세션끼리 크로스노드 통신이 되냐를 가르는 건 **hostNetwork 여부가 아니라
> `containerd+privnet`(오버레이 있음) vs `docker`(오버레이 없음)** 이다.
> - docker 모드, **오버레이 없이**(실험 3): ❌ 두 독립 세션이 docker0 기본 172.17.0.2로 충돌. 단 **Docker Swarm overlay면 크로스노드 가능**(실험 9)
> - containerd+privnet, **pod network**(실험 4): ✅ 크로스노드 20/20 (hostNetwork 아님에도 통신됨)
> - containerd+privnet, **hostNetwork**(실험 5): ✅ 통신 + VTEP=노드 IP(베어메탈 형태)
>
> 즉 hostNetwork는 "통신 성립"의 조건이 아니라, PoC 가설의 "VTEP=노드 IP / 물리 LAN single-encap"
> 형태를 정확히 재현하기 위한 것(성능도 pod-net 0.35 → hostNet 0.51 Gbit/s로 상승).

---

## 테스트 환경

| 노드 | 호스트명 | 역할 | 비고 |
|---|---|---|---|
| 192.168.0.21 | charsyam-tfx | k8s control-plane | clean, Wi-Fi(wlo1) |
| 192.168.0.156 | ser8 | worker | dev agent i-node2 공존 |
| 192.168.0.104 | charsyam-nvidia | worker | GPU(RTX 4070) + dev 스택(manager/etcd/agent i-node1) |

- k8s v1.34.1, containerd 2.2.x, CNI = **flannel host-gw**(무캡슐화)
- fatpod 이미지: ubuntu 24.04 + docker-ce/containerd, repo·venv·pyenv는 hostPath bind-mount

---

## 실험 0. 인프라 구축

| 항목 | 결과 |
|---|---|
| 3노드 k8s 클러스터 | ✅ 모두 Ready |
| CNI 선택 | **flannel host-gw** → landmine #1(우리 VXLAN 4789 vs flannel 4789) 사전 제거. 3노드 모두 UDP 4789 리스너 0 |
| dev 스택 무중단 | ✅ .104 kubelet 포트 10250→11250(appproxy 10205-10300 회피), NodePort 32000-32767, swap `failSwapOn:false` |
| landmine "MTU 역전" | 해당 없음 — host-gw라 underlay=노드 물리 MTU 1500 |

---

## 실험 1. 0·1단계 게이트 (특권 pod admit / 권한)

| 단계 | 결과 |
|---|---|
| 0단계 게이트 | ✅ PASS — PSA=privileged, hostNetwork+hostPID+privileged pod admit, Gatekeeper/Kyverno/PSP 없음 |
| 1단계 G (SecurityContext/caps) | ✅ PASS — hostNetwork(netns=노드 netns 동일), hostPID, NET_ADMIN(vxlan/bridge), SYS_ADMIN(nsenter), NET_RAW(iptables), seccomp Unconfined |
| 1단계 H (host 마운트) | ✅ `/dev/nvidia*` 9개, `/sys` rw, `/lib/modules`, `/etc/cdi/nvidia.yaml` |
| 1단계 J (커널/노드) | ✅ ip_forward=1, vxlan/bridge/veth/nf_conntrack 로드, NAT는 nftables 백엔드 |
| 1단계 K (RBAC) | 기본 SA는 pod create/delete 불가(최소권한); pause-pod 하이브리드 시 전용 SA 필요 |

---

## 실험 2. 특권 분석 — "published 포트 노출"과 "노드 장악"은 별개 축

세 축이 서로 독립임을 실측으로 분리:

| 축 | 원인 | 실측 |
|---|---|---|
| published 포트 **노출** | flannel 라우팅 + NetworkPolicy 없음 | **비특권·타 namespace** pod도 세션 포트 도달 (권한 무관) |
| 포트를 **여는** 능력 | `NET_ADMIN` (전체 privileged 불필요) | 비특권 iptables DNAT `Permission denied`, NET_ADMIN만 추가 시 성공 |
| **노드 장악** | `privileged` + `hostPID` | `/proc/1/root`로 노드 FS·`/etc/kubernetes/kubelet.conf` 열람 |

**privnet의 SYS_ADMIN:** `network/privnet/__main__.py`가 4개 캡(NET_ADMIN/SYS_ADMIN/SYS_PTRACE/DAC_READ_SEARCH) 선언.
`native_attacher.py`가 veth를 netns로 옮긴 뒤(**NET_ADMIN**) `nsenter`(setns)로 진입해 IP/MAC/route 설정(**SYS_ADMIN**).
→ **현 코드로는 privnet에서 SYS_ADMIN 제거 불가.** 제거하려면 in-netns 설정을 netnsid-타깃 netlink(pyroute2)로 재구현 필요.
단 **fatpod가 이미 privileged 신뢰 경계**라, 이 하드닝은 fatpod 노선과 직교(fatpod 안에선 문제 아님).

---

## 실험 3. docker 모드 — 오버레이 없이는 크로스노드 불가 (Swarm이면 됨, 실험 9 참조)

> **정정(실험 9 반영):** 아래는 **오버레이 드라이버(Docker Swarm)를 세팅하지 않고**, 두 노드에 **독립된
> SINGLE_NODE 세션 2개**를 띄워 서로 통신을 시도한 케이스다. docker 모드가 멀티노드를 **근본적으로 못 하는 게 아니다** —
> docker 백엔드의 멀티노드 오버레이는 **Docker Swarm**이며(매니저가 `overlay` 드라이버로 페어링), **Swarm을 세팅하면
> 크로스노드가 된다**(실험 9에서 c1↔c2 양방향 실증). 이 실험은 "오버레이 없으면 왜 안 되는가"를 보여줄 뿐이다.

| 결과 | 내용 |
|---|---|
| ❌ 오버레이 없는 크로스노드 통신 | 독립 SINGLE_NODE 세션 2개가 각자 docker0 기본(`172.17.0.2`)을 받아 충돌 → 상대 "IP" 접속 시 자기 자신에 연결. (애초에 별개 세션이라 통신 안 되는 게 정상이기도 함) |
| ✅ 단일 세션 정상 | 세션 생성·published port·AppProxy 동작 |
| ✅ published port 크로스노드 | 상대 **pod IP**의 published 포트는 flannel로 도달 |
| **정정된 결론** | docker 모드 멀티노드 크로스노드는 **Docker Swarm overlay로 가능**(실험 9). 단 Swarm은 매니저 노드/쿼럼·호스트 docker 종속을 요구 → fatpod 모델엔 containerd+privnet이 더 적합(실험 9의 비교표). "docker=불가"가 아니라 "docker=Swarm 필요, 그리고 그 대가가 큼" |

---

## 실험 4. containerd+privnet, pod network (VTEP=pod IP)

fatpod 안에 containerd 데몬 + privnet(root, 전체 캡) + agent(containerd 모드) 재구성.
매니저는 `backend=containerd` 발행을 보고 자동으로 `cni` 드라이버 선택(`network/pairing.py`).

| 항목 | 결과 |
|---|---|
| MULTI_NODE 세션 배치 | ✅ 두 fatpod에 하나씩 (reserved-cpu로 cpu=2 캡→분산 강제) main1@.104 / sub1@.156 |
| 크로스노드 CinC↔CinC | ✅ 왕복 **20/20 = 100%** — 오버레이 IP(10.128.7.x)·`/etc/hosts` 이름 둘 다 |
| /etc/hosts 피어 해석 | ✅ 두 커널에 `10.128.7.1 sub1` + `10.128.7.2 main1`, `BACKENDAI_CLUSTER_HOSTS=sub1,main1` |
| MTU 무결성 | ✅ `baimulti0` MTU **1450**(=1500-50), 500MB 전송 완료, 드롭 0 |
| RTT | ✅ p50 **0.395ms**, p99 0.53ms |
| 데이터플레인 | VXLAN VNI 4103 on **eth0**, FDB→피어 **pod IP**(10.244.x), flannel host-gw가 4789/UDP 라우팅 |

---

## 실험 5. containerd+privnet, **hostNetwork (VTEP=노드 IP)** — PoC 가설 원형

fatpod를 `hostNetwork: true`로. 호스트 dev agent와의 충돌은 포트·pool 분리로 회피.

| 항목 | 결과 |
|---|---|
| agent addr / VTEP | ✅ **노드 IP** `192.168.0.104:6031` / VTEP `192.168.0.104`,`192.168.0.156` |
| VXLAN 디바이스 | ✅ VNI 4103 on **물리 uplink enp4s0**(pod-net 땐 eth0), dstport 4789 |
| FDB | ✅ 피어 오버레이 MAC → **피어 노드 IP 192.168.0.156** = **물리 LAN 직접 single-encap(flannel 무관)** = 베어메탈 BEP-1062 |
| 크로스노드 양방향 | ✅ main1↔sub1 각 **20/20 = 100%** (클러스터 호스트명으로) |
| MTU 무결성 | ✅ MTU 1450, 드롭 0, 300MB 전송 (0.51 Gbit/s — 물리 직결이라 pod-net 0.35보다 빠름) |
| 충돌 회피 설정 | rpc 6031·svc 6033·sock 6037·**aiomonitor 38700/39700**·port-range 31100-31600·LOCAL pool 172.31/16 |

> aiomonitor 포트(기본 38200/39200) 충돌이 첫 기동 실패의 원인이었음 — hostNetwork라 127.0.0.1도 호스트와 공유되기 때문.

---

## 실험 6. backend.ai 기본 동작 전수 검증 (hostNetwork 세션 기준)

| 동작 | 결과 |
|---|---|
| API 연결성 (domain/user/agent/image/session/rg) | ✅ |
| agent 헬스/하트비트/리소스 회계 | ✅ ALIVE, cpu 2/2 |
| 세션 create / get / logs | ✅ |
| published port DNAT (노드 IP) | ✅ 192.168.0.104:31100 OPEN, DNAT→172.31.0.2:2200 |
| 서비스(jupyter) 시작 | ✅ HTTP 302 |
| AppProxy end-to-end | ✅ add code 200, 프록시 HTTP 308(auth), 타 노드에서도 도달 |
| **코드 실행** | ✅ python 3.13.2, 6*7=42, **`nproc=2`(리소스 제한 CinC까지 정확 적용)** |
| vfolder | ✅ my-search |
| **terminate teardown** | ✅ 커널 0·VXLAN 0·DNAT 0·agent cpu 회수 — **완전 정리** |

---

## 실험 7. GPU 주입 (2단계 C) — .104 단일 GPU

privileged fatpod에 호스트 nvidia device 노드 + 유저스페이스를 스테이징하고 cuda_open으로 GPU 탐지 → 세션 CinC에 CDI 주입.

| 항목 | 결과 |
|---|---|
| fatpod GPU 접근 | ✅ fatpod `nvidia-smi` = RTX 4070, 드라이버 580.65.06 |
| agent GPU 탐지 | ✅ cuda_open이 GPU 탐지 → **cuda.device=1 광고** |
| **CinC GPU 주입** | ✅ 커널 컨테이너 `nvidia-smi` = RTX 4070/CUDA 13.0, device 노드 전부 주입 |
| **실연산 가능** | ✅ CUDA 드라이버 API `cuInit`+`cuDeviceGetCount=1` |
| 주입 경로 | `/etc/cdi/nvidia.yaml` → agent가 OCI spec에 device/mount/hook 주입(runtime/cdi.py), `NVIDIA_VISIBLE_DEVICES=void`(CDI 표식) |

### containerd vs docker 모드 GPU (둘 다 검증)

| 모드 | 세션 실행 | GPU 주입 경로 | CinC nvidia-smi | libcuda / libcudart | 실제 연산 | 세션 컨테이너 위치 |
|---|---|---|---|---|---|---|
| **containerd** | containerd | **CDI**(agent가 `runtime/cdi.py`로 OCI spec에 직접 주입) | ✅ RTX 4070/CUDA13 | libcuda ✅ / libcudart ❌ | ✅ vector-add 1M PASS | containerd(docker 컨테이너 **0개**) |
| **docker** | docker | nvidia docker 런타임(`HostConfig.DeviceRequests` Driver=nvidia) | ✅ RTX 4070 | libcuda ✅ / libcudart ❌ | ✅ vector-add 1M PASS | docker(커널+relay 2개) |

→ **두 모드 모두 CinC에서 실제 GPU 연산 확인**: `nvidia-smi` + **driver-API vector-add(1M elems, c=a+b 검증 PASS)**. 초기엔 `cuDeviceGetCount=1`만 봤으나, 재검증에서 실 커널 실행까지 확인.

> **libcudart 주입 오해 정정 (실측):** **CDI도 nvidia-runtime도 컨테이너에 `libcudart`를 넣지 않는다.** 둘 다 nvidia-container-toolkit이 만든 것으로 **드라이버 유저스페이스(`libcuda.so`, NVML)만** 주입한다. 위 표처럼 두 모드 CinC 모두 `libcuda.so.1`은 있고 `libcudart`는 **없는데도** driver-API 연산이 돌았다. `libcudart`는 CUDA **툴킷** 구성요소라 **이미지/앱**이 갖는다(PyTorch/TF는 자체 번들). 이 점에서 CDI ≡ nvidia-runtime. (아래 "libcudart 필요"는 컨테이너가 아니라 **에이전트 cuda_open의 device count**용 — `plugin.py:157 libcudart.get_device_count()` — 이라 fatpod에 스테이징한 것이며 모드 무관.)

### 발견한 이슈 2가지 (성격 구분)

| 요구 | 정체 | 버그 여부 |
|---|---|---|
| cuda_open이 docker+nvidia런타임을 요구 | **backend.ai 소스**(`accelerator/cuda_open/plugin.py`의 `init`) | ✅ backend.ai 버그성 커플링 — containerd 모드인데도 `aiodocker.Docker()`로 docker에 nvidia 런타임을 확인. 이 체크만 컨테이너드 모드에서 스킵하면 docker 없이 동작 |
| libcudart 필요 | NVIDIA CUDA 툴킷 **외부 라이브러리** | ❌ 버그 아님 — GPU 개수 세는 정당한 의존성. 모든 모드 공통 |

> **핵심:** containerd 모드에서 GPU 세션은 containerd+CDI로 실제로 실행됨(docker 컨테이너 0개가 증거). docker가 필요했던 건 순전히 cuda_open `init`의 레거시 게이트 때문이지 containerd가 GPU를 못 다뤄서가 아님. **프로덕션 fatpod 이미지엔 libcudart(CUDA runtime) + nvidia userspace를 포함해야 하고, cuda_open의 docker 게이트는 containerd 모드에서 스킵하도록 고치는 게 맞음.**

**미완:** device-plugin 정식 경로(현재는 hostPath 직접 주입), 멀티-GPU NCCL(단일 GPU HW 제약), fractional/MIG.

## 실험 8. NVLink / NCCL 분석 (이 랙에선 실측 불가, 구조 분석 + NIC 실측)

.104은 단일 GPU(RTX 4070 Laptop, NVLink 없음)라 NVLink/NCCL 실측 불가. 대신 **구조적 영향**과
**실측 가능한 언더레이 조건**을 정리.

### 실측된 언더레이 조건 (inter-node NCCL 대역폭 좌우)

| 항목 | .104 enp4s0 / .156 enp1s0 |
|---|---|
| VXLAN 터널 오프로드 (`tx-udp_tnl-segmentation`) | **off [fixed]** — 하드웨어 불가 |
| caps.py 발행 `tunnel_offload` | **false** (위를 정확히 탐지) |
| NIC 속도 | **1 GbE** |

→ 이 랙은 오프로드 없는 1GbE라 inter-node NCCL busbw 측정 자체가 무의미(라인레이트 ~1Gbit + CPU encap).

### 핵심: "중첩 구조"는 NVLink/NCCL을 깨뜨리지 않음. 신경 쓸 지점은 따로 있음

| 항목 | 신경 정도 | 근거 |
|---|---|---|
| 중첩(CinC)이 NVLink/NCCL 깨뜨림? | ✅ 무관 | NVLink=하드웨어 DMA(컨테이너 경계 안 거침), NCCL=오버레이 정상이면 그 위에서 동작 |
| NVLink 디바이스 주입 | ⚠️ 챙겨야 | 멀티-GPU는 **전부 같은 CinC**에 주입해야 P2P. NVSwitch(A100/H100)면 호스트 `nvidia-fabricmanager`+`/dev/nvidia-caps` 주입 필수(안 하면 깨짐) |
| **NCCL inter-node 인터페이스 선택** | 🔴 **P0 미검증** | CinC에 `baimulti0`(오버레이)+LOCAL 두 인터페이스 → NCCL이 LOCAL을 고르면 rank 연결 실패=**hang**. `NCCL_SOCKET_IFNAME=baimulti0` 주입/보장 필요 |
| NCCL 성능(busbw) | 🟡 하드웨어 문제 | fatpod 구조가 아니라 NIC 속도/오프로드·NVLink가 좌우. 이 랙(1GbE, offload 없음)으론 측정 무의미 |

### intra-node vs inter-node

- **intra-node(NVLink)**: fatpod = 베어메탈. 중첩이 하드웨어 P2P를 안 건드림. GPU device 노드+`nvidia-caps`만 CinC에 주입되면 동작.
- **inter-node(NCCL)**: 우리 VXLAN 오버레이(`baimulti0`)를 탐. **전제조건은 이미 검증됨**(크로스노드 도달 20/20, MTU 1450 무결=블랙홀 없음, `/etc/hosts` 피어 해석). 남은 건 ① 인터페이스 선택(hang 방지, P0) ② 성능(하드웨어) ③ RDMA/GPUDirect(IB/RoCE over VXLAN, 고급).

> **single-encap의 정당성:** offload 안 되는 NIC일수록 encap 겹수가 CPU 비용으로 직결 → hostNetwork single-encap(VXLAN 한 겹)이 pod-network double-encap보다 NCCL 대역폭에서 유리. PoC가 hostNetwork를 고집한 근거가 여기서 확인됨.

**결론:** "fatpod라서 NVLink/NCCL이 안 되나"는 걱정 불필요(구조 무관). 단 **NCCL 인터페이스 선택(hang 방지)은 P0로 남고**, NVSwitch 디바이스 주입은 배포 시 필수. 성능은 이 랙에선 측정 불가.

## 실험 9. docker 모드 멀티노드 데이터플레인 (Docker Swarm overlay)

containerd 모드의 멀티노드(실험 4/5, privnet VXLAN)에 대응하는 docker 모드를 검증. docker 백엔드는
매니저가 `overlay` 드라이버=**Docker Swarm**으로 페어링(`network/pairing.py`, `network/overlay.py`).
정식 세션 경로는 매니저가 **호스트 docker에 `swarm init`**을 요구 → dev 스택 침습적이라, 데이터플레인만
**중첩 docker(dind) 2개를 직접 Swarm으로 묶어** 비침습 검증(dind-1@.104 / dind-2@.156).

| 항목 | 결과 |
|---|---|
| Swarm 형성 | ✅ dind-1(leader)+dind-2(worker), pod IP advertise |
| overlay 네트워크 | ✅ `--attachable` overlay(10.200.0.0/24) |
| **크로스노드 컨테이너 통신** | ✅ c1(.104 10.200.0.11) ↔ c2(.156 10.200.0.12) **양방향 REACHABLE** |
| encap | VXLAN **4789**, overlay MTU **1450**, outer=dind pod IP → flannel host-gw = **single-encap** |

### containerd(privnet) vs docker(Swarm) 멀티노드 비교

| | containerd (privnet, BEP-1062) | docker (Swarm overlay) |
|---|---|---|
| 크로스노드 통신 | ✅ (실험 4/5) | ✅ (실험 9) |
| encap / MTU | VXLAN 4789 / 1450, single-encap over host-gw | **동일** — VXLAN 4789 / 1450 |
| 관리 주체 | **우리 privnet** (per-agent, 자기완결) | **Docker Swarm** (cluster-wide, 불투명) |
| 세션 경로 요건 | agent+privnet, **호스트 독립** | 매니저가 **호스트 docker에 swarm init** 필요(침습적) |
| VTEP | pod IP / 노드 IP(hostNetwork) | advertise-addr(pod IP / 노드 IP) |
| 세션별 격리 제어 | 세션별 VNI/LOCAL FORWARD를 **우리가 제어** | Swarm이 네트워크별 관리(backend.ai 제어 밖) |

### 4789에 관한 정정: 포트 공유 ≠ 자동 충돌, 진짜 블로커는 정책/방화벽

Docker Swarm도 privnet도 VXLAN 4789를 쓰지만, **같은 포트라고 자동 충돌이 아니다** — 실측: 같은 netns에서
VNI가 다른 VXLAN 2개(vxtest0 VNI100 / vxtest1 VNI200)가 4789로 **공존**(커널이 VNI로 디먹싱). 둘 다 커널
vxlan 드라이버라 공유 소켓+VNI 디먹싱을 타고, Swarm은 보통 별도 sandbox netns라 포트 공간도 분리됨.

- 포트 4789에서 실제 위험: **VNI 겹침**(→ misdelivery, 단 VNI 할당으로 회피) 또는 드문 배타적 bind 구현.
- **현실적 블로커는 정책/방화벽**: `NetworkPolicy`(Calico/Cilium이 default-deny면 pod 간 UDP 4789 드롭) 또는
  EKS `Security Group`/NACL이 UDP 4789 미허용 시 오버레이 끊김. → **정책 클러스터/EKS에선 UDP 4789 허용이 필수 확인 항목.**
- 이 테스트 클러스터가 통한 이유: flannel host-gw라 4789를 CNI가 안 씀 + **NetworkPolicy 0개**(타 ns pod 상호도달로 확인) + bare LAN(방화벽 없음). 포트 충돌이 없어서가 아니라 세 조건이 다 열려서.

> **결론:** docker 모드도 멀티노드 크로스노드 통신이 됨(Swarm overlay). encap 특성은 containerd와 동일(single-encap/4789/MTU1450). 차이는 **누가 오버레이를 소유·제어하느냐** — privnet은 backend.ai가 세션별로 제어(VNI/격리), Swarm은 Docker가 관리(제어 밖) + 세션 경로에 호스트 Swarm 의존. NCCL inter-node 관점에선 둘 다 같은 언더레이 한계를 가지며 인터페이스 선택(hang) 이슈도 동일.
> **미검증(의도적):** 매니저-드리븐 docker 멀티노드 **세션**은 호스트 docker Swarm이 필요해 dev 스택 보호를 위해 생략. 데이터플레인(Swarm overlay)만 격리 검증.

### 결정적 아키텍처 차이: Swarm 매니저 노드 종속 vs privnet 탈중앙

Docker Swarm은 **매니저 노드가 필수**(HA면 3+개 Raft 쿼럼). backend.ai docker 모드에선 **매니저의 호스트 docker가
Swarm 매니저**가 되고 fatpod docker들이 worker로 join. → fatpod 모델과 상충:

| | Docker Swarm (docker 모드) | privnet (containerd 모드) |
|---|---|---|
| 중앙 매니저 노드 | **필수** (SPOF 또는 3+ Raft 쿼럼) | **없음** (탈중앙) |
| 컨트롤플레인 | Swarm 자체 Raft (별도 계층) | **etcd 재사용**(backend.ai가 이미 보유) |
| fatpod(pod) 재스케줄 | 매니저면 Swarm 붕괴 위험, worker join 토큰·노드 관리 | 무관 — 각 agent가 etcd 뷰로 독립 복구 |
| 호스트 종속 | 세션 경로가 **호스트 docker를 Swarm 매니저로 요구**(침습) | 호스트 독립, agent별 자기완결 |
| 오버레이 소유·격리 | Docker(제어 밖) | backend.ai가 세션별 VNI/LOCAL FORWARD 제어 |

**privnet은 중앙 네트워크 매니저가 없다** — 각 agent가 자기 VTEP을 etcd에 발행하고 피어 VTEP을 etcd에서 읽어
각자 VXLAN FDB를 프로그래밍(탈중앙). ephemeral한 fatpod(재스케줄되는 pod)엔 Swarm의 Raft-쿼럼 매니저보다
etcd-탈중앙 privnet이 근본적으로 더 적합.

**왜 둘이 반대 선택을 했나 — 설계 목표가 정반대이기 때문:**

| | 설계 목표 | 택한 것 | 대가 |
|---|---|---|---|
| Docker Swarm | **외부 의존성 0**(도커만으로 클러스터 완성) | Raft를 매니저에 **내장** | 매니저 노드+쿼럼 직접 운영 |
| backend.ai | 이미 etcd가 **하드 의존성** | 기존 **etcd 재사용** | 없음 |

- Swarm classic(~1.11)은 외부 etcd/consul을 썼으나, Swarm mode(1.12+)에서 **외부 의존 제거를 위해** Raft를 매니저에 내장.
- 그 "self-contained" 장점은 **도커 단독 사용자**에게 의미. **backend.ai엔 무의미** — 의존성-프리를 지향하지 않고 이미 etcd가 있으므로.
- 오히려 Swarm 도입 = 기존 etcd 위에 **두 번째 합의 계층을 중복**으로 얹고 매니저 쿼럼·호스트 Swarm 의존을 새로 떠안는 것.

> **이것이 BEP-1062가 Swarm overlay 대신 자체 VXLAN(privnet)을 택한 핵심 정당성:** 합의는 어느 쪽이든 필요하지만,
> backend.ai는 이미 가진 etcd로 이미 해결했다. Swarm은 그 해결된 문제를 다시, 더 무겁게(별도 Raft 매니저로) 푸는 것.
> **etcd를 이미 가진 backend.ai에겐 privnet의 etcd-재사용이 정답.**

### 기능·실패모드 상세 비교

**(a) fatpod 변경(재스케줄/재시작) 시 거동 — fatpod 모델의 핵심 관심사**

| 시나리오 | Docker Swarm | privnet (VXLAN/etcd) |
|---|---|---|
| worker 재스케줄 | 옛 노드 "Down" 잔류+**새 join 토큰 재가입**, stale 노드 누적. swarm state가 emptyDir면 **재시작마다 멤버십 소멸→fresh 재가입** | agent가 **etcd에 VTEP 재발행**→피어가 읽어 FDB 재프로그래밍(설계된 경로) |
| manager 재스케줄 | **치명적**(Raft 상태 소멸, 쿼럼 없으면 컨트롤플레인 붕괴). pod=매니저는 반패턴 | 해당 없음 — **중앙 매니저 없음** |
| hostNetwork | advertise=노드 IP지만 daemon 재시작=새 node 정체성, swarm state 영속화 필요 | **VTEP=노드 IP 고정** → 재시작해도 동일, 재수렴 최소 |

> ⚠️ **정직한 단서:** privnet도 재스케줄/재시작 경로가 버그 다발 영역(`next.md`: stale VTEP 키, `_resume_session` VTEP 가드 우회, reconcile 취약성 등 수정 이력). **"구조상 churn 지원" ≠ "저절로 안전"**. 다만 Swarm은 구조 자체가 ephemeral pod에 적대적인 반면, privnet은 churn을 전제로 설계됨(withdraw_vtep·stale 회수·15초 재수렴).

**(b) Swarm이 더 되는 것 (privnet엔 없음)**
- 오버레이 **암호화**(`--opt encrypted`, IPSec) 내장 — privnet은 평문
- **서비스 VIP LB + DNS 디스커버리** 내장 — privnet 없음(단 backend.ai는 rank 직결이라 불필요)
- 기성품 성숙도 — privnet은 자체 코드(유지보수 부담)

**(c) privnet이 더 되는 것 (Swarm은 불가/어색)**
- **세션별 미세 격리**(세션별 VNI + LOCAL FORWARD)를 backend.ai가 직접 제어 — Swarm은 Docker가 네트워크 단위 관리(제어 밖)
- hostNetwork **단일-encap(베어메탈 동일)** + VTEP=노드 IP 안정성
- **투명성/디버깅**: FDB·VNI를 우리가 관찰·수정 — Swarm 오버레이는 숨은 netns 블랙박스
- **탈중앙 실패격리**: agent 1개 실패는 국소적 — Swarm은 매니저(쿼럼) 실패가 전체 네트워크 변경 능력에 영향

**(d) 둘 다 동일**: VXLAN 4789 / MTU 1450 / single-encap over host-gw, 언더레이 성능 한계, NCCL 인터페이스 선택 이슈, **4789 포트(hostNetwork 공존 시 충돌)**.

> **종합:** 기능 표면적은 Swarm이 넓으나(암호화/LB), backend.ai가 실제로 필요한 것(세션별 격리 + ephemeral 친화 + 탈중앙 + 투명성)은 privnet만 제공. 특히 **fatpod 변경 관점에서 Swarm은 구조적 취약(worker churn·매니저 fragility·state 영속성), privnet은 그걸 위해 설계됨.**

## 종합 판정

| 구분 | 결과 |
|---|---|
| 0단계 게이트 | ✅ PASS |
| 1단계 권한 | ✅ 대체로 PASS (GPU device-plugin·이미지 toolkit만 미비) |
| 2단계 A (핵심 데이터플레인) | ✅ **PASS** — pod network·hostNetwork 양쪽에서 크로스노드 CinC↔CinC·MTU·/etc/hosts |
| **최종** | ✅ **hostNetwork 노선 채택** — 베어메탈 BEP-1062와 동일 동작 확인 |

---

## 미완 / 다음 실행 후보

1. **세션 간 격리** 정량화 — fatpod 용량 늘려 동시 2세션으로 cross-session 도달 차단(세션별 VNI/LOCAL FORWARD)
2. **GPU 주입 (2단계 C)** — NVIDIA k8s device-plugin 설치 + fatpod 이미지에 nvidia-container-toolkit + `/etc/cdi` 마운트
3. **정량 성능** — iperf3 대역폭 / nccl-tests busbw로 베어메탈 무회귀 확인
4. **privnet SYS_ADMIN 제거** 하드닝 — in-netns 설정을 pyroute2 netnsid-netlink로 재구현
5. **hostNetwork 운영화** — 프로덕션에선 fatpod 전용 노드(dev agent 미실행)가 정석. 현재는 포트/pool 수동 분리로 공존

## 정리 상태 (2026-08-05 실험 종료 시점)

- 테스트 세션 6개 전부 TERMINATED, 내 fatpod agent 레코드 전부 TERMINATED
- k8s `bai-fatpod` 네임스페이스 삭제, 양 노드 호스트 netns의 bai* 디바이스 0
- **3노드 k8s 클러스터는 유지**(사용자 결정), 호스트 dev 스택(manager/i-node1/i-node2)·사용자 원래 i-fatpod 컨테이너 보존
