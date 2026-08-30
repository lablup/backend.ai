# CNI 없는 순수 VXLAN 기준선 — 런타임 백엔드 검증

**결론: 3개 백엔드 × (CPU · GPU) 6칸 전부 통과.** 파드 네트워크를 완전히 제거한 구성에서 세션
오버레이는 설정 하나 없이 정확히 동작한다 — 크로스노드 0% 손실, DF 경계가 오버레이 MTU−28에
정확히, GPU는 노드당 1장이 정확히 주입된다.

여기까지 오는 데 결함 넷(평문 HTTP 강제, launch 실패의 원인 소실, LOCAL 서브넷 저장소의
하드코딩 경로, aiomonitor 기동 행)을 고쳤고, 제약 하나(privnet이 containerd에 하드코딩)와
노드 전제 하나(enroot 헬퍼 caps)가 드러났다.

> **이 문서는 8/28 오후까지의 기준선 측정 기록이다.** 그 뒤 같은 브랜치에서 결함 7건이 더 나와
> 총 11건 / 14커밋이 되었고, 여기서 "설계 제약"·"미검증"으로 적힌 항목 몇 개는 이후 해결됐다.
> 이후 내용과 최종 상태는 `works.md`를 본다. 아래 각 절에 **[해결됨]** 표시로 갱신해 두었다.

측정일 2026-08-28 · 브랜치 `feat/containerd-network-v2-rebased` · 자매 문서 `cni-features.md`, `works.md`

---

## 1. 왜 따로 재는가

`cni-features.md`의 27칸(9개 CNI × 3개 백엔드)은 **전부 파드 네트워크 위**에서 쟀다. 그 문서가
찾아낸 실패 두 종류 — Calico의 4789 DROP, 캡슐화 CNI의 MTU 부족 — 는 둘 다 **아래 레이어가 원인**
이다. 우리 오버레이 자체가 맞는지는 그 레이어를 걷어내야 보인다.

이 문서는 그 기준선이다. 언더레이가 물리 LAN(MTU 1500)뿐이면 `cni-features.md` §7의 처방이
**하나도 필요 없어야** 하고, 실제로 그렇다.

---

## 2. 구성

| | |
|---|---|
| k8s | 4노드 전부 `kubelet` 정지 → 파드 컨테이너 레코드 제거 → `flannel.ipip`·`cni0`·pod CIDR 라우트 삭제 |
| 언더레이 | 물리 LAN만. 3노드 상호 ping 0% 손실, MTU 1500 |
| 유지한 것 | 호스트 `containerd`(containerd 백엔드가 쓴다), halfstack 도커 — db 8101 / etcd 8121 / valkey 8111 |
| 매니저 | 네이티브 1개 (`:8091`), `[network.inter-container] default-driver = "cni"` ※ |
| 에이전트 | 3 백엔드 × 3 노드 = 9개 (`i-{cd,en,sg}-{104,112,156}`) |
| 네트워크 플러그인 설정 | **없음** — `mtu`/`vxlan-port`/`overlay-encryption` 모두 미설정 |

※ 이 `"cni"`는 **Backend.AI 자체의 BEP-1062 오버레이 드라이버 이름**이고, 이 문서가 걷어낸
쿠버네티스 CNI와는 무관하다 (`manager/config/unified.py`의 `ipam-pool`·`forced-backend` 설명 참조).
드라이버의 다른 값은 `"overlay"`(Docker Swarm)뿐이다.

노드: `.104`(RTX 4070, 31 CPU) · `.112`(RTX 3070, 15 CPU) · `.156`(GPU 없음, 15 CPU).

`kubelet`을 멈추는 것만으로는 부족하다. 파드 컨테이너는 containerd가 계속 돌리고, `flannel.ipip`와
pod CIDR 라우트도 남는다. 컨테이너 레코드를 지우고 인터페이스·라우트를 직접 걷어내야 언더레이가
정말로 물리 LAN만 남는다. **`containerd` 자체는 멈추면 안 된다** — containerd 백엔드가 그걸 쓴다.

---

## 3. 결과

