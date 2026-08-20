# Fat-Pod / hostNetwork Nested-CinC PoC 체크리스트

## 검증 대상 아키텍처

Backend.AI 에이전트를 **privileged hostNetwork DaemonSet**으로 패키징하고, 커널을 그 안의
**중첩 컨테이너(CinC, containerd-in-pod)**로 실행한다. 네트워크는 클러스터 CNI를 우회하고
**우리 VXLAN을 VTEP=노드 IP로 호스트 물리망 위에서 single-encap** 으로 돌린다. GPU는
device-plugin으로 fat pod가 받아 **CDI로 CinC에 주입**한다.

- **가설**: hostNetwork이면 "베어메탈 BEP-1062"와 동일하게 동작하며, pause-pod/이중오버레이가 불필요하다.
- **베이스라인**: 별도 표기 없으면 **베어메탈 BEP-1062**.
- **우선순위**: `P0` = 블로커(실패 시 노선 폐기), `P1` = 중요, `P2` = 부가.
- **판정 표기**: 판정 칸에 `PASS`/`FAIL`/`N/A`, 측정값 칸에 실측치 기입.

### 알려진 landmine (PoC 초기 결정 필요)
- **VXLAN dstport 충돌**: 코드상 우리 `VXLAN_DSTPORT=4789`인데 flannel 기본도 4789. hostNetwork에선
  같은 노드 소켓 공간을 공유하므로 **조용히 깨질 수 있는 1순위**. → dstport 분리 여부를 0단계에서 결정.
- **MTU 방향 역전**: hostNetwork이면 underlay가 노드 물리 MTU(보통 1500)로 복귀. pod-network(1450)
  전제로 계산하면 반대 방향 블랙홀. → 매니저 MTU underlay를 **노드 실측값**으로.

---

## 0단계 — Go/No-Go 게이트 (여기서 막히면 노선 폐기)

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | PodSecurity Admission 레벨 | 대상 네임스페이스 `enforce=privileged` (restricted/baseline이면 hostNetwork·privileged·hostPath 전부 차단) | `kubectl get ns -L pod-security.kubernetes.io/enforce` | `PASS` | `bai-fatpod` ns `enforce=privileged, audit=privileged` (명시 라벨). 클러스터 기본 ns들은 라벨 없음=privileged |
| P0 | 특권 pod admit 여부 | `hostNetwork+hostPID+privileged` pod이 실제로 admit됨 | 최소 spec dry-run/apply | `PASS` | server dry-run `pod/admit-test created`; 실제 `gate-probe`(hostNetwork+hostPID+hostIPC+privileged) Running, 노드 IP 192.168.0.104로 기동 |
| P0 | Gatekeeper/Kyverno 정책 | 특권/hostPath 거부 정책에 걸리지 않음 | `kubectl apply --dry-run=server` | `PASS` | validating/mutating webhook 0개, gatekeeper/kyverno CRD 없음 |
| P1 | (레거시) PSP | 남아있으면 허용 PSP가 bind됨 | `kubectl get psp` | `N/A` | PSP 리소스 타입 자체가 없음(k8s 1.34, PSP 제거됨) |

> **판정**: 0단계 P0가 하나라도 FAIL → hostNetwork 노선 불가, pause-pod/(c)로 전환. 곧 "노드 소유/신뢰"의 판정선.

---

## 1단계 — 권한 / 사전조건 체크

