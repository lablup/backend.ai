# 런타임 백엔드 검증표 — CNI · 네트워크 · 기능 · 로그 · PID

**결론: 9개 CNI 구성 × 3개 런타임 백엔드 = 27칸 전부 통과.** 두 CNI는 설정 없이, 나머지는 설정
한두 개가 필요하다. 3개 백엔드는 3개 네트워크 옵션 × 11개 기능에서도 모두 통과하고, NCCL 분산 학습·
컨테이너 로그 로테이션·PID 처리도 정상이다 — 단 컨테이너화된 에이전트에서 containerd 로그 경로가
어긋나 있었고(수정 완료), rootless 로테이션은 성질이 다르다.

측정일 2026-08-26 ~ 27 · 브랜치 `feat/containerd-network-v2-rebased` · 클러스터 4× k8s v1.34.1

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
| NCCL all-reduce | `baimulti0` 위 2랭크 torch all-reduce (4절) | 통과 | 통과 | 통과 |
| 컨테이너 로그 | 로테이션 상한·tail 정확도·terminate 후 삭제 (5절) | 통과 (수정 후) | 통과 (창이 짧음) | 통과 (창이 짧음) |
| PID 처리 | PID 1 회수·pidns 격리·teardown 정리 (6절) | 통과 | 통과 | 통과 |

---

## 4. NCCL 분산 학습

처음엔 enroot 하나만 재놓고 "나머지는 미측정"으로 뒀었다. 원칙이 아니라 순서였고, 못 잴 이유가 없어서
같은 하네스로 3개를 같은 날 같은 노드 쌍(.104 RTX 4070 ↔ .112 RTX 3070)에 다시 돌렸다.

| 백엔드 | 정합성 (2⁸=256) | 8×256MB 소요 | 처리량 | `baimulti0` tx/rx | `eth0` |
|---|---|---|---|---|---|
| containerd | OK | 30.71 s | 0.065 GB/s | +2167 / +2179 MB | +0.0 MB |
| enroot | OK | 29.47 s | 0.068 GB/s | +2178 / +2195 MB | +0.0 MB |
| singularity | OK | 30.42 s | 0.066 GB/s | +2178 / +2199 MB | +0.0 MB |

세 백엔드가 5% 안에 들어온다 — 셋 다 1GbE 링크에 걸려 있다는 뜻이지 백엔드 차이가 아니다. 중요한 건
**`eth0` 가 정확히 0.0 MB** 라는 것: 2.2 GB 가 전부 세션 오버레이를 탔고 파드 네트워크로 새지 않았다.

일반 이미지로 검증했다 — 커널 안에서 `pip install torch`(2.13.0+cu130)가 그냥 되므로 전용 이미지가
필요 없다. `NCCL_SOCKET_IFNAME=baimulti0`, NCCL 2.29.7+cuda13.2.

**singularity 커널 안에서는 `/sys/class/net` 을 믿으면 안 된다.** 측정: 커널 안에서

```
ls /sys/class/net  → bai2a5e231c8ce baibr4106 baif83cb683aa3 bailo4106 baivx4106 eth0 lo tunl0
cat /proc/net/dev  → lo  tunl0  eth0  baimulti0
```

즉 sysfs 가 **에이전트의** 네트워크 디바이스를 보여준다. sysfs 인스턴스는 마운트 시점의 netns 에
묶이는데 apptainer 가 컨테이너 netns 로 들어가기 전에 `/sys` 를 붙이기 때문이고, containerd·enroot 는
컨테이너 안에서 새로 마운트해(ro) 목록이 일치한다. `/proc/net/dev` 는 3개 다 정확하다.

실제로 깨진 것은 못 찾았다 — NCCL 은 `getifaddrs` 를 쓰므로 영향이 없고(2.2 GB 를 `baimulti0` 으로
옮긴 것이 증거), 커널 러너는 `/sys/class/net` 을 읽지 않는다. 다만 사용자 코드가 sysfs 로 인터페이스를
찾으면 틀린 목록을 받고, 덤으로 에이전트의 오버레이 브리지·VXLAN 디바이스 이름이 노출된다.

---

## 5. 컨테이너 로그 로테이션

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

## 6. PID · 프로세스 처리

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

## 7. 설정 방법

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

## 8. 검증 수준