세션마다 `cluster_size 2`, 커널당 CPU 8. `.112`/`.156`이 각 15 CPU이므로 `2×8 = 16 > 15`라야
노드당 커널 하나로 갈린다(그냥 두면 한 노드에 bin-pack된다 — `cni-features.md` 2b절과 동일).

| 백엔드 | 세션 | VNI | 오버레이 IP | 크로스노드 200패킷 | DF 경계 | PID 1 |
|---|---|---|---|---|---|---|
| containerd | RUNNING | 4103 | 10.128.7.1 ↔ .2 | **0% 손실**, avg 0.353 ms | **1422** 통과 / 1423 드롭 | `init.py` |
| singularity | RUNNING | 4103 | 10.128.7.1 ↔ .2 | **0% 손실**, avg 0.300 ms | **1422** 통과 / 1423 드롭 | `appinit` |
| enroot | RUNNING | 4103 | 10.128.7.1 ↔ .2 | **0% 손실**, avg 0.542 ms | **1422** 통과 / 1423 드롭 | `init.py` |

### GPU 세션 (`.104` + `.112`, 커널당 `cuda.device` 1)

노드당 GPU가 1장이므로 **GPU 제약만으로** 배치가 노드당 하나로 갈린다(CPU 조정 불필요).

| 백엔드 | 세션 | GPU 주입 | 크로스노드 200패킷 | DF 경계 |
|---|---|---|---|---|
| containerd | RUNNING | RTX 4070, `/dev` nvidia 노드 6개 | **0% 손실**, avg 0.251 ms | **1422** / 1423 드롭 |
| singularity | RUNNING | RTX 4070 | **0% 손실**, avg 0.245 ms | **1422** / 1423 드롭 |
| enroot | RUNNING | RTX 4070, `/dev` nvidia 노드 6개 | **0% 손실**, avg 0.218 ms | **1422** / 1423 드롭 |

`.112`는 드라이버(595.84)만 있고 CUDA 런타임이 없어 `cuda.device` 슬롯이 0으로 잡혔다.
`cuda-cudart-13-0` 하나만 설치하면 된다 — 툴킷 전체가 아니라 `libcudart.so.13`이 필요할 뿐이다.

> **이 표가 보이는 것과 보이지 않는 것.** "RTX 4070"은 `.104` 커널에서 읽은 값이다(`.112`의
> 장치는 RTX 3070이다). 즉 이 표는 **GPU가 주입된다**는 것을 보이고, (a) 두 커널이 각각 한 장씩
> 받았는지, (b) 컨테이너가 할당된 장치만 보는지 — 즉 **격리** — 는 보이지 않는다. 후자는 노드당
> GPU가 1장인 이 테스트베드에서는 원리상 잴 수 없다: 호스트도 1장이므로 "1장이 보인다"에 대조군이
> 없다. §8 참조.

### GPU 장치 노드가 백엔드마다 다르다 (결함 아님)

| 백엔드 | 커널 안 `/dev` nvidia 노드 |
|---|---|
| containerd · enroot | 6개 |
| singularity | **4개** — `nvidia0`, `nvidiactl`, `nvidia-uvm`, `nvidia-uvm-tools` |

apptainer 의 `--nvccli` 는 **컴퓨트에 필요한 것만** 넣는다. CUDA 는 그대로 동작한다
(`cuInit` 0, `cuDeviceGetCount` 0 → 장치 1개). 빠진 둘은 `nvidia-modeset`(그래픽 모드셋)과
`nvidia-caps`(MIG 능력 디렉터리)이므로, **MIG 와 OpenGL 워크로드는 singularity 에서 동작하지
않는다** — 그것이 이 차이의 유일한 실질적 의미다.

### CPU 세션 상세

- 오버레이 MTU 1450 = 1500 − VXLAN 50. DF 경계 1422 = 1450 − 28. **설정 없이 정확히 맞는다.**
- LOCAL 브리지도 정상: 커널 안 `eth0 172.30.0.2/26`, 호스트에 `baivx4103`/`baibr4103`/`bailo4103`.
- VXLAN 디바이스는 `dev enp2s0 dstport 4789` — uplink가 `advertised-host`에서 유도되므로 노드마다
  NIC 이름이 달라도(`enp4s0`/`enp2s0`/`enp1s0`) 따로 설정할 것이 없다.