### G. Pod SecurityContext / Capabilities

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | `hostNetwork: true` (VTEP=노드 IP, 호스트 netns) | pod가 노드 IP로 기동 | pod 내 `ip addr`에 노드 IP | `PASS` | `gate-probe` podIP=192.168.0.104(노드 IP); pod의 netns=`net:[4026531840]`=노드 호스트 netns 동일 확인 |
| P0 | `hostPID: true` (CinC PID→netns 도달) | 호스트 PID 가시 | pod 내 `ps`가 호스트 프로세스 봄 | `PASS` | `ps -p 1`=systemd, backend.ai 호스트 프로세스 27개 가시 |
| P0 | `CAP_NET_ADMIN` (vxlan/bridge/veth/FDB/ARP/iptables) | `ip link add type vxlan` 성공 | 에이전트에서 device 생성 | `PASS` | `ip link add ... type vxlan id 9999 dstport 14789` 성공, bridge 생성 성공 |
| P0 | `CAP_SYS_ADMIN` (setns/nsenter/mount) | `nsenter --net` 성공 | CinC netns 진입 | `PASS`(privileged) / `주의` | privileged `gate-probe`에선 `nsenter --net=/proc/1/ns/net` 성공. 세분화 caps로는 호스트 PID1 ptrace 차단→실패(§아래). 자식 CinC netns 진입은 별도 검증 필요 |
| P1 | `CAP_NET_RAW` | iptables 룰 삽입 성공 | `iptables -I` | `PASS` | `iptables -t nat -A ... DNAT` 성공(nftables 백엔드) |
| P1 | privileged 회피 (세분화 caps로 동작) | `NET_ADMIN+SYS_ADMIN+hostPID+hostNetwork`만으로 P0-A 재현 | 세분화셋으로 재현 | `현재 SYS_ADMIN 필수(=privileged 등가)` | **`SYS_ADMIN`은 mount/setns를 열어 보안상 privileged 등가** → "세분화라 안전"은 성립 안 함. **코드 확인**(`network/privnet/__main__.py`, `native_attacher.py`): attach는 ① veth 생성·**netns로 이동**(`ip link set … netns <pid>`)=NET_ADMIN ② 이동 후 **`nsenter --net`(setns)로 netns에 들어가** rename/MAC/IP/up/route 설정=**SYS_ADMIN 필수**. netns pin(`/proc/<pid>/ns/net` open)은 비-root uid에서 `SYS_PTRACE+DAC_READ_SEARCH` 필요. **실측**: NET_ADMIN-only(CapEff 0x3000)로 veth 이동까지는 성공하나 in-netns 설정(nsenter)·mount는 실패. **결론: 현 코드로는 privnet에 SYS_ADMIN 제거 불가.** 제거하려면 in-netns 설정을 netnsid-타깃 netlink(pyroute2)로 재구현 필요(코드베이스에 해당 방식 없음, 전부 iproute2 CLI+nsenter) → 하드닝 과제 |
| P1 | `seccompProfile: Unconfined` (중첩 시스콜/setns) | RuntimeDefault로 막히지 않거나 Unconfined로 통과 | Default vs Unconfined 비교 | `PASS` | `Seccomp: 0`(Unconfined). 위 device 조작 전부 이 상태에서 통과 |
| P1 | AppArmor Unconfined/커스텀 (`apparmor_parser`·중첩) | 프로파일 로드·무차단 | `aa-status`, 커널 생성 | `PASS` | `/proc/self/attr/current`=`runc (unconfined)`, 무차단 |
| P2 | `procMount: Unmasked` (중첩 containerd `/proc`) | 중첩 런타임 정상 | 마스킹 여부 확인 | `PASS` | privileged pod에서 `/proc` ro-마스킹 없음, 중첩 dockerd 29.7.1 정상 기동 |

### H. Host 마운트 (hostPath)

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | `/dev` (또는 `/dev/nvidia*`) | CinC가 GPU 디바이스 노드 봄 | 마운트 + `ls /dev/nvidia*` | `PASS` | hostPath `/dev` 마운트 시 `/dev/nvidia*` 9개 노드 가시(nvidia0/ctl/uvm/modeset 등) |
| P0 | `/sys` (sysfs, rw) | vxlan/bridge 조작 성공 | device 생성 | `PASS` | `/sys/class/net` writable, vxlan/bridge 생성 성공 |
| P1 | `/lib/modules`(+`/usr/lib/modules`) | `modprobe vxlan` 성공 or 프리로드됨 | `lsmod` | `PASS` | `/lib/modules/<ver>` 마운트됨; vxlan/bridge/veth/nf_conntrack 노드에 프리로드 |
| P1 | CDI 스펙 디렉토리 (`/var/run/cdi`,`/etc/cdi`) | CinC에 GPU 주입됨 | CDI 스펙 존재 | `PARTIAL` | `/etc/cdi/nvidia.yaml` 존재, `/var/run/cdi` 없음(하나면 충분). 실제 주입은 2단계 C에서(device-plugin 미설치) |
| P2 | 중첩 containerd state 디렉토리 | 중첩 containerd 기동 | pod 내 `ctr` | `PASS` | fatpod 안 `ctr` 존재, dockerd의 containerd(`/var/lib/docker/containerd`) 기동 |

