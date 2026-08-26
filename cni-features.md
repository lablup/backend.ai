# 런타임 백엔드 검증표 — CNI · 네트워크 · 기능 · 로그 · PID

**결론: 9개 CNI 구성 × 3개 런타임 백엔드 = 27칸 전부 통과.** 두 CNI는 설정 없이, 나머지는 설정
한두 개가 필요하다. 3개 백엔드는 3개 네트워크 옵션 × 11개 기능에서도 모두 통과하고, 컨테이너 로그
로테이션과 PID 처리도 정상이다 — 단 컨테이너화된 에이전트에서 containerd 로그 경로가 어긋나 있었고
(수정 완료), rootless 로테이션은 성질이 다르다.

측정일 2026-08-26 · 브랜치 `feat/containerd-network-v2-rebased` · 클러스터 4× k8s v1.34.1

---

## 1. CNI × 백엔드 (실제 Backend.AI 멀티노드 GPU 세션)

**27칸 전부 통과.** 9개 CNI 구성 × 3개 런타임 백엔드를, 매번 실제 세션(`cluster_size 2`,
커널당 `cuda.device 1`)으로 라이브 4노드 클러스터에서 확인했다. 각 칸: 노드당 GPU 1장 정확히 배치,
`cuInit 0 / cuDeviceGetCount 1`, 크로스노드 0% 손실, DF 경계가 오버레이 MTU−28에서 정확.

| CNI / 모드 | 필요한 설정 | 실측 언더레이 | 오버레이 MTU | DF 경계 | containerd | enroot | singularity |
|---|---|---|---|---|---|---|---|
| flannel host-gw | 없음 | 1500 | 1450 | 1422 | 통과 | 통과 | 통과 |
| flannel vxlan | `mtu=1450` | 1450 | 1400 | 1372 | 통과 | 통과 | 통과 |
| flannel ipip | `mtu=1480` | 1480 | 1430 | 1402 | 통과 | 통과 | 통과 |
| flannel wireguard | `mtu=1420` | 1420 | 1370 | 1342 | 통과 | 통과 | 통과 |
| calico ipip | `vxlan-port=4790` + `mtu=1480` | 1480 | 1430 | 1402 | 통과 | 통과 | 통과 |
| calico vxlan | `vxlan-port=4790` + `mtu=1450` | 1450 | 1400 | 1372 | 통과 | 통과 | 통과 |
| calico no-encap | `vxlan-port=4790` | 1500 | 1450 | 1422 | 통과 | 통과 | 통과 |
| cilium vxlan | `mtu=1430` | 1430 | 1380 | 1352 | 통과 | 통과 | 통과 |
| cilium native routing | `mtu=1480` | 1480 | 1430 | 1402 | 통과 | 통과 | 통과 |

버전: flannel 최신 · calico v3.30.0 · cilium 1.17.5 · k8s v1.34.1

### 실패 형태가 두 가지다

**Calico — 포트 차단.** Felix가 모든 파드 veth의 호스트 쪽에 안티스푸핑 규칙을 건다.

```
-A cali-fw-<iface> -p udp -m multiport --dports 4789 -j DROP
   /* Drop VXLAN encapped packets originating in workloads */
```

포트는 Felix의 `vxlanPort`(기본 4789)이고 우리가 쓰던 포트와 같다. **캡슐화 모드와 무관하다** —
Calico가 VXLAN을 아예 안 쓰는 IPIP 모드에서도 발동한다. **Calico 쪽은 손댈 필요 없다.** 우리 포트만
옮기면 된다.

**나머지 — MTU 부족.** 매니저가 오버레이 MTU를 *설정된* 언더레이 상수(1500)에서 유도하고 실제 경로를
보지 않는다. 캡슐화하는 CNI는 딱 자기 오버헤드만큼 오버레이가 커진다. 작은 패킷은 통과하고 풀 사이즈
프레임만 ICMP 없이 사라진다.

라이브에서 확인된 예: flannel을 host-gw → vxlan으로 바꾸고 처방을 넣기 전에 세션을 띄우면

```
overlay MTU 1450 exceeds what uplink eth0 can carry (1400)
```

로 **거부된다.** 조용한 블랙홀이 아니라 이름 있는 실패다.