---

## 4. enroot를 띄우기까지 — 두 겹의 벽

enroot만 두 번 더 막혔고, 둘 다 노드 쪽 전제였다. **첫 번째 벽은 진단 자체였다.**

```
RuntimeError: enroot launch exited before pause (rc=1)
```

rc만 있고 런타임이 무엇을 불평했는지가 없다. 그런데 그 stderr는 버려진 것이 아니라 **컨테이너
로그 파일로** 가고 있었다(launch는 파이프가 아니라 로그 fd에 stdout/stderr를 쓴다 — 에이전트
재시작을 넘겨야 하므로). `_wait_ready`가 실패할 때 그 로그의 꼬리를 예외에 실어 주도록 고쳤더니
원인이 한 번에 나왔다.

```
enroot launch exited before pause (rc=1):
enroot-nsenter: failed to create user namespace: Permission denied
```

**두 번째 벽: `enroot-nsenter`에 file caps가 있으면 안 된다.** 동작하던 `.104`를 보니 caps가
`enroot-aufs2ovlfs`와 `enroot-mksquashovlfs` **둘에만** 있었다. `enroot+caps`를 설치하며 `nsenter`와
`switchroot`에도 붙였던 것이 오히려 userns 생성을 막았다 — 에이전트가 root로 돌며 `setpriv`로 커널
uid로 떨어지는 경로에서, 그 caps가 있으면 `unshare(CLONE_NEWUSER)`가 거부된다. `setcap -r`로 떼자
바로 떴다.

`/etc/sub{u,g}id`(uid 1000에 100000:65536)는 세 노드 모두 이미 있었고, `unshare -U`는 uid 1000
직접이든 `setpriv --reuid` 경유든 성공한다 — 즉 userns 자체가 막힌 것이 아니라 **caps가 붙은
바이너리를 그 경로로 실행한 것**이 문제였다.

**정리하면 enroot의 노드 전제는 "caps를 붙이는 것"이 아니라 "정확히 두 바이너리에만 붙이는 것"이다.**

그리고 `enroot+caps` 패키지는 **설치하면 안 된다.** postinst가 네 바이너리 모두에 붙이고(그래서
`nsenter`가 깨진다), 제거하면 prerm이 **두 바이너리의 caps까지 걷어간다**(그래서 enroot가 아예 못
돈다). 둘 다 실측했다. 올바른 절차는 base 패키지만 설치하고 `setcap`을 손으로 두 번 거는 것이다.

| 바이너리 | caps |
|---|---|
| `enroot-aufs2ovlfs` | `cap_dac_override,cap_setpcap,cap_sys_admin,cap_mknod=ep` |
| `enroot-mksquashovlfs` | 동일 |
| `enroot-nsenter` | **없어야 함** |
| `enroot-switchroot` | **없어야 함** |
| `newuidmap` / `newgidmap` | **없어야 함** (setuid-root 그대로 — apptainer 공존 조건) |

## 5. 이 구성이 드러낸 것

### 수정 — 평문 HTTP가 레지스트리를 가리지 않고 강제됐다

`ENROOT_ALLOW_HTTP`도 apptainer의 `--no-https`도 "허용"이 아니라 스킴을 **고정**한다. 둘 다 무조건
붙고 있었으므로 `cr.backend.ai` pull이 포트 80으로 나가 curl 타임아웃까지 30초를 매달렸고, 멀티노드
enroot 세션이 PREPARED에서 멈췄다.

```
curl: (28) Failed to connect to cr.backend.ai port 80 after 30001 ms
```

판정 자체는 **이미 있었다**. `rootless/registry.py`의 메타데이터 probe와 push는 레지스트리별로
스킴을 고르고 있었고(`schemes = ("http",) if ref.insecure else ("https", "http")`), pull 경로만 그것을
보지 않았다. 한 백엔드 안에서 두 정책이 공존한 셈이다.