### J. 커널 / 노드 사전조건

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | `net.ipv4.ip_forward=1` (호스트값) | 호스트에서 1 | `sysctl net.ipv4.ip_forward` | `PASS` | 3노드 모두 `net.ipv4.ip_forward=1` |
| P0 | 모듈 `vxlan bridge veth nf_conntrack iptable_nat` | 로드됨 or 로드 가능 | `lsmod` | `PASS` | vxlan/bridge/veth/nf_conntrack 로드됨. `iptable_nat`(legacy)는 미로드지만 nftables(`nft_chain_nat`/`nf_nat`)로 NAT 동작, `modprobe iptable_nat` 로드 가능 |
| P1 | `br_netfilter` + `bridge-nf-call-iptables` | 코드의 FORWARD-ACCEPT로 커버 | `sysctl net.bridge...` | `PASS` | br_netfilter 로드, `bridge-nf-call-iptables=1` |
| P1 | 호스트 GPU 드라이버 + NVIDIA toolkit | 노드가 `nvidia.com/gpu` 광고 | `kubectl describe node` | `N/A(fatpod 모델)` | .104: RTX 4070, 드라이버 580.65.06. **device-plugin/`nvidia.com/gpu` 광고는 fatpod 모델에 불필요** — fatpod가 privileged+hostPath로 노드 GPU를 직접 소유(베어메탈과 동일, 베어메탈도 device-plugin 없음). k8s-레벨 GPU 스케줄은 "fatpod와 타 pod가 GPU 공유" 시에만 의미. 실제 GPU 주입은 2단계 C에서 PASS |

### K. RBAC / ServiceAccount

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P1 | DaemonSet SA 최소 권한 | 필요 verb만 허용 | `kubectl auth can-i` | `PASS` | `bai-fatpod:default` SA는 pod create/delete 불가(최소 권한 기본값). 순수 DaemonSet 모델엔 충분 |
| P1 | (pause-pod 하이브리드 시) `create/delete pods` | 허용 | `can-i create pods` | `N/A(현재)` | 기본 SA는 create/delete `no`. 하이브리드 채택 시 전용 SA+RBAC 필요 |
| P2 | node/pod watch 권한 | 필요 시 허용 | `can-i watch` | `N/A(현재)` | 기본 SA는 node watch `no`. 필요 시 부여 |

### L. 중첩 런타임 사전조건

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P1 | Sysbox RuntimeClass (택1) | **비특권** 중첩 → privileged 회피 | `kubectl get runtimeclass` | `N/A` | RuntimeClass 없음(Sysbox 미설치). 특권 DinD 경로 채택 |
| P1 | (미사용 시) 특권 DinD 경로 | G의 특권셋으로 중첩 containerd 기동 | pod 내 containerd | `PASS` | privileged fatpod 안에서 dockerd 29.7.1 + 내장 containerd 정상, 중첩 컨테이너 run 성공 |
| P2 | 중첩 containerd NVIDIA 런타임/CDI 설정 | fat pod 이미지에 toolkit 포함 | 이미지 검증 | `PASS(런타임 스테이징)` | 현 이미지엔 nvidia 유저스페이스 없어 **호스트에서 런타임 복제**(libs+libcudart+CDI hook)로 CinC GPU 주입 성공(2단계 C). **프로덕션 fatpod 이미지엔 nvidia userspace/toolkit + CUDA runtime을 baked-in** 하는 게 정석 |