| 축 | 무엇으로 검증했나 |
|---|---|
| 1~6절 전부 | **실제 Backend.AI 세션**. 라이브 4노드 클러스터(k8s v1.34.1)에서 멀티노드 GPU 세션을 스케줄·RUNNING까지 올리고 커널 컨테이너 안에서 확인한 뒤 정리. CNI 9개 구성은 **운영 클러스터의 CNI를 실제로 교체**하며 측정했다. |

CNI 교체가 가능하려면 인프라가 먼저 견뎌야 했다. `postgres`·`etcd`가 emptyDir이라 파드 재생성마다
데이터가 날아갔다. 노드 고정 hostPath로 전환(`/var/lib/bai-infra/{postgres,etcd}`)한 뒤에야
CNI 교체가 기계적인 작업이 됐다. 교체 후에도 35 agents / 444 sessions / etcd 346키가 그대로 남는다.

재현 스크립트: `.112:~/cnitest/` (데이터플레인 단독 재현용), 세션 하네스는 세션 스크래치패드.

---

## 9. 미검증

- 노드당 GPU 1장이라 랭크당 1 GPU 구성만 봤다. 노드 내 NVLink/P2P 경로는 미검증.
- NCCL은 2랭크뿐이다. 3노드 이상, 랭크당 다중 GPU는 하드웨어가 없어 못 잰다.
- default-deny NetworkPolicy 클러스터, CNI 레벨 암호화(cilium WireGuard/IPsec)를 우리 것 아래 겹친 조합.
- 포크밤을 실제로 터뜨려 보지는 않았다. `pids.max = max`는 읽어서 확인했고, 라이브 클러스터에서 재현할 성질이 아니다.
- 로그·PID는 CPU 전용 2노드 세션으로 쟀다. GPU 축과 교차하지는 않았다(교차할 이유가 없는 축이다).
- **단일노드 클러스터 세션**(한 노드에 커널 2개). 1~3절의 27칸은 전부 노드당 커널 1개다. containerd의 `create_local_network`가 no-op이므로(11절), 노드 내 경로가 세션 네트워크만으로 서는지 확인한 적이 없다.

---

## 10. 이 검증이 찾아낸 결함