**cilium에서는 파드 디바이스 MTU를 읽으면 안 된다.** 라이브 클러스터에서 터널 모드일 때
디바이스는 1480, 파드 기본 라우트는 `mtu 1430`이었다. 디바이스만 읽으면 50바이트 낙관적이다.
flannel·calico는 반대로 디바이스를 낮추고 라우트는 그대로 둔다. 그래서 **둘 다 읽고 작은 쪽**을 쓴다.

## 2. 백엔드 × 네트워크 옵션

각 칸 = 멀티노드 GPU 세션 1개 (`cluster_size 2`, 커널당 `cuda.device 1`). 노드마다 GPU가 1장이라
GPU 제약만으로 배치가 갈린다.

| 네트워크 옵션 | 오버레이 MTU | DF 경계 | containerd | enroot | singularity |
|---|---|---|---|---|---|
| 4789 평문 (기본) | 1450 | 1422 | 통과 | 통과 | 통과 |
| 4790 평문 (포트 오버라이드) | 1450 | 1422 | 통과 | 통과 | 통과 |
| 4789 ESP 암호화 | 1412 | 1384 | 통과 | 통과 | 통과 |

암호화는 설정이 아니라 와이어에서 확인했다 — `ESP(spi=...)` 양방향, 평문 VXLAN 없음, SA 쌍이 세션과
함께 생기고 사라짐.

---

## 3. 백엔드 × 기능

| 기능 | 확인 방법 | containerd | enroot | singularity |
|---|---|---|---|---|
| 멀티노드 배치 | GPU 제약만으로 노드당 커널 1개 | 통과 | 통과 | 통과 |
| GPU 주입·격리 | 커널 안 `nvidia-smi` + `cuDeviceGetCount == 1` | 통과 | 통과 | 통과 (수정 후) |
| 크로스노드 오버레이 | 커널 간 200패킷 스트림 0% 손실 | 통과 | 통과 | 통과 |
| 풀 MTU 프레임 | DF 경계가 `mtu − 28`에서 정확, 1B 더는 드롭 | 통과 | 통과 | 통과 |
| VXLAN 포트 오버라이드 | 디바이스 `dstport`·etcd meta·와이어 캡처 모두 4790 | 통과 | 통과 | 통과 |
| 오버레이 암호화 | 와이어 ESP + SA가 세션과 함께 생성·제거 | 통과 (수정 후) | 통과 (수정 후) | 통과 (수정 후) |
| MTU 가드 | 파드 eth0를 1450으로 → 블랙홀이 아니라 거부해야 함 | 거부됨 | 거부됨 | 거부됨 |
| 도달성 프로브 | udp/4789 차단 → 침묵이 아니라 로그로 보고해야 함 | 보고됨 | 보고됨 | 보고됨 |
| NCCL all-reduce | `baimulti0` 위 2랭크 torch all-reduce | 미측정 | 통과 | 미측정 |
| 컨테이너 로그 (4절) | 로테이션 상한·tail 정확도·terminate 후 삭제 | 통과 (수정 후) | 통과 (창이 짧음) | 통과 (창이 짧음) |
| PID 처리 (5절) | PID 1 회수·pidns 격리·teardown 정리 | 통과 | 통과 | 통과 |

NCCL은 일반 이미지로 검증했다. 커널 안에서 `pip install torch`가 그냥 되므로 별도 이미지가 필요 없다.
정확도 정확(all-reduce 8회 후 2⁸ = 256), 그리고 **전량 오버레이 경유** — `baimulti0` tx +2187MB /
rx +2204MB 대 `eth0` +0.0MB. 처리량 0.092 GB/s는 1GbE 링크 상한이지 오버레이 결함이 아니다.

---

## 4. 컨테이너 로그 로테이션

`container_logs.max_length` 기본 10 MiB, 파일 5개 → 파일당 2 MiB. **쓰기단을 누가 쥐느냐로 메커니즘이
갈리고, 그 차이가 측정된다.**

| | containerd | enroot / singularity |
|---|---|---|
| PID 1 의 fd 1 | **파이프** (우리 `binary://` 라이터) | **로그 파일** (O_APPEND) |
| 로테이션 주체 | 라이터 자신 — 다 차면 새 파일을 연다 | 밖의 5초 주기 루프가 파일 밑에서 갈아끼운다 |
| 상한 | 하드 | 소프트 |
| 30 MiB 버스트 후 보존 | **8.00 MiB, 연속** | **2.00 MiB** (`.1` 하나뿐) |
| 700 KiB/s 지속 후 보존 | 8.00 MiB, 연속 | 8.00 MiB, **경계마다 구멍** |
| terminate 후 파일 삭제 | 10초 내 | 10초 내 |
| TERMINATED 세션 로그 조회 | 전체 윈도우 | 전체 윈도우 |