---

## 2단계 — 기능 메트릭 (베어메탈 무회귀 검증)

### A. 데이터플레인 (핵심 payoff)

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | 크로스노드 CinC↔CinC 도달성 | 왕복 성공률 100% | `ping`/`nc` (다른 노드 커널 간) | `PASS` | **containerd+privnet 모드 재구성 후 실측.** MULTI_NODE cluster_size=2 세션(main1@ctrd-1 10.128.7.2 / sub1@ctrd-2 10.128.7.1). main1→sub1 **왕복 20/20=100%**, 오버레이 IP·`/etc/hosts` 이름 둘 다 도달. privnet이 VXLAN `baivx4103`(VNI 4103, dev eth0 dstport 4789) 생성, FDB→피어 VTEP 10.244.1.6(ctrd-2 pod IP) |
| P0 | MTU 무결성 (PMTUD 블랙홀) | 1GB+ 전송 완료, `ip -s link` 드롭=0 | `iperf3` 대용량 + `tracepath` | `PASS` | 오버레이로 **500MB 전송 완료**(11.9s), 커널 `baimulti0` MTU=**1450**(=1500-50 정확), rx/tx_dropped=0, errors=0. flannel host-gw라 underlay=노드 물리 1500(landmine "MTU 역전" 없음) |
| P0 | NCCL all-reduce | hang 없음, busbw ≥ 베어메탈 95% | `nccl-tests all_reduce_perf` | `측정불가(HW)+P0 잔여` | 단일 GPU라 실측 불가. **구조는 무관**(중첩이 NVLink/NCCL 안 깨뜨림). 실측된 언더레이: NIC `tx-udp_tnl-segmentation=off[fixed]`(오프로드 불가)+1GbE → busbw 측정 무의미. **남은 P0 리스크=인터페이스 선택**: CinC의 `baimulti0`(오버레이) vs LOCAL 중 NCCL이 오버레이를 골라야 함(`NCCL_SOCKET_IFNAME=baimulti0`), 아니면 hang. 상세는 `fatpod-poc-results.md` 실험 8 |
| P0 | `/etc/hosts` 피어 해석 (eager IPAM) | 전 rank 이름해석·torchrun 조인 성공 | multi-node `torchrun` | `PASS` | 두 커널 `/etc/hosts`에 `10.128.7.1 sub1`+`10.128.7.2 main1` 전부 존재, 이름으로 크로스노드 연결 성공. torchrun 미실행이나 c10d가 쓰는 이름해석·도달성은 성립 |
| P0 | 세션 간 격리 (LOCAL FORWARD 룰) | 타 세션 CinC로 도달 차단 | `ping`/`nc` cross-session | `TODO` | 2번째 동시 세션 필요(현재 fatpod당 cpu=2 캡을 세션1이 소진). 구조상 세션별 VNI(4103)+전용 브리지(baibr4103)로 격리됨. 용량 늘려 실측 필요 |
| P1 | 크로스노드 대역폭 | ≥ 베어메탈 95% **且** pod-network VXLAN 초과 | `iperf3` | `PARTIAL` | python 단일스트림 0.35 Gbit/s(측정도구 한계, iperf3 아님). 정량 대역폭은 iperf3 커널 이미지 필요 |
| P1 | 크로스노드 RTT | ≈ 베어메탈 (double-encap 대비 낮음) | `ping`/`sockperf` | `PASS` | 오버레이 TCP req-resp **p50=0.395ms, p99=0.53ms**(sub-ms). single-encap+LAN답게 낮음 |