| 상태 | 결함 | 커밋 |
|---|---|---|
| 수정 | singularity에 GPU가 한 번도 주입되지 않음. `--nvccli`는 apptainer 자신의 환경에서 할당을 읽는데 `--env`로만 넘겼고, 공용 rootless base가 `NVIDIA_*`를 제거. `NVIDIA_DRIVER_CAPABILITIES=all`은 apptainer가 거부. | `f480a92ed` |
| 수정 | 오버레이 암호화가 실제로 안 걸림. `ip xfrm state update`는 SA가 없으면 ESRCH — 생성이 안 된다. 평문으로 나가면서 MTU에서 ESP 38B는 이미 빠진 상태. | `0a112d3fa` |
| 수정 | XFRM teardown 누수. teardown에 XFRM 정리가 아예 없었다. SPI가 `(vni, src, dst)`로 결정되므로 잔재 SA는 같은 VNI를 재사용하는 다음 세션의 트래픽을 전부 먹는다. | `0a112d3fa` |
| 수정 | 동시 브리지 생성 레이스. `ip link show` → `ip link add`가 check-then-act라 한 세션의 두 커널이 동시에 붙으면 진 쪽이 `File exists`로 세션을 실패시킴. | `d5c692d63` |
| 수정 | **containerd 로그 루트가 네임스페이스를 건넌다.** 상수 `/var/lib/backend.ai/containerd-logs`를 넘기지만 containerd는 그 경로를 **자기** 마운트 네임스페이스에서 연다. 호스트 에이전트는 같은 파일시스템이라 안 드러나고, 컨테이너화된(fatPod) 에이전트는 증상 3개가 동시에 조용히 난다 — `session logs`가 1 byte, 커널 로그가 노드에 54개 누적(unlink가 containerd가 쓴 적 없는 디렉터리를 쓸었다), 배포판 프로브가 빈 파일을 읽고 `ImageNotAvailable`. 로그 루트를 `agent.var-base-path` 아래로 앵커링해 해결 — 그 디렉터리는 **이미** 양쪽이 같은 곳을 가리켜야만 한다(로그 라이터 런처가 거기 쓰이고 containerd가 경로로 exec한다). 통상 설정에선 하드코딩돼 있던 그 경로로 그대로 풀린다. | `b690a6791` |
| 닫힘 | ~~containerd pull 경로에서 `registry-hosts-dir`가 안 먹는다~~ — 결함이 아니라 **배포 요구사항**이었다. 라이브 재확인(11절): 같은 containerd·같은 ref에 노브만 바꿔 두 번 pull하면 없을 때만 실패한다. 앞선 관찰은 `certs.d` hostPath가 cd-agent 배포에 추가되기 전의 상태다. | — |
| 환경 | Calico 기본 IP 자동탐지가 이중 홈 노드(.112: 유선 .112 + Wi-Fi .252)에서 **Wi-Fi 주소를 골라** BGP가 안 맺힌다. `IP_AUTODETECTION_METHOD=kubernetes-internal-ip` 로 해결. | — |
| 설계 | 한 노드에서 두 백엔드를 돌리면 `/var/lib/backend.ai/net-local-subnet`을 공유해 저장소 가드가 거부한다(정상 동작). 테스트 구성에서만 닿는 문제라 코드 대신 에이전트별 hostPath로 분리. | — |
| 설계 | rootless 로그 로테이션은 소프트 캡이라 **420 KiB/s 이상에서 구멍이 난다**(5절). 하드 캡을 주려면 컨테이너에 파이프를 쥐여주고 우리가 읽어야 하는데, 그러면 에이전트 재시작 중에 커널 stdout이 막힌다. 커널이 에이전트 재시작을 넘겨야 하므로 그 교환은 선택지가 아니다. | — |
| 열림 | `pids.max`가 3개 백엔드 모두 `max` — 포크밤 상한이 없다. 다만 **Docker 백엔드도 `PidsLimit`을 안 걸어** 회귀가 아니라 동등성이다. pids 컨트롤러는 이미 위임돼 있어 `_write_cgroup_limits` 한 줄이면 닫힌다. | — |
| 열림 | singularity 커널 안 `/sys/class/net`이 **에이전트의** 네트워크 디바이스를 보여준다(4절). apptainer가 컨테이너 netns로 들어가기 전에 `/sys`를 붙여 sysfs 인스턴스가 에이전트 netns에 묶인다. `/proc/net/dev`는 정확하고 NCCL(`getifaddrs`)도 영향 없지만, sysfs로 인터페이스를 찾는 사용자 코드는 틀린 목록을 받고 에이전트의 브리지·VXLAN 이름이 노출된다. | — |
| 배포 | 에이전트가 파드의 PID 1일 때 임의 고아를 blanket-reap 하지 않는다. 커널 라이프사이클로는 재현되지 않고 테스트용 `nsenter` 고아에서만 나왔다. fatPod 엔트리포인트를 `init.py`로 감싸면 닫히는, 코드가 아닌 배포 쪽 문제. | — |

---

## 11. 추가 확인 (2026-08-28)

세 가지다. 10절의 열린 항목 하나를 닫았고, 문서에 없던 백엔드 간 차이를 하나 찾았고, 그 차이들을
단위 테스트로 고정했다.

### `registry-hosts-dir` — 결함이 아니라 배포 요구사항

라이브 containerd(`charsyam-nvidia`, 네임스페이스 `backend-ai`)에 에이전트가 쓰는 것과 같은
`ContainerdGrpcRuntime`을 직접 붙여, 같은 ref를 노브만 바꿔 두 번 pull했다.

| 설정 | 결과 |
|---|---|
| `registry_hosts_dir=None` | `failed to resolve image: ... Head "https://192.168.0.156:5000/v2/..." : http: server gave HTTP response to HTTPS client` |
| `registry_hosts_dir="/etc/containerd/certs.d"` | **OK** |

10절이 보고한 그 에러가 노브를 끄면 재현되고 켜면 사라진다. **코드 경로는 정상이다.**

앞선 관찰은 배포 상태의 차이였다. `certs.d`는 hostPath 볼륨으로 파드에 들어가야 하는데,
그 볼륨이 있는 배포와 없는 배포가 섞여 있었다.

| 파드 | `/etc/containerd/certs.d` | `registry-hosts-dir` |
|---|---|---|
| cd-agent-104 / cd-agent-112 | 있음 (hostPath `certsd`) | 설정됨 |
| en-agent-* / sg-agent-* | 없음 | 설정 없음 |