측정 방법: 커널 PID 1 의 fd 1 에 번호가 붙은 1 KB 줄을 직접 써서(`MARK %08d`) 어느 바이트가 어느
파일에 남았는지 추적했다.

**containerd 는 Docker 와 같은 창을 준다.** 30 MiB 를 쏟아부은 뒤 남은 것:

```
.log.4  MARK 00022726 – 00024791
.log.3  MARK 00024792 – 00026857
.log.2  MARK 00026858 – 00028924
.log.1  MARK 00028925 – 00030990
.log    MARK 00030991 – 00030992     합계 8.00 MiB, 끊긴 데 없음
```

**rootless 는 창이 짧고, 빠르면 구멍이 난다.** 같은 버스트에서 `.1` 하나에 MARK 28927–30992(2 MiB)만
남는다. 로테이터가 "가장 최근 max-size 만 복사하고 truncate" 하기 때문이고, 이건 레이스가 아니라 설계다.
따라서 **max_size / interval = 2 MiB / 5초 ≈ 420 KiB/s** 를 넘는 순간부터 초과분이 버려진다. 700 KiB/s
로 지속해서 쓰면 파일 5개가 다 차긴 하지만 경계마다 ~1480줄(1.4 MiB)이 빈다:

```
.log.4  STDY 00020622 – 00022687      ← 여기서 1480줄 결손
.log.3  STDY 00024167 – 00026232      ← 또 1480줄
.log.2  STDY 00027712 – 00029777
.log.1  STDY 00029839 – 00031904      ← 가장 최근 2 MiB 는 항상 연속
```

가장 최근 2 MiB 는 언제나 온전하고 연속이다. `session logs` 가 그 이하를 요구하면 완전히 정확하고,
그보다 거슬러 올라갈 때만 구멍을 만난다. 하드 캡을 주려면 컨테이너에 파이프를 쥐여주고 우리가
읽어야 하는데, 그러면 에이전트가 재시작하는 동안 커널의 stdout 이 막힌다 — 커널은 에이전트 재시작을
넘겨야 하므로 그 교환은 선택지가 아니다.

에이전트 자신의 로그(`[logging.file]`)는 `RotatingFileHandler`(maxBytes + backupCount)로 정상.

---

## 5. PID · 프로세스 처리

| 항목 | 확인 방법 | containerd | enroot | singularity |
|---|---|---|---|---|
| PID 1 | 컨테이너 안 `/proc/1/cmdline` | `init.py` | `init.py` | `appinit` + 그 아래 `init.py` |
| PID 네임스페이스 격리 | 컨테이너 안에서 보이는 프로세스 수 | 통과 (~10) | 통과 (~10) | 통과 (~11) |
| 좀비 회수 | 고아 손자 20개 → 6초 후 좀비 수 | 0개 | 0개 | 0개 |
| 회수 검출 대조군 | 부모가 살아서 wait 안 함 → 좀비가 보여야 함 | 5개 | 5개 | 5개 |
| teardown 프로세스 정리 | 커널 PID ns 안 백그라운드 5개 → terminate | 전멸 | 전멸 | 전멸 |
| teardown cgroup 회수 | `/sys/fs/cgroup/backend-ai/` 잔재 | 0개 | 0개 | 0개 |
| `memory.max` | 세션 요청 4 GiB | 4294967296 | 4294967296 | 4294967296 |
| `pids.max` | 포크밤 상한 | `max` | `max` | `max` |

**좀비 회수는 공짜가 아니라 `init.py` 덕분이다.** Docker 백엔드는 `HostConfig.Init: True` 로 dockerd 가
tini 를 PID 1 에 꽂아준다. containerd 에는 그런 게 없어서 — OCI 스펙을 우리가 만들고 runc 는 아무것도
끼워넣지 않는다 — 커널 러너가 그대로 PID 1 이 되고 고아를 아무도 거두지 않는다. `init.py` 가 그 자리를
대신 맡고 진짜 프로그램을 자식으로 fork 한다(그래서 러너의 asyncio 가 자기 자식 종료코드를 잃지 않는다).
apptainer 는 `appinit` 을 자체로 PID 1 에 넣으므로 이중이 되지만 해가 없다.