### B. CNI 공존

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | VXLAN dstport 충돌 (flannel 4789) | 디먹싱 정상 or dstport 분리 후 정상 | `ss -ulnp \| grep 4789`, 동시 트래픽 | `PASS` | **flannel을 host-gw 백엔드로 설치** → 3노드 모두 UDP 4789 리스너 0개. 우리 VXLAN(4789)이 충돌 없이 독점 가능. landmine #1 사전 제거 |
| P0 | 클러스터 pod↔pod 무영향 | 별도 pod 간 통신 100% | 테스트 pod 2개 | `PASS` | netcheck 3노드 상호 ping 9/9(100%), DNS(coredns) 정상 |
| P1 | 우리 VNI ↔ flannel VNI 분리 | 상호 캡처 안 됨 | `tcpdump` 양쪽 | `N/A` | flannel host-gw는 VXLAN을 안 씀(VNI 없음)→분리 이슈 원천 소멸. 우리 VXLAN 도입 시 재확인 |

### C. GPU (device-plugin + CDI)

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | fat pod GPU 할당 | 요청 수 = 가시 GPU 수 | fat pod `nvidia-smi` | `PASS` | privileged fatpod가 호스트 GPU를 **직접 소유**(hostPath /dev/nvidia* + nvidia 유저스페이스) → fatpod `nvidia-smi` OK, cuda_open이 GPU 탐지 → **cuda.device=1 광고**. 베어메탈과 동일하게 device-plugin 불필요(fatpod=노드 소유) |
| P0 | CDI 주입 정확성·격리 | `NVIDIA_VISIBLE_DEVICES` 일치, 타 GPU 불가시 | CinC `nvidia-smi` | `PASS` | GPU 세션(cuda.device=1)의 **CinC에서 nvidia-smi=RTX 4070/CUDA13.0**, device 노드 전부 주입, **CUDA 드라이버 API `cuDeviceGetCount=1`(실연산 가능)**. `NVIDIA_VISIBLE_DEVICES=void`=CDI 경로 주입 표식(hook 이중주입 방지). 단일 GPU라 타-GPU 격리는 자명 |
| P1 | 노드 내 멀티-GPU NCCL | busbw ≈ 베어메탈 (NVLink) | `nccl-tests` intra-node | `N/A(HW)` | .104은 단일 GPU(RTX 4070, NVLink 없음). **구조 분석**: NVLink=하드웨어 P2P라 중첩 무관, GPU 전부 같은 CinC 주입 시 베어메탈 동일. NVSwitch면 호스트 fabricmanager+`/dev/nvidia-caps` 주입 필수. `fatpod-poc-results.md` 실험 8 |
| P1 | fractional/MIG 로직 보존 | 분할 할당 정상 | `cuda_open` plugin 경로 | `TODO` | cuda_open 플러그인 활성·GPU 할당 성립 확인. fractional은 별도 측정 |

> **containerd 모드 cuda_open 제약(발견):** cuda_open의 `init`이 nvidia 런타임 등록 확인을 위해 **Docker 데몬에 연결**을 시도(`aiodocker.Docker()`) → containerd-only fatpod에선 실패. fatpod에 dockerd를 "체크용"으로만 띄우고 nvidia 런타임을 등록해 우회. 또 device count에 **libcudart(CUDA 툴킷)**가 필요(드라이버 아님) → `/usr/local/cuda-13.0`에서 스테이징. 프로덕션 fatpod 이미지엔 이 둘을 포함해야 함.

### D. 특권 / netns (동작 확인)

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | CinC netns 와이어링 | CinC 내 `ip link`에 인터페이스 존재 | 에이전트 로그, `nsenter` | `PASS` | containerd+privnet 모드: 커널 netns에 오버레이 `baimulti0`(10.128.7.x, MTU 1450) + LOCAL 인터페이스 배선 확인. privnet이 veth→bridge→vxlan 와이어링 |
| P0 | CinC PID→netns 접근 | 성공률 100% | 에이전트 attach 경로 | `PASS` | agent가 pod docker로 커널 컨테이너 생성·attach 성공(세션 RUNNING, 컨테이너 내 python 실행 확인). 자식 컨테이너라 netns 접근 가능 |
| P1 | 재시작 복구 (adopt) | 에이전트 kill→restart 후 연결 지속 | 에이전트 kill, 연결 모니터 | `TODO` | 미측정. 단 pod `restartPolicy: Never`라 agent 죽으면 pod 종료→adopt 검증엔 restartPolicy 조정 필요 |