rootless 백엔드에 이 디렉터리가 없는 것은 무관하다 — 그쪽은 containerd의 `hosts.toml`을 읽지
않고 각각 `ENROOT_ALLOW_HTTP` / `--no-https`로 처리한다. 다만 그 두 노브는 **레지스트리를 가리지
않고 평문을 강제**하므로(4절의 미해결 항목과 같은 뿌리), 레지스트리별 게이트를 넣을 때
rootless 쪽에도 `certs.d`에 상응하는 설정 소스가 필요해진다.

**한 줄 요약**: 노브는 동작한다. 배포에 hostPath 마운트가 빠지면 조용히 HTTPS로 떨어진다.

### containerd의 단일노드 클러스터 네트워크는 no-op이다

Docker 백엔드는 `create_local_network`에서 `ai.backend.cluster-network` 라벨을 단 bridge를 실제로
만들고 destroy에서 지운다. containerd 백엔드는 같은 호출에 **아무것도 하지 않는다.**

```python
async def create_local_network(self, network_name: str) -> None:
    # TODO: a dedicated agent-local bridge for single-node cluster sessions.
    return
```

근거는 BEP-1062의 세션별 LOCAL/오버레이 브리지가 노드 내 경로를 이미 담당한다는 것이고, 그
근거는 코드 주석에만 있었다. 그런데 **1~3절의 27칸은 전부 노드당 커널 1개**다. 한 노드에 커널
2개가 뜨는 클러스터 세션은 측정한 적이 없다. 9절에 미검증으로 올렸다.

### 단위 테스트로 닫은 패리티 구멍 3건

Docker 백엔드가 먼저 갖고 있던 기능을 containerd가 재구현했는데 양쪽 다 테스트가 없던 자리들이다.

| 대상 | 왜 중요한가 | 추가 |
|---|---|---|
| `restart_kernel__{store,load}_config` | `resource.txt`는 커널 프로세스가 이미 핀된 cpuset·가속기를 담는다. 재시작이 이를 조용히 잃으면 할당을 다시 유도해 **커널을 자기 cpuset 밖으로 옮길 수 있다.** 없는 config는 빈 바이트가 아니라 오류여야 하고, scratch 준비 전 저장도 성공한 척하면 안 된다 | 6 |
| `check_duplicate_commit` | 락 파일 기반 판정. 커널별·subdir별 독립성이 검증된 적 없었다 — 남의 락을 내 것으로 읽으면 정상 commit을 거부한다 | 5 |
| `create/destroy_local_network` | 위의 no-op을 계약으로 고정. TODO 구현이 조용한 변경이 아니라 의도적 변경이 되도록 | 3 |

`tests/unit/agent/containerd::` 418 passed (재시도 끔).

### 측정 방법에 관한 주의

커버리지를 이름 grep으로 재면 안 된다. OciRuntime 24개 메서드 중 테스트 파일에 이름이 등장하는
것은 23개지만, **실제 런타임 인스턴스에 대해 호출되는 것은 9개**다. 나머지 히트의 다수는 그
메서드를 가짜로 갈아끼운 하네스(`FakeFacade`)이고, 그건 커버리지의 반대다.

호출되지 않는 15개 중 대부분은 얇은 gRPC 위임이라 라이브 검증이 덮는 것이 맞다. 값이 있는 것은
넷이다 — `exec_in_container`(파일 API·sudoers가 의존, 타임아웃 시 프로세스를 죽여야 함),
`image_entrypoint`(Entrypoint와 Cmd를 합치면 의미가 달라진다), `list_image_infos`(라벨 파싱이
틀리면 이미지가 통째로 안 보인다), `configure_logging`(로그 루트 계약).

---

## 12. CNI 없는 기준선

이 문서의 모든 측정은 **파드 네트워크 위**에서 이뤄졌다. 그 변수를 없앤 구성 — k8s를 통째로
내리고 Backend.AI만 호스트에 올려 언더레이가 물리 LAN뿐인 상태 — 은 별도 문서에 있다:
`non-cni-features.md`.

요약: containerd·singularity 통과, enroot 실패. 7절의 처방이 **하나도 필요 없는** 유일한
구성이며(언더레이 1500이라 매니저 기본값이 그대로 맞다), rootless 백엔드의 privnet 위임이
containerd 전용이라는 설계 제약이 거기서 드러났다.