`is_insecure_registry()`로 판정을 공개하고 양쪽 pull에 연결했다. 테스트 8개.

> **[해결됨]** 여기 남겨둔 둘 다 같은 커밋에서 처리했다. `_credentials_for()`가 예상치 못한
> http 강등에서는 자격증명을 **빼고** 보내고(익명 폴백), 포트 판정은 443을 제외한다.
>
> **[추가 해결]** 휴리스틱 자체를 주 판정에서 내렸다. 이제 `container.registry-hosts-dir`
> (`certs.d`/`hosts.toml` — containerd 백엔드가 이미 transfer service에 넘기는 그 파일)를 먼저 읽고,
> 거기 없는 레지스트리에만 휴리스틱을 쓴다. 휴리스틱만으로는 **기본 포트의 평문 레지스트리**
> (`registry.internal/img` — 읽을 포트가 없어 secure로 판정되어 443으로 나감)를 절대 맞출 수 없었다.

### 수정 — LOCAL 서브넷 저장소가 하드코딩 경로였다 **[진단이 반대였음 — `works.md` §10.1]**

> **이 절의 결론은 틀렸다.** 여기 적힌 `NetworkStateStoreConflict`는 가드가 **옳게** 동작한
> 것이고, 진짜 버그는 그 정상적인 경쟁을 저장소 손상으로 보고한 것이었다. 저장소를
> `var-base-path`로 앵커링한 처방은 노드 전역 조율을 없애 **조용한 네트워크 탈취**를 만들었다
> (한 노드의 두 에이전트가 같은 블록 → 같은 브리지 이름 → 뒤에 뜬 쪽이 앞의 데이터 플레인을
> 가져감). 되돌리고 다르게 고쳤다 — `works.md` §10.1.

한 노드에 백엔드 둘 이상을 띄우면 두 번째 세션이 거부된다.

```
NetworkStateStoreConflict: The on-disk network state store was modified by another writer.
  (local-subnet index 0 exists) — /var/lib/backend.ai/net-local-subnet
```

가드 자체는 옳다 — 두 번째 쓰기를 막는 것이 그 목적이다. 문제는 **경로가 상수**라서
(`local_subnet.py:56`) 같은 노드의 모든 에이전트가 한 저장소를 공유한다는 것이다.
`b690a6791`이 containerd 로그 루트에 한 것과 같은 처방을 적용했다 — 저장소를 에이전트의
`var-base-path` 아래로 앵커링. 우리 설정은 이미 백엔드마다 `var-base-path`가 다르므로
그것만으로 갈린다.

k8s에서는 파드마다 hostPath가 달라 드러나지 않았다. 한 호스트에 여러 백엔드를 올리는
구성(이 문서의 구성, 그리고 단일 노드 개발 환경)에서만 닿는다.

### 결함 — privnet 데몬이 containerd에 하드코딩돼 있었다 **[해결됨]**

> 이 절은 당시 "설계 제약"으로 판정했으나 **오판이었다.** 실제로는 하드코딩이었고
> `8c7eeecbb`에서 백엔드 무관 디스패치로 고쳤다. 아래는 당시 증상 기록이며, 현재 상태는 절 끝을 본다.

비특권 에이전트를 위한 privnet 위임이 rootless 백엔드에서는 성립하지 않았다.

```
privnet/server.py:578  _attach          → containerd/runtime/grpc.py:1169  container_pid
privnet/server.py:290  _live_containers → containerd/runtime/grpc.py:1034  list_container_infos
```

컨테이너의 PID를 **containerd에** 묻는데, enroot/apptainer 컨테이너는 containerd가 모른다. 따라서
**비특권 uid로 도는 rootless 에이전트는 세션 네트워킹을 할 수단이 없다.**