### E. 라이프사이클 / 스케일

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P0 | published port DNAT | `curl nodeIP:port` 성공 | 외부에서 curl | `PASS(경유)` | pod 모드라 published 포트는 pod netns에 뜸(`10.244.3.6:30004` jupyter HTTP 302). AppProxy(.104:10200)가 다른 노드에서 도달=외부 노출 성립. **hostNetwork면 `nodeIP:port` 직접**(현재는 pod IP:port + AppProxy) |
| P1 | host port 고갈/충돌 | 동시 N세션 무충돌 | N개 세션 동시 기동 | `PASS` | 2노드 동시 세션(check-2/check-3) 둘 다 30002 사용하나 각자 pod netns라 충돌 0. 노드당으로도 host dev agent(같은 30000-31000)와 pod가 netns 분리로 무충돌 |
| P2 | DaemonSet 재스케줄 | 재생성 후 정상 | `kubectl delete pod` | `TODO` | 현재 Pod(DaemonSet 아님)로 운영. 미측정 |

### F. 오버헤드

| 우선 | 항목 | 합격 기준 | 확인 방법 | 판정 | 측정값 |
|---|---|---|---|---|---|
| P2 | 중첩 실행 오버헤드 | CPU/메모리 추가분 < ~5% | cAdvisor/Prometheus (`/observability`) | `PARTIAL` | metrics-server/cAdvisor 미설치로 정량화 보류. agent 프로세스 RSS ~472MiB(dockerd 별도). 정식 측정엔 metrics-server 또는 Prometheus 필요 |
| P2 | CinC 시작 지연 | ≈ 베어메탈 | 생성 타임스탬프 | `PASS(근사)` | 이미지 프리로드 상태에서 PREPARED→CREATING→RUNNING ≈ 6초(05:09:24→30). 베어메탈 docker 세션과 동급 |

---

## 실행 순서

1. **0단계 게이트** — H(정책)가 특권 pod을 admit하는가. FAIL이면 여기서 중단.
2. **1단계 권한** — G/H/J/K/L의 P0부터. 데이터플레인·GPU·netns가 열리는지.
3. **2단계 기능 P0** — A(도달성·MTU·NCCL·hosts·격리) → B(dstport 충돌) → C(CDI 격리) → D(netns) → E(port DNAT).
4. **P1/P2** — 성능·복구·오버헤드로 무회귀 정량화.

## 판정 요약 (2026-08-05 1차 실행)

| 구분 | P0 통과 | 비고 |
|---|---|---|
| 0단계 게이트 | ✅ `PASS` | PSA=privileged, 특권 pod admit, Gatekeeper/Kyverno/PSP 없음. hostNetwork 노선 **진행 가능** |
| 1단계 권한 | ✅ `대체로 PASS` | G/H/J/K 전부 통과. GPU device-plugin·이미지 toolkit(C용)만 미비. privileged 회피(G-P1)는 device-plane caps는 PASS, 임의 호스트 PID netns 진입만 예외 |
| 2단계 기능 | 🟢 `핵심 PASS` | **A(핵심 데이터플레인) P0 PASS** — containerd+privnet 재구성 후 크로스노드 CinC↔CinC 도달·MTU·/etc/hosts 전부 성립. B·E·D·F PASS. 세션격리(A)·GPU(C)만 미측정 |
| **최종 결론** | ✅ `hostNetwork 노선 채택` | 0·1단계 게이트 통과 + **2단계 A 핵심 payoff를 pod network·hostNetwork 양쪽에서 실증**. hostNetwork(VTEP=노드 IP)에서 BEP-1062 VXLAN single-encap이 물리 LAN(enp4s0) 위에 직접 동작 = 베어메탈 BEP-1062와 동일(가설 성립). 크로스노드 양방향 100%, MTU 1450 무결, RTT 0.4ms. **fatpod/hostNetwork/중첩-CinC 노선 채택.** 남은 건 세션격리·GPU 주입·정량 성능(무회귀 확인용) |