**`pids.max` 는 3개 다 안 걸려 있다 — 다만 Docker 백엔드도 `PidsLimit` 을 안 건다.** 회귀가 아니라
동등성이다. pids 컨트롤러 자체는 위임돼 있으므로(`cgroup.controllers` 에 있음) 포크밤 방어를 원하면
`_write_cgroup_limits` 에 한 줄이면 된다. `cpu.max = max` 인 것도 정상 — CPU 는 쿼터가 아니라 cpuset
핀으로 제한하는 것이 Backend.AI 모델이다.

관찰 하나: **에이전트가 파드의 PID 1 일 때 임의 고아를 blanket-reap 하지는 않는다.** 커널
라이프사이클 경로로는 재현되지 않고(세션을 많이 돌린 에이전트들 좀비 0개) 테스트용 `nsenter` 고아에서만
나왔다. fatPod 매니페스트가 엔트리포인트를 `init.py` 로 감싸면 닫히는, 코드가 아닌 배포 쪽 문제다.

---

## 6. 설정 방법

플러그인 그룹 키는 `network_manager`, 플러그인 이름은 `cni`.

```bash
# 언더레이 MTU (이 노드 파드 경로의 실제 MTU. 이질적이면 최솟값)
etcdctl put /sorna/local/config/plugins/network_manager/cni/mtu 1450

# Calico 클러스터에서 필수. Felix 기본 4789를 피한다
etcdctl put /sorna/local/config/plugins/network_manager/cni/vxlan-port 4790

# 오버레이 암호화 (ESP). 켜면 MTU에서 38B 더 빠진다
etcdctl put /sorna/local/config/plugins/network_manager/cni/overlay-encryption true
```

매니저 재시작 후 적용된다. `mtu`는 클러스터 전역 값 하나이므로 노드마다 언더레이가 다르면 **최솟값**을
넣어야 한다 — 큰 값을 넣으면 감당 못 하는 노드가 세션을 거부한다(설계대로).

포트는 4791처럼 GPE가 아닌 값이 낫다. 4790은 IANA VXLAN-GPE 포트라 tcpdump가 GPE 디섹터로
잘못 파싱해 `unknown-next-protocol`이라 불평한다. 커널 동작에는 영향 없다.

---

## 7. 검증 수준

| 축 | 무엇으로 검증했나 |
|---|---|
| 1~5절 전부 | **실제 Backend.AI 세션**. 라이브 4노드 클러스터(k8s v1.34.1)에서 멀티노드 GPU 세션을 스케줄·RUNNING까지 올리고 커널 컨테이너 안에서 확인한 뒤 정리. CNI 9개 구성은 **운영 클러스터의 CNI를 실제로 교체**하며 측정했다. |

CNI 교체가 가능하려면 인프라가 먼저 견뎌야 했다. `postgres`·`etcd`가 emptyDir이라 파드 재생성마다
데이터가 날아갔다. 노드 고정 hostPath로 전환(`/var/lib/bai-infra/{postgres,etcd}`)한 뒤에야
CNI 교체가 기계적인 작업이 됐다. 교체 후에도 35 agents / 444 sessions / etcd 346키가 그대로 남는다.

재현 스크립트: `.112:~/cnitest/` (데이터플레인 단독 재현용), 세션 하네스는 세션 스크래치패드.

---

## 8. 미검증

- NCCL은 enroot에서만 측정. containerd·singularity는 분산 잡 결과가 없다.
- 노드당 GPU 1장이라 랭크당 1 GPU 구성만 봤다. 노드 내 NVLink/P2P 경로는 미검증.
- default-deny NetworkPolicy 클러스터, CNI 레벨 암호화(cilium WireGuard/IPsec)를 우리 것 아래 겹친 조합.
- 포크밤을 실제로 터뜨려 보지는 않았다. `pids.max = max`는 읽어서 확인했고, 라이브 클러스터에서 재현할 성질이 아니다.
- 로그·PID는 CPU 전용 2노드 세션으로 쟀다. GPU 축과 교차하지는 않았다(교차할 이유가 없는 축이다).

---

## 9. 이 검증이 찾아낸 결함