k8s에서 en/sg 파드가 privileged였던 이유가 이것이고(그 configmap 주석이 "privileged fatPod이므로
privnet 생략"이라고 말한다), 이 문서를 쓰던 시점에는 네이티브에서도 에이전트를 root로 돌려
in-process로 처리해야 떴다.

**현재 (해결 후)** — privnet은 노드가 실제로 돌리는 백엔드의 런타임을 discovery에서 받아 쓴다
(`8c7eeecbb`). rootless 컨테이너의 PID는 컨테이너 저널에서 나오고, 저널을 에이전트가 쓰므로 세 겹의
경계가 추가로 걸린다 — netns의 userns 소유자 검증(`ca89a6485`), 세션 결속(`9763329e2`),
cgroup 조작 대상 PID의 uid 검증(`828eee355`). 그리고 cgroup 위임이 붙으면서 rootless의
`memory.max = max` 문제도 같이 닫혔다. **에이전트 탈특권은 이제 세 백엔드 모두에서 가능하다.**

### 버그 — aiomonitor 포트 충돌이 기동을 멈춘다

`aiomonitor_webui_port`가 39200 고정이라 한 호스트에 에이전트를 둘 이상 띄우면 두 번째가
`Using uvloop as the event loop backend` 직후 **영원히 멈춘다**. 크래시가 아니라 행이라 프로세스는
살아 있고 등록만 안 된다.

```python
try:
    monitor.start()
    aiomon_started = True
except Exception as e:
    log.warning("aiomonitor could not start but skipping this error to continue", exc_info=e)
```

`monitor.start()`는 UI를 **스레드에서** 띄우므로 bind 실패가 이 `except`에 걸리지 않는다. 로그에는
`OSError: [Errno 98] ... 39200` 트레이스백이 찍히는데 기동은 진행되지 않는다. 에이전트별
`aiomonitor-webui-port`/`-termui-port`로 우회했지만, **실패가 무시되지 않고 행으로 이어지는 것**이
문제다.

### 수정 — launch 실패가 원인을 지웠다

`_wait_ready`가 returncode만 담아 던지고 있었다. 런타임의 stderr는 컨테이너 로그에 있으므로,
실패 시 그 꼬리(15줄)를 예외에 싣도록 했다. 4절의 두 번째 벽은 이 수정 **직후** 드러났다 —
그전까지 같은 `rc=1`을 세 번 보면서 원인을 몰랐다.

### 환경 — enroot 헬퍼 caps는 4절 표대로

`enroot+caps` 설치만으로는 부족하고(postinst의 세트가 좁다), 반대로 네 바이너리 전부에 붙이면
`nsenter`가 userns를 못 만든다. 정확히 두 개에만 붙여야 한다.

### 재확인 — `agent_list`는 배치 지정이 아니라 후보 풀

`["i-cd-104","i-cd-112"]`로 요청해도 스케줄러가 bin-pack해 **두 커널이 한 노드에** 갔다. 노드당
하나로 만들려면 `2 × (커널당 CPU) > 각 노드의 여유`가 되어야 한다.

---

## 6. 재현

```bash
# 1) k8s 내리기 (노드마다)
kubectl scale deploy -n bai --replicas=0 --all
sudo systemctl stop kubelet
sudo ctr -n k8s.io tasks ls | tail -n +2 | awk '{print $1}' | xargs -I{} sudo ctr -n k8s.io tasks kill -s SIGKILL {}
sudo ctr -n k8s.io containers ls -q | xargs -I{} sh -c 'sudo ctr -n k8s.io tasks delete --force {}; sudo ctr -n k8s.io containers rm {}'
sudo ip link del flannel.ipip; sudo ip link del cni0
for r in 10.244.{0,1,2,3}.0/24; do sudo ip route del $r; done
# containerd 는 멈추지 말 것

# 1b) enroot 노드 프로비저닝 — `enroot+caps` 는 설치하지 말 것
sudo apt-get install -y ./enroot_4.2.1-1_amd64.deb     # base 만
CAPS=cap_dac_override,cap_setpcap,cap_sys_admin,cap_mknod+pe
sudo setcap $CAPS /usr/bin/enroot-aufs2ovlfs
sudo setcap $CAPS /usr/bin/enroot-mksquashovlfs
# enroot-nsenter / enroot-switchroot / newuidmap / newgidmap 에는 붙이지 않는다

# 1c) GPU 노드 — 툴킷 전체가 아니라 런타임만
sudo apt-get install -y cuda-cudart-13-0

# 2) 매니저 (halfstack 인프라는 그대로 둔 채)
./dev start mgr

# 3) 에이전트 — 백엔드마다 포트/경로를 분리하고 aiomonitor 포트를 반드시 다르게
#    이 측정 당시: containerd 는 root (containerd 소켓), enroot/singularity 도 root (privnet 미사용).
#    현재: privnet 이 세 백엔드를 모두 구동하므로 enroot/singularity 는 uid 1000 +
#    network-privnet-socket 으로 돌릴 수 있다 (5절 privnet 항목 참조).
sudo -n env PYTHONPATH=$PWD/src ./py -m ai.backend.cli ag start-server -f agent-cd-104.toml
```

포트 배치: containerd `6211/6203/6207/6219` · enroot `6011/6003/6007/6019` ·
singularity `6111/6103/6107/6119`, aiomonitor는 `38200+n`/`39200+n`.

---

## 7. 왜 잔재가 쌓였나

이 기준선을 세우며 앞선 실험들의 잔재를 걷어냈다 — etcd 세션 네트워크 키 125개(살아있는 세션은
1개), `.156`의 오버레이 디바이스 10개, containerd 고아 컨테이너 28개, 그리고 **14일째 돌고 있던
관리되지 않는 에이전트 하나.** 네 가지 원인이 겹쳤고, 셋은 코드 쪽이다.

### 정리 책임이 "정상 종료 경로"에만 붙어 있다

14일 된 그 에이전트에 SIGTERM을 보내니 **즉시 스스로 매니저에서 빠졌다.** 정상 경로는 멀쩡하다.
남아 있던 이유는 아무도 정상적으로 죽이지 않았기 때문이다 — 부모 tmux가 죽고 systemd에 입양돼
계속 하트비트를 보냈다. `./dev`는 tmux로 띄우지만 **프로세스는 tmux와 함께 죽지 않는다.**

같은 구조로 `kubectl scale --replicas=0`은 파드를 죽이지만 vxlan/bridge 디바이스는 **파드 밖
호스트**에 있다. teardown이 완주하지 못하면 그대로 남는다.

### 리컨사일러는 있는데 마지막 한 걸음에서 막힌다

`sync_container_lifecycles`가 10초마다 돌고 "레지스트리에 없는 살아있는 컨테이너 → DESTROY"
경로가 실제로 구현돼 있다(`agent.py:1942`). 그런데 그 고아를 지우려 하면:

```
runc did not terminate successfully: exit status 1: unable to signal init: permission denied
```

**runc가 자기 init 프로세스에 시그널을 못 보낸다.** 그러면 그 위 모든 계층 — `ctr`, 에이전트
리컨사일러, 매니저 — 이 전부 조용히 실패한다. 결국 호스트에서 `kill -9` 로만 지워졌다.

### 근본 원인: 우리가 물린 MAC 프로파일이었다 — 그래서 걷어냈다 **[해결됨]**

커널 감사 로그가 지목한 것은 containerd 백엔드가 **혼자** 커널에 물리던 AppArmor 프로파일
(`backendai-default`)이었다. Ubuntu 24.04 가 배포하는 `/etc/apparmor.d/runc` 는 권한은 그대로 둔 채
runc 의 레이블만 `unconfined` 에서 `runc` 로 바꾸는데, 우리 프로파일은 그 레이블로 매칭하고 있었다.
결과적으로 **이런 호스트의 모든 containerd 커널이 강제 회수 불가** 상태였다. 갓 만든 정상 컨테이너에
`ctr tasks kill -s SIGCONT` 만 해도 재현됐다.

당시에는 프로파일의 규칙을 고쳐서 닫았다(`f1cb28483`). **그 뒤 전제 자체가 틀렸다는 것이 확인됐다** —
Backend.AI 의 레퍼런스인 Docker 백엔드는 AppArmor 프로파일을 **한 번도 지정하지 않는다**
(`docker/agent.py` 는 jail 일 때 `apparmor=unconfined` 만 준다). "dockerd 의 docker-default 와 맞춘다"
는 것이 이 기능의 근거였는데, 맞출 대상이 애초에 없었다.

그래서 containerd 백엔드에서 AppArmor 를 통째로 제거했다 — `containerd/apparmor.py`, OCI 스펙의
`apparmorProfile` 배선, 기동 시 `apparmor_parser` 로드까지. **이 결함은 우리가 스스로 만든 것이고,
원인을 없애는 쪽이 규칙을 고치는 쪽보다 옳다.** 커널의 격리는 그대로 남는다 — 능력 집합, seccomp
프로파일(Docker 도 쓰는 것), 네임스페이스, cgroup 은 전부 유지된다.

### 그 실패가 어디에도 잡히지 않는다

```
backendai_sync_container_lifecycle_trigger_count_total{i-cd-104} 1024
backendai_sync_container_lifecycle_success_count_total{i-cd-104}  292
backendai_sync_container_lifecycle_failure_count_total            (없음)
```

**세 카운터의 단위가 서로 다르다.** trigger 는 스윕 1회당 +1, failure 는 예외 1건당 +1인데,
success 는 `inc(amount=num_synced_kernels)` — **동기화된 커널 수**만큼 오른다. 나란히 두면
"1024번 돌아 292번 성공"으로 읽히지만 실제로는 "1024번 돌면서 커널 292개를 정리했다"는 뜻이다.
(유휴 에이전트에서 60초를 관찰하면 trigger 만 6 오르고 success 는 0에 머무는데, 그것이 정상이다.)

그래서 **회수가 실패해도 이 메트릭에는 아무 흔적이 없다.** 실패는 큐 처리기에서 나고 이 메트릭은
스윕만 본다. 이름이 나란한 만큼 오해를 부르는 조합이다.

그리고 로그가 남지 않는다. `./dev` 와 이 문서의 기동 방식 모두 `| tee logs/...` 라 **에이전트를
재기동할 때마다 로그가 잘린다.** 회수 시도 기록도 그렇게 사라진다.

### 결함으로 볼 만한 것

| # | 항목 | 상태 |
|---|---|---|
| 1 | **리컨사일러의 "성공"이 회수를 보증하지 않는다.** enqueue 성공을 sync 성공으로 센다 | **[해결됨]** 커널 수를 `synced_kernel_count`로 분리하고 "enqueued, not reclaimed"를 documentation에 명시 (`works.md` §9.5) |
| 2 | **회수 불가 컨테이너를 아무도 보고하지 않는다.** 위 시그널 차단 건이 몇 주를 갔는데 신호가 없었다 | **[해결됨]** `unreclaimed_containers` 게이지 + 리컨사일러의 destroy 재발행 (`works.md` §9.4) |
| 3 | trigger / success / failure 의 단위가 달라 나란히 읽으면 오해를 부른다 (success 는 커널 수) | **[해결됨]** 셋 다 스윕 단위로 통일 |

---

## 8. 미검증 (이 문서 시점)

- **오버레이 암호화·포트 오버라이드.** 기본값(4789 평문)만 쟀다. → **[해결됨]** 이후 세 백엔드
  모두에서 측정했다 (포트 4790 오버라이드, 와이어 ESP만·SA 2, 암호화 후 MTU 1412 / DF 1384).
  `works.md` §2 표.
- **NCCL.** GPU 주입과 크로스노드 경로는 확인했지만 실제 all-reduce는 돌리지 않았다
  (`cni-features.md` 4절의 하네스를 그대로 쓸 수 있다). → 여전히 미측정.
- **단일노드 클러스터 세션.** `cni-features.md` 9절의 미검증 항목 그대로. → 여전히 미측정.
- **GPU 격리.** 3절의 "GPU 주입"은 주입을 보였을 뿐 **격리는 보이지 않았다.** 노드마다 GPU가
  1장이므로 "커널이 1장을 본다"는 호스트와 같은 값이고 대조군이 없다. 2장 노드에서 1장 할당하거나
  0장 할당 시 0장이 보이는 대조군이 있어야 격리를 주장할 수 있다.