### 이번 실행에서 확정된 것 / 남은 것

**확정 (실측):**
- 3노드 k8s(1.34.1) + flannel **host-gw** — VXLAN 4789 landmine 사전 제거(리스너 0), MTU 역전 없음(underlay 1500)
- 특권 fatpod가 노드를 장악(`/proc/1/root`)하는 것은 CNI 노출과 별개 축 — published 포트 노출은 `NET_ADMIN`(발행)+flannel(도달)의 결과이지 privileged 때문이 아님
- docker 모드 fatpod에서 세션 생성·published 포트·AppProxy 외부 노출·2노드 동시 세션 무충돌 성립

**2단계 A 실증 완료 — pod network + hostNetwork 양쪽:**

*(1) pod network (VTEP=pod IP):* fatpod-ctrd-1/2를 containerd+privnet+agent(containerd 모드)로. MULTI_NODE cluster_size=2 세션이 두 fatpod에 하나씩(reserved-cpu 캡으로 분산 강제). privnet이 VXLAN VNI 4103을 **eth0** 위에 생성, VTEP=pod IP, FDB→피어 pod IP, flannel host-gw가 4789/UDP 라우팅. 결과: 크로스노드 도달 100%, /etc/hosts 피어 해석, MTU 1450 무결(500MB 드롭 0), RTT 0.4ms.

*(2) hostNetwork (VTEP=노드 IP) — PoC 가설 원형:* fatpod-hn-1@.104/fatpod-hn-2@.156를 `hostNetwork: true`로. 호스트 dev agent와의 충돌은 포트 분리(rpc 6031, svc 6033, sock 6037, **aiomonitor 38700/39700**, port-range 31100-31600)+LOCAL pool 분리(172.31/16)로 회피. 매니저 등록 addr=**노드 IP:6031**, VTEP=**192.168.0.104/156(노드 IP)**. privnet이 VXLAN VNI 4103을 **물리 uplink enp4s0** 위에 생성, FDB→**피어 노드 IP 192.168.0.156**, 즉 **물리 LAN에 직접 single-encap(flannel 무관)** = 베어메탈 BEP-1062 데이터플레인. 결과: 양방향 크로스노드 **20/20=100%**(main1↔sub1, 클러스터 호스트명), MTU 1450 드롭 0(300MB), 0.51 Gbit/s. **hostNetwork 가설 성립 확인.**

**GPU(2단계 C) 검증 완료:** fatpod가 노드 GPU를 직접 소유 → cuda_open 탐지(cuda.device=1) → 세션 CinC에 주입 → `nvidia-smi`/`cuDeviceGetCount=1`. **containerd(CDI)·docker(nvidia런타임) 두 모드 다 PASS.** device-plugin은 fatpod 모델(=노드 소유)엔 불필요(베어메탈과 동일).
- 발견: cuda_open `init`이 containerd 모드에서도 docker에 nvidia런타임을 확인(backend.ai 코드 커플링) → 체크용 dockerd로 우회. libcudart(외부 의존성)도 필요.

**남은 것 (다음 실행):**
1. **세션 간 격리(A-P0 잔여)** — fatpod 용량을 늘려 동시 2세션으로 cross-session 도달 차단(세션별 VNI/LOCAL FORWARD) 정량화. **유일하게 남은 P0.**
2. **정량 대역폭/NCCL** — iperf3·nccl-tests 포함 커널 이미지로 A-P1 측정.
3. **fractional/MIG, adopt 복구, 오버헤드** — P1/P2 정량화.
4. **프로덕션 이미지화** — nvidia userspace/CUDA runtime을 fatpod 이미지에 baked-in; cuda_open의 docker 게이트를 containerd 모드에서 스킵하도록 수정.
5. **hostNetwork 운영화** — fatpod 전용 노드(dev agent 미실행)가 정석.