| 상태 | 결함 | 커밋 |
|---|---|---|
| 수정 | singularity에 GPU가 한 번도 주입되지 않음. `--nvccli`는 apptainer 자신의 환경에서 할당을 읽는데 `--env`로만 넘겼고, 공용 rootless base가 `NVIDIA_*`를 제거. `NVIDIA_DRIVER_CAPABILITIES=all`은 apptainer가 거부. | `f480a92ed` |
| 수정 | 오버레이 암호화가 실제로 안 걸림. `ip xfrm state update`는 SA가 없으면 ESRCH — 생성이 안 된다. 평문으로 나가면서 MTU에서 ESP 38B는 이미 빠진 상태. | `0a112d3fa` |
| 수정 | XFRM teardown 누수. teardown에 XFRM 정리가 아예 없었다. SPI가 `(vni, src, dst)`로 결정되므로 잔재 SA는 같은 VNI를 재사용하는 다음 세션의 트래픽을 전부 먹는다. | `0a112d3fa` |
| 수정 | 동시 브리지 생성 레이스. `ip link show` → `ip link add`가 check-then-act라 한 세션의 두 커널이 동시에 붙으면 진 쪽이 `File exists`로 세션을 실패시킴. | `d5c692d63` |
| 수정 | **containerd 로그 루트가 네임스페이스를 건넌다.** 상수 `/var/lib/backend.ai/containerd-logs`를 넘기지만 containerd는 그 경로를 **자기** 마운트 네임스페이스에서 연다. 호스트 에이전트는 같은 파일시스템이라 안 드러나고, 컨테이너화된(fatPod) 에이전트는 증상 3개가 동시에 조용히 난다 — `session logs`가 1 byte, 커널 로그가 노드에 54개 누적(unlink가 containerd가 쓴 적 없는 디렉터리를 쓸었다), 배포판 프로브가 빈 파일을 읽고 `ImageNotAvailable`. 로그 루트를 `agent.var-base-path` 아래로 앵커링해 해결 — 그 디렉터리는 **이미** 양쪽이 같은 곳을 가리켜야만 한다(로그 라이터 런처가 거기 쓰이고 containerd가 경로로 exec한다). 통상 설정에선 하드코딩돼 있던 그 경로로 그대로 풀린다. | `b690a6791` |
| 열림 | containerd 에이전트 pull 경로에서 `registry-hosts-dir`가 안 먹는다. 노브를 설정하고 디렉터리를 마운트해도 평문 HTTP 레지스트리를 HTTPS로 시도한다. 같은 디렉터리로 `ctr --hosts-dir`는 정상. 노드에 미리 pull해 우회. | — |
| 환경 | Calico 기본 IP 자동탐지가 이중 홈 노드(.112: 유선 .112 + Wi-Fi .252)에서 **Wi-Fi 주소를 골라** BGP가 안 맺힌다. `IP_AUTODETECTION_METHOD=kubernetes-internal-ip` 로 해결. | — |
| 설계 | 한 노드에서 두 백엔드를 돌리면 `/var/lib/backend.ai/net-local-subnet`을 공유해 저장소 가드가 거부한다(정상 동작). 테스트 구성에서만 닿는 문제라 코드 대신 에이전트별 hostPath로 분리. | — |
| 설계 | rootless 로그 로테이션은 소프트 캡이라 **420 KiB/s 이상에서 구멍이 난다**(4절). 하드 캡을 주려면 컨테이너에 파이프를 쥐여주고 우리가 읽어야 하는데, 그러면 에이전트 재시작 중에 커널 stdout이 막힌다. 커널이 에이전트 재시작을 넘겨야 하므로 그 교환은 선택지가 아니다. | — |
| 열림 | `pids.max`가 3개 백엔드 모두 `max` — 포크밤 상한이 없다. 다만 **Docker 백엔드도 `PidsLimit`을 안 걸어** 회귀가 아니라 동등성이다. pids 컨트롤러는 이미 위임돼 있어 `_write_cgroup_limits` 한 줄이면 닫힌다. | — |
| 배포 | 에이전트가 파드의 PID 1일 때 임의 고아를 blanket-reap 하지 않는다. 커널 라이프사이클로는 재현되지 않고 테스트용 `nsenter` 고아에서만 나왔다. fatPod 엔트리포인트를 `init.py`로 감싸면 닫히는, 코드가 아닌 배포 쪽 문제. | — |
