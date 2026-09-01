# works.md — 2026-08-28 작업 정리

**한 줄: CNI를 걷어낸 순수 VXLAN 기준선에서 3개 백엔드 × (CPU·GPU) 6칸을 통과시켰고, 그 과정에서
드러난 결함 11건을 고쳐 14개 커밋으로 올렸다. 푸시는 안 했다.**

브랜치 `feat/containerd-network-v2-rebased`. 배경은 `cni-features.md`(CNI 9종 × 3 백엔드),
기준선 측정은 `non-cni-features.md`(단, 이 문서는 오늘 오후 이후 내용이 아직 빠져 있다 — §5 참조).

---

## 1. 테스트베드를 통째로 바꿨다

| | 이전 | 지금 |
|---|---|---|
| 오케스트레이션 | k8s (파드 안 에이전트) | **없음** — 호스트에 네이티브 |
| 언더레이 | flannel-ipip | **물리 LAN만** (MTU 1500) |
| 노드 | 4 | 3 (`.104` `.112` `.156`) |
| 에이전트 | 9 (파드) | 9 (3 백엔드 × 3 노드) |

**내린 절차** (재현은 `non-cni-features.md` §6):
`kubectl scale --replicas=0` → 4노드 `systemctl stop kubelet` → k8s 컨테이너 레코드 제거 →
`flannel.ipip`·`cni0`·pod CIDR 라우트 삭제. **`containerd` 데몬은 멈추면 안 된다**(containerd 백엔드가 쓴다).

**컨트롤 플레인**: manager `:8091`, storage-proxy `:6021/:6022`, webserver `:8090`,
app-proxy `:10200/:10201`, halfstack(db 8101 / etcd 8121 / valkey 8111).
etcd의 storage-proxy 주소를 `127.0.0.1` → `192.168.0.104`로 올려야 원격 에이전트가 닿는다.

**노드 프로비저닝** — 이것들은 코드가 아니라 배포 전제다.

| 항목 | 내용 |
|---|---|
| enroot | base 패키지만 설치. **`enroot+caps`는 설치하지 말 것** — postinst가 네 바이너리에 caps를 붙여 `nsenter`가 깨지고, 제거하면 prerm이 필요한 caps까지 걷어간다 (둘 다 실측) |
| enroot caps | `cap_dac_override,cap_setpcap,cap_sys_admin,cap_mknod+pe` 를 **`enroot-aufs2ovlfs`와 `enroot-mksquashovlfs` 두 개에만**. `nsenter`/`switchroot`/`newuidmap`/`newgidmap`에는 붙이면 안 된다 |
| GPU 노드 | 툴킷 전체가 아니라 `cuda-cudart-13-0` 하나면 된다 (`libcudart.so.13`) |
| privnet | uid 1000 + `CAP_NET_ADMIN,SYS_ADMIN,SYS_PTRACE,DAC_READ_SEARCH,DAC_OVERRIDE` |

---

## 2. 검증 결과 — 6칸 전부 통과

`cluster_size 2` 멀티노드. GPU는 노드당 1장이라 GPU 제약만으로 노드당 커널 1개가 된다.

| 축 | containerd | enroot | singularity |
|---|---|---|---|
| 멀티노드 세션 | ✅ | ✅ | ✅ |
| GPU 주입 | ✅ RTX 4070, 장치 1 | ✅ | ✅ |
| GPU 격리 | ⚠️ **안 쟀음** — 노드당 1장이라 대조군 없음 (§6) | ⚠️ | ⚠️ |
| 크로스노드 200패킷 | ✅ 0% | ✅ 0% | ✅ 0% |
| DF 경계 (mtu−28) | ✅ 1422/1423 | ✅ | ✅ |
| 피어 TCP (오버레이 `:2200`) | ✅ dropbear | ✅ | ✅ |
| VXLAN 포트 오버라이드 | ✅ 4790 | ✅ | ✅ |
| 오버레이 암호화 | ✅ 와이어 ESP만, SA 2 | ✅ | ✅ |
| 암호화 후 MTU/DF | ✅ 1412 / 1384 | ✅ | ✅ |
| MTU 가드 | ✅ `OverlayMtuTooLarge` 로 거부 | 공용 코드 | 공용 코드 |
| IPC 격리 | ✅ | ✅ | ✅ (PID 1 포함) |
| 좀비 회수 (대조군 5) | ✅ 0 | ✅ 0 | ✅ 0 |
| cgroup 한도 적용 | ✅ | ✅ | ✅ |
| 종료 후 잔재 | ✅ 0 | ✅ 0 | ✅ 0 |

**설정이 하나도 필요 없는 첫 구성이다.** 언더레이가 진짜 1500이라 매니저 기본값(오버레이 1450)이
그대로 맞는다. `cni-features.md` §7의 처방 9개 중 필요한 것이 0개.

### 네임스페이스 감사 (8종 × 3 백엔드)

| | containerd | enroot | singularity |
|---|---|---|---|
| mnt·uts·ipc·pid·net·cgroup | 격리 | 격리 | 격리 (cgroup은 `--ipc` 이후 확인 필요) |
| user | **호스트 공유**(runc 설계) | 격리 | 격리 |
| time | 공유 (Docker도 동일, 결함 아님) | 공유 | 공유 |
| CapEff | `0` (전부 없음) | `1ffffffffff` (userns 안) | 동일 |
| Seccomp | 2 (필터 적용) | 2 | 2 |

---

## 3. 고친 것 — 커밋 14개

```
9763329e2 fix(agent): refuse to attach a container that belongs to another session
828eee355 fix(agent): delegate the rootless cgroup to the privnet
ca89a6485 fix(agent): ask the kernel which netns the agent may point privnet at
f14fa99ab fix(agent): anchor the IPAM and privnet stores to var-base-path too
8c7eeecbb fix(agent): let privnet drive whichever backend the node runs
c1f59bb20 docs: add the CNI-free VXLAN baseline, and what it found
1cd6efee9 test(agent): cover three Docker-parity gaps on the containerd backend
88c04e43f fix(manager): record why an agent refused to create kernels
26d1d688b fix(agent): skip aiomonitor when its port is taken instead of hanging
f1cb28483 fix(agent): let a privileged host process signal a confined kernel
740913436 fix(agent): stop reporting a failed destroy as a clean one
cacf4053b fix(agent): anchor the LOCAL subnet store to var-base-path
6d6bdc1a1 fix(agent): give a rootless launch its own IPC namespace, and a reason when it fails
c869f182f fix(agent): gate the plain-HTTP registry scheme per registry
```

### 성격별로

**보안·정확성**

| 결함 | 증상 | 커밋 |
|---|---|---|
| 평문 HTTP가 레지스트리를 가리지 않고 강제 | `ENROOT_ALLOW_HTTP`/`--no-https`는 "허용"이 아니라 스킴을 **고정**. `cr.backend.ai` pull이 포트 80으로 30초 타임아웃 → 세션이 PREPARED에서 멈춤. 판정은 이미 있었고 pull 경로만 안 보고 있었다 | `c869f182f` |
| https 실패 시 http 폴백에 자격증명 재전송 | TLS가 깨진 것만으로 평문에 계정이 나감 | `c869f182f` |
| `":" in registry` 휴리스틱 | `registry.example.com:443`을 insecure로 판정 | `c869f182f` |
| **우리가 물린 MAC 프로파일이 runc의 시그널을 차단** | containerd 백엔드만 커널에 AppArmor(`backendai-default`)를 물리고 있었다. Ubuntu 24.04가 runc를 `flags=(unconfined)` 프로파일로 **레이블만** 바꿔 `peer=unconfined` 규칙이 안 맞음 → **모든 containerd 커널이 강제 회수 불가**. 정상 종료는 러너가 스스로 빠져서 가려졌다 | `f1cb28483` → **이후 §8에서 AppArmor 자체를 제거** |
| privnet이 다른 세션 컨테이너에 attach 가능 | 세션 결속 미확인 | `9763329e2` |
| privnet이 에이전트가 댄 pid를 그대로 신뢰 | rootless는 저널이 에이전트 소유라 위조 가능 → **커널에 netns의 userns owner uid를 물어** 범위를 묶음 | `ca89a6485` |

**격리·자원**

| 결함 | 증상 | 커밋 |
|---|---|---|
| **IPC 격리 없음** | enroot는 `--ipc`가 `/dev/log`로 하드 실패해 미적용, singularity는 `--contain`이 해준다는 **근거 없는 기술**. 실측: 두 커널과 호스트가 모두 `ipc:[4026531839]` | `6d6bdc1a1` + apptainer `--ipc` |
| **rootless cgroup 미적용** | 비특권 에이전트가 `/sys/fs/cgroup`에 못 써서 `memory.max=max`, `Cpus_allowed_list: 0-31`. 한도가 안 보이는 게 아니라 **아예 안 걸렸다** | `828eee355` |

**운영·관측**

| 결함 | 증상 | 커밋 |
|---|---|---|
| destroy 실패를 성공처럼 정리 | `finally`에서 CLEAN 발행 → 컨테이너는 살아있는데 레지스트리에서 사라짐 | `740913436` |
| 회수 실패를 `self-terminated`로 기록 | 40분 살아있던 고아가 "스스로 끝남"으로 남음 | `740913436` |
| launch 실패가 stderr를 버림 | `rc=1`만 남음. 고치자마자 enroot의 진짜 원인이 나옴 | `6d6bdc1a1` |
| 매니저가 에이전트 거부 사유를 버림 | `gather(return_exceptions=True)`가 어느 에이전트인지만 기록 → 세션이 `PREPARED/scheduled`로 방치 | `88c04e43f` |
| aiomonitor 포트 충돌이 기동을 멈춤 | 스레드 안 bind 실패가 `except`에 안 잡혀 **행**. 한 호스트에 에이전트 둘이면 재현 | `26d1d688b` |
| 하드코딩 경로 4곳 | LOCAL 서브넷 / privnet 저널 / IPAM / 어태처의 별도 IPAM 핸들이 전부 `/var/lib/backend.ai/*` 상수 → 멀티백엔드 노드 충돌 + 비특권 실패 | `cacf4053b`, `f14fa99ab` |
| privnet이 containerd 하드코딩 | rootless 컨테이너의 pid를 containerd에 물어 rootless 위임이 불가능 | `8c7eeecbb` |

**테스트 공백** — `1cd6efee9` 외 대부분의 수정에 회귀 테스트를 동반했다. 다만 뮤테이션 테스트로
재점검한 결과 **13개 수정 중 4개는 테스트가 0개였고, 있던 테스트 중 셋은 검증력이 없었다.**
이후 보강했다 — 아래 §7.

### 짚어둘 것: 테스트가 깨진 동작을 고정하고 있던 사례 2건

- `assert "--no-https" in argv` — 무조건 평문을 계약으로 박아둠
- `assert "signal (receive) peer=unconfined," in profile` — 문법만 보고 그 레이블이 실제로 매칭되는지는 아무도 확인 안 함

둘 다 실제 요구사항을 검증하는 테스트로 교체했다.

---

## 4. 결함이 아니었던 것 (조사 완료, 조치 불요)

| 항목 | 판정 |
|---|---|
| `registry-hosts-dir`가 안 먹는다 (`cni-features.md` §10 "열림") | **닫힘.** 코드는 정상, `certs.d` hostPath 마운트가 배포에서 빠졌던 것 |
| singularity `/dev` nvidia 노드 4개 vs 6개 | 컴퓨트에 필요한 4개가 전부. `cuInit`/`cuDeviceGetCount` 정상. 빠진 둘은 `nvidia-modeset`(그래픽)·`nvidia-caps`(MIG) → **MIG·OpenGL만 불가** |
| rootless `NoNewPrivs=1` | `--fakeroot`로 컨테이너 안 uid가 0이라 `sudo` 자체가 불필요. 실패 사유도 NNP가 아니라 `/etc/sudo.conf` 소유권 |
| `sync_container_lifecycle` trigger 1024 vs success 292 | **단위가 다름** — success는 `inc(amount=num_synced_kernels)`, 즉 정리한 **커널 수**. 유휴 시 0이 정상 |
| cgroup 누적 | **누적 0.** `ls | wc -l`이 자식 cgroup이 아니라 인터페이스 파일을 센 것 |
| `pids.max = max` (3 백엔드) | 코드에 pids 한도 개념 자체가 없음 → 버그가 아니라 **새 리소스 축 기능**. Docker도 안 걺 |

---

## 5. 앞으로 할 일

### 5.1 바로 해야 하는 것

| # | 항목 | 비고 |
|---|---|---|
| 1 | ~~**`non-cni-features.md` 갱신**~~ **완료** | 헤더에 시점 경고, privnet 절을 "결함(해결됨)"으로 정정, 자격증명/포트 판정 해결 표시, §6 재현의 root 전제 갱신, §8에 암호화 해결 + GPU 격리 미측정 추가, `default-driver="cni"`가 k8s CNI가 아님을 명시 |
| 2 | **news fragment (`changes/`)** | 14개 커밋 중 사용자 영향 있는 것들. PR 올릴 때 한 번에 |
| 3 | **루트의 문서 3개 위치** | `cni-features.md`, `non-cni-features.md`, `works.md`가 리포 루트에 있다. `CLAUDE.md`의 문서 구조 규칙(AGENTS/CONTEXTS/README)에 안 맞음 → `proposals/` 또는 `src/ai/backend/agent/CONTEXTS.md` 쪽 |
| 4 | **푸시 + PR** | 아직 로컬에만 있다 |

### 5.2 미측정 축 (코드는 있으나 이 구성에서 안 쟀다)

| 항목 | 왜 |
|---|---|
| **NCCL all-reduce** | GPU 주입과 크로스노드 경로는 봤지만 실제 학습은 안 돌렸다. `cni-features.md` §4의 하네스를 그대로 쓸 수 있다 |
| **도달성 프로브** | udp/4789 차단 시 침묵이 아니라 로그로 보고하는지. 방화벽 조작 필요 |
| **로그 로테이션 상한·구멍** | `session logs` 서빙만 봤다. rootless의 420 KiB/s 소프트 캡은 `cni-features.md` §5 측정을 그대로 적용 중 |
| **commit / 이미지 push** | singularity commit(whiteout 포함)과 인증 붙은 레지스트리 push |
| **단일노드 클러스터 세션 통신** | 한 노드에 커널 2개인 세션이 실제로 통신되는지. containerd의 `create_local_network`가 no-op이라 세션 네트워크만으로 서야 한다 |
| **containerd 커널의 netns owner** | rootless만 쟀다. 소유자 검증을 containerd에 적용하지 않는 근거를 굳히려면 필요 |

### 5.3 알려진 미해결

| 항목 | 성격 |
|---|---|
| **etcd 인증 없음** | 에이전트가 uid 1000으로 아무 키나 쓴다 — 다른 노드 VTEP·플러그인 설정·암호화 키까지. **오늘 나온 것 중 가장 큰 보안 항목이고, 이 브랜치 밖**(매니저·전 컴포넌트) |
| `pids.max` 상한 | 포크밤 방어. 기능으로 설계 필요 |
| singularity PID 1의 IPC | `--ipc`로 닫았으나, `appinit`이 우리 게이트보다 먼저 뜨는 구조 자체는 그대로 |
| privnet 신뢰 모델 | 한도 **값**은 여전히 에이전트가 정한다. 권한 격리지 할당 검증이 아니다 — 주석에 명시해 둠 |
| 원격 노드 코드 관리 | `.112`는 git repo가 아니고(rsync 사본), `.156`은 옛 커밋 위에 덮어썼다. 재현 가능한 상태가 아니다 |

### 5.4 테스트베드 복구

k8s로 되돌리려면: 4노드 `systemctl start kubelet` → 파드 자동 복귀 →
`kubectl scale deploy -n bai --replicas=1 <각 배포>`.
`postgres`/`etcd`는 hostPath라 데이터가 남아 있다. 배포 replica 원본은
`$SCRATCHPAD/restore/deploy-replicas.txt`, 전체 매니페스트는 `restore/bai-all.yaml`.

---

## 6. 측정 방법에 관한 경고 (이번에 다섯 번 틀렸다)

전부 **잘못된 대상을 재서** 결론이 뒤집힌 경우다. 다음 사람이 같은 함정을 밟지 않도록 남긴다.

| 잘못 잰 것 | 왜 틀렸나 | 올바른 방법 |
|---|---|---|
| singularity IPC "격리됨" | netns 보유자(`appinit`)만 보고 그 아래를 안 봄 | 컨테이너 안 **모든** 프로세스의 ns id를 보고, 세그먼트 가시성으로 기능 확인 |
| `nproc=32`라 CPU 제한 안 됨 | `nsenter`로 만든 **새 프로세스**는 내 cgroup·affinity를 물려받음 | 커널 프로세스의 `/proc/<pid>/status`를 호스트에서 직접 |
| `ipcs`로 IPC 공유 확인 | `nsenter`에 `-i`를 안 줘 호스트 IPC ns를 읽음 | `nsenter -t PID -i` |
| cgroup "85개/86개 누적" | `ls | wc -l`이 자식 cgroup이 아니라 **인터페이스 파일**을 셈 | `find -mindepth 1 -maxdepth 1 -type d` |
| 좀비 회수 "0개라 정상" | **대조군이 없어 검출력 0** | 부모가 살아서 wait 안 하는 대조군이 좀비를 **보여야** 함 (5개 확인 후에야 유효) |

그리고 `cni-features.md`에 IPC 항목이 아예 없었던 것처럼, **표에 없는 축은 "통과"가 아니라 "안 쟀음"**이다.
목록을 스스로 정해놓고 "모든 칸 통과"라고 쓰지 말 것.

---

## 7. 테스트 재점검 (뮤테이션 테스트, 8/29)

§6의 "표에 없는 축은 안 쟀음"을 **유닛 테스트에도 적용**했다. 지적한 코드를 망가뜨린 뒤
`pants test tests/unit/agent/::`가 여전히 통과하는지 봤다. **6건 전부 생존했다** — 즉 그 코드는
테스트되고 있지 않았다.

| 뮤턴트 | 재점검 전 | 보강 후 |
|---|---|---|
| `netns.py` 소유자 검사 `if False:` | 통과 (생존) | ✅ 사망 |
| `server.py` `_make_cgroup` → `return` | 통과 (생존) | ✅ 사망 |
| `server.py` `_require_agents_process` → `return` | 통과 (생존) | ✅ 사망 |
| `agent.py` `else:` → `finally:` (수정 이전) | 통과 (생존) | ✅ 사망 |
| `seccomp_installer.py` `unshare(CLONE_NEWIPC)` → `unshare(0)` | 통과 (생존) | ✅ 사망 |
| `session_network.py` `local_subnet_state_dir = None` | 통과 (생존) | ✅ 사망 |
| `containerd/agent.py` `UNKNOWN` → `SELF_TERMINATED` | 통과 (생존) | ✅ 사망 |

### 왜 통과했나 — 세 가지 패턴

| 패턴 | 실례 |
|---|---|
| **앞 분기에 가려짐** | `test_netns_owner.py`가 자기 PID(호스트 netns)로 물어서 소유자 검사 **이전**의 host-netns 거부에 걸렸다. 실측 메시지가 `'target resolves to the host netns'`. 게다가 `or`로 두 메시지를 다 받아 영원히 초록불 |
| **와이어 포맷만 검증** | cgroup 위임의 유일한 테스트가 `PrivNetRequest`의 JSON 왕복이었다. 데몬의 cgroup 코드를 통째로 지워도 통과 |
| **소스 텍스트 grep** | IPC 격리를 `assert "CLONE_NEWIPC = 0x08000000" in src`로 확인. 같은 파일의 seccomp 테스트는 BPF를 인터프리터로 **실행**하는데 IPC만 문자열 검사였다 |

### 보강한 것

- `test_netns_owner.py` — `unshare -r -n`로 실제 비-호스트 netns를 만들어 수락/거부/`None` 3방향
- `test_privnet.py::TestConfiningAContainer` — `CONFINE_CONTAINER`를 데몬까지 태워 limit 실제 기록·프로세스 이동·타 uid PID 거부·경로 탈출 id 거부 검증
- `test_destroy_lifecycle.py` (신규) — destroy 실패 시 CLEAN 미발행·레지스트리 잔류·`done_future` 예외
- `test_task_exit_reason.py` (신규) — exit 이벤트의 사유가 `UNKNOWN`인지 (성공 대조군 포함)
- `test_seccomp.py` — grep 2건을 **실행 후 `/proc/self/ns/ipc` 비교**로 교체
- `test_session_network.py` — 세 저장소가 전부 `var-base-path` 아래로 가는지

### 같이 고친 코드

| 대상 | 내용 |
|---|---|
| `privnet/server.py` `_make_cgroup` | 모든 쓰기가 `suppress(OSError)`였다 — **고치려던 결함(`memory.max=max`가 조용히 안 걸림)을 위임 경로가 그대로 재현**하고 있었다. 실패한 limit을 모아 보고하고, 아무도 cgroup에 못 들어간 경우도 실패로 친다. `_remove_cgroup`의 EBUSY도 경고 |
| `rootless/base.py` `_confine_via_privnet` | docstring이 `"no fallback ... prevent"`라고 했지만 실제로는 로그만 남기고 커널을 띄운다(로컬 경로와 동일한 best-effort). 문서를 사실에 맞추고, `except Exception`을 좁혔다 — 넓은 except가 **이 메서드 자신의 `AttributeError`까지 "privnet could not confine"으로 기록**해 오타 하나로 모든 한도가 영구히 사라질 수 있었다 |
| `rootless/registry.py` | 평문 HTTP 판정을 휴리스틱에서 `container.registry-hosts-dir`(`certs.d`/`hosts.toml`)로 옮겼다. 휴리스틱은 **기본 포트의 평문 레지스트리**(`registry.internal/img`)를 원리상 맞출 수 없어 443으로 나갔다. containerd 백엔드가 이미 같은 파일을 쓰므로 한 노드가 백엔드와 무관하게 같은 답을 낸다 |
| `privnet/server.py` 모듈 docstring | 신뢰 모델이 `"re-resolves the container PID from containerd (authoritative)"`로 낡아 있었다. 백엔드 무관 + netns 소유자·세션 결속·PID uid 세 경계를 명시 |
| `test_aiomonitor_ports.py` | 두 번째 포트로 `free + 1`을 써서 flaky했다. 둘 다 커널에서 받도록 |

### 남는 축 (여전히 안 쟀음)

- **GPU 격리** — 2장 노드에서 1장 할당, 또는 0장 할당 시 0장이 보이는 대조군이 필요하다
- **`--contain`이 IPC를 안 덮는다는 전제** — apptainer 쪽은 argv에 `--ipc`가 있는지만 본다

---

## 8. AppArmor 제거 (8/29)

**Backend.AI는 원래 AppArmor를 쓰지 않는다.** 레퍼런스인 Docker 백엔드는 프로파일을 한 번도
지정하지 않고(`docker/agent.py`는 jail일 때 `apparmor=unconfined`만 준다), containerd 백엔드만
혼자 `backendai-default`를 물리고 있었다. §3의 "AppArmor가 runc의 시그널을 차단" 결함은
**그 기능이 있었기 때문에만 존재한 결함**이다 — 우리가 만들고 우리가 고친 것이다.

"dockerd의 docker-default와 맞춘다"가 그 기능의 유일한 근거였는데, 맞출 대상이 애초에 없었다.
그래서 규칙을 고치는 대신(`f1cb28483`) 원인을 제거했다.

| 제거 | |
|---|---|
| `containerd/apparmor.py` | 삭제 (프로파일 렌더러 + `apparmor_parser` 로더) |
| `containerd/agent.py` | 기동 시 `ensure_profile_loaded()`, `_apparmor_profile` 필드 2곳, 커널 생성자 인자, OCI 스펙 주입 |
| `containerd/runtime/spec.py` | `process.apparmorProfile` 배선 |
| `tests/.../test_apparmor.py` | 삭제 |
| `test_runtime_spec.py::TestAppArmor` | 삭제 |

**격리는 그대로다.** 능력 집합, seccomp 프로파일(Docker도 쓰는 것), 네임스페이스, cgroup 한도는
전부 유지된다. 빠진 것은 Docker 백엔드에도 없던 MAC 레이어 하나뿐이다.

§7의 "AppArmor 시그널 실매칭은 유닛 테스트로 확인 불가" 항목은 이로써 **소멸**했다 — 잴 대상이
없어졌다.

---

## 9. 안전성·기능 커버리지 보강 (8/29)

§7이 코드를 뮤테이션으로 재점검했다면, 이번에는 **무엇이 테스트되지 않고 있는지**를 신뢰 모델과
리컨사일러 쪽에서 재봤다. 기능면(VXLAN)은 이미 촘촘했고 — `test_vxlan.py`가 암호화 빌더/해체,
MTU 가드, 포트 오버라이드, 도달성 프로브, xfrm까지 클래스 15개로 덮는다 — 구멍은 안전성 쪽에
몰려 있었다.

### 9.1 실측된 취약점 — privnet 저널이 IPsec 키를 world-readable로 저장

```
0775  journal/sessions
0664  journal/sessions/sess-a
      {"backend":"vxlan", ..., "encryption_key":"dede…"}   ← 64-hex IPsec 키
```

`record_session()`이 검증된 network_config를 **통째로** JSON으로 쓰는데 `_write()`에 `chmod`가 없어
umask에 맡겨져 있었다. privnet은 노드에서 `CAP_NET_ADMIN`을 가진 유일한 컴포넌트인데, 소켓은
`0600`으로 잠그면서(`server.py:306`) 저널은 안 잠갔다.

키를 뺄 수는 없다 — privnet은 설계상 etcd 클라이언트를 갖지 않으므로 이 저널이 재시작 후 세션을
복원할 **유일한** 내구 기록이다. 그래서 잠갔다: 디렉터리 `0700`, 파일은 `os.open(..., 0o600)`으로
**생성 시점부터** 0600(생성 후 chmod는 읽을 수 있는 창을 남긴다). 이전 릴리스가 남긴 열린 트리도
매 쓰기마다 조인다 — `mkdir(mode=)`는 이미 존재하는 디렉터리에 적용되지 않는다.

### 9.2 신뢰 모델 — peer auth에 테스트가 없었다

`server.py` docstring이 선언하는 6개 경계 중 **1번 항목(SO_PEERCRED)**만 커버리지가 0이었다.
하네스가 늘 자기 uid를 넘겨서 거부 분기가 한 번도 실행되지 않았다. 나머지 경계(세션 결속,
netns 소유자, cgroup PID uid, 세션 직렬화, 오버레이 IP 봉쇄)는 전부 그 위에 서 있다.

추가: 다른 uid 거부 / **거부된 요청이 실행되지 않음** / **거부된 요청이 저널에 남지 않음** /
허용 uid 통과(대조군) / 소켓 모드 `0600`.

### 9.3 policy.py — wire 입력 검증자 9개 중 2개만 테스트되고 있었다

미테스트였던 7개를 덮었다(113 케이스). 그중 둘은 **파일시스템 경로를 구성한다** —
`session_id`는 저널 레코드 경로, `container_id`는 cgroup leaf. 정규식이 막고 있었지만
"그 정규식이 실제로 `../`를 거부하는가"는 아무도 확인하지 않았다.

**테스트가 실제 결함을 하나 잡았다**: `int(1.5)`는 예외가 아니라 `1`이다. JSON `1.5`가 VNI 1로
조용히 절삭됐고, 그건 운영자가 고르지 않은 세그먼트 ID이자 같은 노드의 다른 세션이 이미 쓰고
있을 수 있는 값이다 — 포맷 문제가 아니라 격리 문제다. `bool`도 `int` 서브클래스라 같은 경로로
0/1이 됐다. `_as_int()`로 거부하도록 고쳤다(숫자 문자열은 그대로 허용).

### 9.4 기능 — 리컨사일러에 테스트가 없었고, 약속한 재시도가 실제로 없었다

`sync_container_lifecycles`(143줄)에 직접 테스트가 없었다. 그런데 §3의 destroy 수정
(`740913436`)이 남긴 주석은 이렇게 약속한다:

> *the periodic reconciler retries from both directions: it re-issues DESTROY while the container
> lives, and CLEANs with CONTAINER_NOT_FOUND once it is gone.*

**앞 절반이 구현돼 있지 않았다.** destroy가 실패한 커널은 레지스트리에 남고(그게 그 수정의 요지)
컨테이너도 살아 있으므로, 스윕이 계산하는 두 집합 차집합(`known - alive`, `alive - known`) 중
**어느 쪽에도 들어가지 않는다.** 재발행도 보고도 없었다. 즉 그 수정은 "보이지 않는 고아"를
"보이지만 아무도 다시 손대지 않는 고아"로 바꿔 놓은 상태였다.

브랜치를 추가했다 — 레지스트리에 있고 · 살아 있고 · `TERMINATING`이고 · 진행 중인 destroy 태스크가
없으면 **destroy를 재발행**하고 원래 종료 사유를 그대로 싣는다. `TERMINATING`은 코드 전체에서
destroy 경로 한 곳에서만 설정되므로 이 조합은 정확히 "destroy가 먹히지 않았다"를 뜻한다.
진행 중인 태스크가 있으면 건드리지 않는다(한 커널에 destroy 둘이 동시에 돌면 안 된다).

### 9.5 메트릭 — 단위를 맞추고, 없던 신호를 만들었다

| 메트릭 | 변경 |
|---|---|
| `..._trigger_count` | 스윕당 +1 (변화 없음) |
| `..._success_count` | **커널 수 → 스윕당 +1.** trigger와 나란히 읽을 수 있게 됨 |
| `..._failure_count` | 예외당 +1 (변화 없음) |
| `..._synced_kernel_count` | **신규.** 커널 수는 여기로. documentation에 "enqueued, not reclaimed" 명시 |
| `..._unreclaimed_containers` | **신규 게이지.** destroy가 먹히지 않아 살아 있는 컨테이너 수. 0일 때도 발행한다 — 문제가 있을 때만 나타나는 시계열은 알람을 걸 수 없고, "시계열 없음"이 정확히 몇 주간의 상태였다 |

> **대시보드 영향**: `success_count`의 의미가 바뀐다(커널 수 → 스윕 수). 이전 데이터와 연속되지
> 않으므로, 커널 수를 보던 패널은 `synced_kernel_count`로 옮겨야 한다.

### 9.6 containerd/rootless 비대칭의 근거 고정

netns 소유자 검증을 rootless에만 걸고 containerd에는 안 거는 것은 "PID가 어디서 오느냐"에 대한
주장이다. 양쪽으로 틀리면 조용히 깨진다 — 전부에 걸면 containerd 커널(netns 소유자 uid 0)이
attach를 못 하고, 아무 데도 안 걸면 rootless 구멍이 다시 열린다. 둘 다 라이브 세션 전까지
드러나지 않으므로 `_is_rootless`의 분기를 고정했다.

### 9.7 추가한 테스트

| 파일 | |
|---|---|
| `network/privnet/test_journal.py` | 신규 — 키 at-rest 권한, 부분 쓰기, 손상 레코드, 어태치먼트 |
| `network/privnet/test_policy.py` | 신규 — wire 입력 검증자 9개 |
| `test_lifecycle_reconciler.py` | 신규 — 스윕 4분기 + destroy 재시도 + 실제 Prometheus 카운터 |
| `network/test_privnet.py` | `TestPeerAuthentication` 추가 |
| `network/test_privnet_runtime.py` | netns 소유자 비대칭 고정 |

### 9.8 여전히 유닛 테스트로는 못 하는 것

- **GPU 격리** — 2장 노드에서 1장 할당, 또는 0장 할당 대조군이 필요하다
- **단일노드 클러스터 세션 통신** — `create_local_network`가 no-op이라 세션 네트워크만으로 서야 한다
- **NCCL all-reduce**
- **도달성 프로브의 실제 차단 동작** — udp/4789 방화벽 조작 필요
- **`--contain`이 IPC를 안 덮는다는 전제** — apptainer 쪽은 argv 검사까지만

---

## 10. 노드 단위 자원과 복구 경로 (8/29–8/30)

§9가 "무엇이 테스트되지 않았나"였다면, 이번은 **라이브에서만 드러나는 결함** 셋이다. 세 개가 사슬로
이어져 있다 — 앞의 것을 고쳐야 뒤의 것이 보인다.

### 10.1 LOCAL 블록 충돌 — `cacf4053b`의 진단이 반대였다

**증상**: containerd 단일노드 클러스터 세션이 0% 손실로 돌던 중, singularity 세션이 같은 노드에
뜨자 **100% 손실**로 죽었다. host측 veth가 사라졌다.

```
/var/lib/bai-containerd/net-local-subnet/0   -> <cd 세션>
/var/lib/bai-singularity/net-local-subnet/0  -> <sg 세션>
```

세 에이전트가 **각자의 저장소에서 전부 index 0을 점유**했다. 그런데 index가 만드는 이름 —
브리지 `bailo<idx>`, 서브넷 `172.30.0.<idx*64>/26` — 은 **노드 전역**이다. 두 번째 에이전트의
셋업이 첫 번째의 `bailo0`을 이름으로 덮어썼다.

**원인**: `cacf4053b`가 저장소를 `var-base-path`로 앵커링하면서 노드 전역 조율이 사라졌다.
`vxlan.py:400`의 주석이 스스로 말한다 — *"one owner keeps their indices from colliding on a
subnet"* — 그 owner가 노드당 하나가 아니라 에이전트당 하나가 됐다.

그리고 `non-cni-features.md` §5의 원래 진단이 **반대였다.** 당시 본
`NetworkStateStoreConflict (index 0 exists)`는 가드가 옳게 동작한 것이고, 진짜 버그는
`local_subnet.py`가 그 정상적 경쟁을 **저장소 손상으로 보고**한 것이었다. 앵커링은 시끄러운
올바른 거부를 **조용한 네트워크 탈취**로 바꿨다.

설정 스키마가 이미 답을 갖고 있었다 — `local_network_pool`은 **override 불가** 클래스에 있다.
즉 LOCAL 풀은 설계상 노드 단위 자원이고, 그 위 할당자도 노드 단위여야 한다.

**수정 — 세 겹**

| | |
|---|---|
| 노드 전역 저장소 복원 | 소유자 태그(`<session>\n<owner>`)로 이웃의 블록을 회수 대상에서 제외. 디렉터리는 `/tmp`처럼 `1777`(스티키) — uid가 다른 에이전트도 클레임 생성 가능, 남의 것 삭제는 불가 |
| 경쟁을 정상 결과로 | `_write_claim`이 `FileExistsError`에서 **다음 인덱스로 진행**. 예전엔 예외 |
| 레거시 입양 | 노드는 한 번에 업그레이드되지 않는다. 에이전트 자기 옛 저장소의 클레임을 **인덱스 보존**한 채 가져온다 — 그 인덱스는 이미 떠 있는 브리지의 이름이다 |
| **호스트가 최종 권위** | 입양만으로는 부족했다. **구코드로 도는 이웃의 클레임은 어느 저장소로도 볼 수 없다.** 할당 직전 노드의 실제 IPv4 주소를 읽어(psutil, `vtep.py`와 동일) 이미 주소가 올라온 블록은 건너뛴다. 누출된 브리지에도 동일 |

호스트 읽기는 **프로덕션 팩토리에서만** 주입한다 — 클래스 기본값은 순수라 테스트가 머신 상태에
의존하지 않는다.

**라이브 검증**: `bind-en`(구코드 enroot)이 블록 1을 쥔 상태에서
```
WARNING local-subnet index 1 (172.30.0.64/26) is already carried by a device on this host
        that no journal here names; skipping it
```
→ sg가 블록 2를 잡고 RUNNING. 세 브리지가 전부 다른 서브넷.
그리고 enroot privnet 재시작 시 `adopted local-subnet index 1 (92b2544a…) from the legacy store`.

### 10.2 rootless 커널이 에이전트와 함께 죽는다

**증상**: enroot 에이전트를 재시작했더니 3일 돌던 세션의 커널이 함께 죽었다. 매니저는
RUNNING을 들고 있는데 뒤에 아무것도 없었다.

**원인**: `create_task`의 spawn에 `start_new_session`이 없어 커널이 에이전트의 세션·프로세스
그룹을 물려받는다. 그 그룹으로 가는 시그널이 커널까지 간다 — Ctrl+C, 터미널 종료,
`tmux kill-session`, systemd 기본 `KillMode=control-group`.

**이건 설계 전제가 깨진 것이다.** rootless 복구 기계 전체 — 저널, `_recover_containers`,
`container_pid`의 저널 폴백 — 가 커널이 에이전트보다 오래 산다는 전제 위에 서 있다.
데몬이 있는 containerd에는 없는 문제다.

**수정**: `start_new_session=True` (자식에서 `setsid`). 회수는 그대로 — `_reap`도 `_signal`도
pid를 쏘지 pgid를 쏘지 않는다.

**라이브 검증**: 세션을 죽인 그 동작을 재현 — `tmux kill-session` 후 커널 2개 **생존**,
에이전트 재시작 시 `recovered 2 running container(s) from the journal`, 세션 RUNNING 유지.

> **운영 메모**: enroot 커널은 데몬이 없어 에이전트의 자식으로 뜬다. 이 수정 이전 버전을
> 재시작할 때는 프로세스 그룹이 아니라 **에이전트 프로세스에만** 시그널을 보내야 한다.

### 10.3 재시작 후 클러스터 이름이 사라진다

10.2를 고치자 비로소 보였다 — 이전엔 커널이 함께 죽어 관측될 수 없었다.

**증상**: 에이전트 재시작 후 피어끼리 ping·TCP는 되는데 `getent hosts sub1`이 무응답.
`getent hosts cr.backend.ai`는 정상(리졸버는 살아 있고 포워딩도 된다). 세션 표만 비었다.

**원인**: 리졸버의 이름표가 둘인데 내구성이 다르다.

| 표 | 출처 | 재시작 후 |
|---|---|---|
| `_names` | etcd `endpoints/` watch | 복구됨 |
| `_static_names` | 에이전트가 `cluster_host_ips`로 계산 | **사라짐** (in-memory) |

단일노드 클러스터는 `endpoints/` 테이블이 없어 `_static_names`가 유일한 출처인데, 그걸 채우는
호출이 `create_kernel` 안에만 있다. 복구된 커널은 그 경로를 타지 않는다.

**수정**: `cluster_host_ips`가 순수 함수이고 입력(서브넷·피어 목록)이 둘 다 내구적이라
**저장이 아니라 재계산**으로 풀었다. `restore_cluster_names()`가 복구 시 다시 계산해 등록하고,
`meta.backend`로 단일노드만 고른다 — 멀티노드에 같은 짓을 하면 아무 데도 없는 주소를 답한다.

**라이브 검증**: 재시작 전후로 `getent main1/sub1` 모두 정상 응답.

### 10.4 이번에 배운 것

**같은 형태의 결함이 이 브랜치에서 네 번 나왔다** — *정상 경로에만 있고 복구 경로에는 없는 로직*:
destroy의 CLEAN, 리컨사일러의 재발행, 커널의 프로세스 분리, 클러스터 이름 등록.
복구 경로를 별도 축으로 두고 매 기능마다 물어야 한다.

**그리고 측정 방법에서 또 네 번 틀렸다** (§6의 목록에 이어서):

| 잘못 본 것 | 왜 틀렸나 |
|---|---|
| "privnet에 요청이 0건" | HEAD에서도 0건 — privnet은 성공 요청을 로깅하지 않는다 |
| "클러스터 DNS 리졸버가 2개" | 코드가 명시적으로 처리하는 정상 경쟁(진 쪽을 `stop()`) |
| "Group A(리컨사일러)가 범인" | flaky를 한 표본으로 확정할 뻔했다. 실제 변수는 다른 에이전트의 블록 점유였다 |
| "HEAD도 블록 1에서 실패" | 무효한 실험 — HEAD는 블록 1에 가지도 못하고 conflict로 죽었다 |

**교훈**: 다중 백엔드 노드는 **발견**에는 유리하지만(충돌 계열 결함이 거기서만 드러난다)
**검증**에는 치명적이다. 두 환경을 분리하고, 결론은 단독 구성에서 낸다.

### 10.5 단독 검증 결과 (3 백엔드)

| | containerd | singularity | enroot |
|---|---|---|---|
| 단일노드 클러스터 세션 | ✅ | ✅ | ✅ |
| ping 양방향 / DNS 양방향 / TCP | ✅ | ✅ | ✅ |
| IPC 격리 | — | ✅ | ✅ |
| cgroup 한도 | — | — | ✅ 2 GiB |
| 재시작 생존 + 이름 복구 | — | — | ✅ |

### 10.6 멀티노드 containerd — 깨진 게 아니라 회전 속도에 걸린다 (8/30)

작업 도중 "멀티노드 containerd 세션이 뜨지 않는다"고 적었는데 **틀렸다.** 다시 돌려 양쪽 노드
로그까지 확인한 결과, 정상 동작하고 8/28 수치와 정확히 일치한다.

| 축 | 측정값 |
|---|---|
| 크로스노드 200패킷 | **0% 손실** |
| DF 경계 | **1422 통과 / 1423 드롭** (= 1450 − 28) |
| DNS 양방향 | `sub1→10.128.5.1`, `main1→10.128.5.2` |
| 피어 TCP `:2200` | `SSH-2.0-dropbear_2024.85` |
| meta ↔ 엔드포인트 ↔ 디바이스 | 전부 일치 (vni 4101, `baivx4101`/`bailo4101`) |

**실패는 간헐적이고, 변수는 세션 회전 속도다.**

| 세션 간격 | 결과 |
|---|---|
| ~12초 (연속) | 6회 중 **4회 실패** |
| 75초 | 3회 중 **0회 실패** |

**실패 서명**: 양쪽 커널의 컨테이너가 뜨고 sshd·ttyd까지 기동한 뒤, 에이전트의
`get_service_apps`가 약 53초 동안 실패를 반복하다 포기한다. **두 노드가 함께** 실패한다.
실패 창에서 재본 크로스노드 L3와 클러스터 DNS는 정상이었다 — 네트워크가 원인이 아니다.

**그리고 실패한 세션은 재시도로 살아나지 못한다.** 매니저가 같은 커널 id로 재시도하면 `.104`가
이렇게 죽는다:

```
ALREADY_EXISTS: snapshot "650e8b49-fab4-4f85-b3cd-7fc455d9f6d0": already exists
```

**첫 시도가 만든 containerd 스냅샷이 정리 경로에서 지워지지 않는다.** 컨테이너는 지워지는데
스냅샷은 남아, 같은 커널 id의 재시도가 영구히 실패한다. 일시적 실패를 세션 전체의 확정 실패로
바꾸는 것이 이것이다 — 실제로 이 때문에 "상시 실패"로 오인했다.

**남은 미해결**: `get_service_apps` 실패의 근인. 컨테이너와 서비스는 뜨고, L3·DNS는 정상이며,
빠른 회전에서만 나타난다. 다음 단계는 실패 창에서 커널 러너의 RPC를 직접 두드려 보는 것.

> **측정 교훈 (§6·§10.4에 이어)**: "안 뜬다"를 한두 번의 실행으로 단정했다. 간헐적 실패는
> **반복 횟수와 조건을 바꿔가며** 재야 하고, 그 전에는 "상시"라고 쓰면 안 된다.

---

## 11. 멀티노드 containerd 실패의 근인 (8/30)

§10.6이 남긴 미해결 — `get_service_apps`가 실패하는 이유 — 를 로그로 끝까지 따라갔다.
결론은 **두 개의 별개 문제**였고, 하나는 환경, 하나는 코드다.

### 11.1 타임라인 (세션 `0c3edb50`, 17:08)

| 시각 | 노드 | 사건 |
|---|---|---|
| 17:08:14 | 104 · 156 | 두 노드가 동시에 `create_kernel` 수신 |
| 17:08:17 | **104** | `service apps initialized` → `done`. **1.1초 만에 정상 완료** |
| 17:08:15~ | **156** | `waiting for kernel service initialization` 이후 **정지** |
| 17:09:14 | 104 · 156 | 매니저가 **같은 커널 id로 create_kernel 재전송** (약 57초 뒤) |
| 17:09:14 | 104 | 스냅샷·컨테이너 레코드 회수 → `ALREADY_EXISTS: task ... already exists` → **커널 파괴** |
| 17:09:19 | 156 | `RetryError` → `Container startup failed` |

**104는 처음부터 멀쩡했다.** 세션을 죽인 것은 156의 정지와, 그 재시도를 104가 처리하지 못한 것이다.

### 11.2 근인 1 — 노드 156이 79커밋 낡은 코드로 돌고 있었다 (환경)

```
156 cd 에이전트 기동: 8월 28일 16:25,  HEAD = 7a9b0bc4a  (이 브랜치보다 79커밋 뒤)
```

이 브랜치의 수정이 하나도 반영돼 있지 않았다. 게다가 156에는 cd·en·sg 세 백엔드가 동시에
떠 있었다 — §10.5에서 정한 "한 번에 한 백엔드" 규칙이 **원격 노드에는 적용되지 않고 있었다.**

**조치**: 156을 현재 브랜치로 올리고(기존 워킹트리는 `git stash`로 보존) containerd 단독으로 재기동.

### 11.3 근인 2 — 살아있는 커널에 대한 재시도가 그 커널을 죽인다 (코드)

매니저가 재전송한 `create_kernel`을 104가 처리하는 방식이 문제였다.

1. `_prepare_rootfs`/`_create_container_record`의 회수 로직은 `ALREADY_EXISTS`를
   "이전 시도의 잔해"로만 해석했다. 실제로는 **"지금 사용 중"** 이라는 뜻이기도 하다.
   → **정상 서비스 중인 컨테이너의 스냅샷과 레코드를 지웠다.**
2. task는 회수 대상이 아니었다 → `ALREADY_EXISTS: task` 에서 막힘.
3. `create_kernel`의 실패 경로가 그 커널에 `DESTROY`를 던졌다 → **1분간 정상 응답하던 커널이 파괴.**

**수정** (`1a1519148`):

| 층 | 내용 |
|---|---|
| `create_kernel` | 이 에이전트에 이미 `RUNNING`인 커널이면 **그때 준 결과를 그대로 다시 답한다** (RPC 멱등성). `track_create`는 진행 중인 생성만 막았다 |
| 회수 로직 | task가 살아있으면 **아무것도 지우지 않고 거절**한다. task가 두 경우를 구분하는 유일한 근거 |
| `create_task` | 죽은 task의 잔여 레코드를 스냅샷·컨테이너 레코드와 같은 방식으로 회수 |

### 11.4 부수 발견 — 러너 누수 (`b2bed4c07`)

`AbstractKernel.init()`이 `self.runner`를 **닫지 않고 덮어썼다**. 재시도마다 REPL 소켓 2개가
버려지고, ZMQ가 그 주소로 영원히 재접속한다. 그 주소는 컨테이너의 LOCAL IP이고 다음 세션이
같은 IP를 받으므로, 버려진 소켓이 **새 커널**에 붙는다. 커널의 PUSH 소켓은 붙은 피어에
**라운드로빈**으로 응답하므로 살아있는 러너가 답을 못 받는다.

관측: 세션이 하나도 없는데 잔여 repl 소켓 **14개**, 단일 주소에 5~6개(ESTAB은 1개).

### 11.5 검증

**단위**: 뮤테이션 5종 전부 검출(가드 3종 + 회수 거절 + `create_task` 경로).
`test_duplicate_create.py` 신규, `test_grpc_runtime.py` 확장.

> 함정: `KernelLifecycleStatus`는 `ai.backend.agent.types`와 `ai.backend.common.types`에
> **중복 정의**돼 있다. `is` 비교는 같은 쪽을 import해야 한다.

**라이브** (양 노드 containerd 단독 + 현재 코드, 12초 간격 연속):

> **먼저 측정 방법의 함정 하나.** 처음 낸 "6/6·12/12·10/10 성공"은 **진짜 멀티노드가 아니었다.**
> `.104`는 31 CPU, `.156`은 15 CPU라 8 CPU 커널 2개가 `.104` 한 노드에 다 들어간다.
> `agent_list` 핀은 무시된다 — 배치를 정하는 것은 **가용 자원뿐**이다. 실패했던 0/4 실행은
> filler 세션이 `.104`를 점유하고 있어서 강제로 갈렸던 것이고, 그 filler를 뺀 채 비교하면
> 조건이 다르다. 그래서 **매 회차 커널이 실제로 어느 에이전트에 갔는지 확인**하도록 바꿨다.

| | 수정 전 | 수정 후 |
|---|---|---|
| 멀티노드 세션 (filler로 분산 강제) | **0 / 4 RUNNING** | **10 / 10 RUNNING** |
| 그 중 실제로 두 노드에 갈린 것 | 4 / 4 | **10 / 10** (`main1@i-cd-104, sub1@i-cd-156`) |
| 실행당 잔여 소켓 증가 | +2 (2→4→6→8) | **0** (4/2에서 고정) |
| 무세션 상태 잔여 소켓 | 14 | **0 / 0** |
| 에이전트 ERROR | 매 실행 | **0 / 0** |
| `.156` 커널 | 60초 정지 후 실패 | 생성 12건 · 완료 12건 |

> **측정 교훈**: "멀티노드 세션"을 요청했다고 멀티노드로 뜨는 게 아니다. 스케줄러가 한 노드에
> 담을 수 있으면 담는다. **결과가 아니라 배치를 검증**해야 한다 — 이 확인을 넣기 전까지
> 28회의 "성공"은 단일 노드 성공이었다.

> **측정 교훈**: "104가 안 뜬다"로 시작했지만 104는 처음부터 정상이었다. 멀티노드 실패는
> **양쪽 로그를 같은 시각축에 놓고** 봐야 어느 쪽이 원인인지 보인다. 그리고 원격 노드의
> **코드 버전과 백엔드 개수**는 로컬만큼 확인해야 할 변수다.

---

## 12. 백엔드별 전수 재검증 (8/31)

**한 번에 한 백엔드만** 양 노드에서 띄우고, 같은 배터리를 세 번 돌렸다.

### 12.1 배터리 구성

| # | 항목 | 통과 기준 |
|---|---|---|
| 1 | 단일노드 세션 | RUNNING |
| 2 | filler(20 CPU)로 분산 강제 | RUNNING |
| 3 | 멀티노드 세션 | RUNNING **+ 커널이 실제로 두 노드에 갈렸는지 확인** |
| 4 | 컨테이너 내부 네트워크 | 클러스터 DNS 양방향 + 노드 간 L3 양방향 0% 손실 |
| 5 | 연속 5회 (분산 강제 유지) | 전부 RUNNING + 전부 분산 |
| — | 정리 후 | 잔여 repl 소켓 0/0, 에이전트 생존, 에이전트 ERROR 0/0 |

### 12.2 결과 — 세 백엔드 전부 실패 0

| 축 | containerd | enroot | apptainer |
|---|---|---|---|
| 단일노드 | ✅ | ✅ | ✅ |
| 멀티노드(실제 분산) | ✅ | ✅ | ✅ |
| 클러스터 DNS 양방향 | ✅ | ✅ | ✅ |
| 노드 간 L3 양방향 | 0% 손실 | 0% 손실 | 0% 손실 |
| 연속 5회 분산 | 5/5 | 5/5 | 5/5 |
| 정리 후 잔여 소켓 | 0/0 | 0/0 | 0/0 |
| 에이전트 ERROR | 0/0 | 0/0 | 0/0 |
| **배터리 실패** | **0** | **0** | **0** |

안전성(유닛): lint·mypy 406파일 클린, `tests/unit/agent::` 99개 타깃 전부 통과.

### 12.3 이번에 드러난 측정·환경 함정

| 함정 | 증상 | 대응 |
|---|---|---|
| `agent_list`가 요청 템플릿에 **containerd 에이전트 id로 고정** | enroot/apptainer에서 멀티노드가 영원히 PENDING | 검사 대상 백엔드의 id로 다시 씀 |
| 자원이 한 노드에 다 들어가면 스케줄러가 **패킹** | "멀티노드 성공"이 실은 단일노드 | filler로 분산 강제 + **매 회차 배치 확인** |
| `156`의 `agent-{en,sg}-156.toml`에 **privnet 소켓 설정이 없었음** | privnet이 기본 경로로 떨어져 에이전트가 `ConnectionRefused` | 104와 동일하게 추가 (`.bak-20260830` 보존) |
| 고아 에이전트 워커가 RPC 포트를 계속 점유 | 재기동이 `Address already in use`로 실패 | 포트 보유 pid로 식별해 정리 |
| `pkill -f <패턴>`이 **자기 셸까지** 매칭 | 정리 명령이 스스로를 죽임 (exit 144) | 패턴을 쪼개거나 스크립트 파일로 분리 |
| 실행 중인 스크립트를 편집 | bash가 파일을 증분 파싱해 **문법 오류로 중단** | 실행 전 `run-frozen.sh`로 복사해 고정 |
| rootless 컨테이너의 PID를 `enroot list`로 탐색 | 이름이 `<unknown>`이라 매칭 실패 | cgroup 경로 `/backend-ai/<kernel-id>`로 찾되, **호스트 netns가 아닌** 프로세스를 고름 (런처가 같은 cgroup을 공유) |
| LOCAL 주소로 노드 간 ping | 두 커널이 같은 `172.30.0.66`이라 **자기 자신에게** ping | 클러스터 DNS가 주는 오버레이 주소(`10.128.26.x`)로 ping |

---

## 13. 로그 로테이션·수명주기 위생 실측 (8/31)

계약: `container_logs.max_length` 기본 **10 MiB**, 파일 5개(`k.log`, `.1`~`.4`), 개당 `max_length/5` = **2 MiB**.
containerd는 `binary://` 라이터가 쓰기 끝을 소유하므로 **하드캡**, rootless 두 백엔드는 에이전트 안의
5초 주기 루프가 밖에서 자르므로 **소프트캡**.

### 13.1 정상 동작 — 세 백엔드 모두 정상

| 항목 | containerd | enroot | apptainer |
|---|---|---|---|
| 48 MiB 버스트 후 잔량 | 8.0 MiB (한 번도 초과 없음) | 2 MiB | 2 MiB |
| 파일 수 / 개당 최대 | 5 / 2 MiB | 5 / 2 MiB | 5 / 2 MiB |
| `bai session logs` (로테이션 가로질러 읽기) | 8.4 MB | 2.1 MB | 2.1 MB |
| 컨테이너 PID 1의 좀비 수거 | 0 | 0 | 0 |
| 종료 시 로그 세트 삭제 | ✅ | ✅ | ✅ |
| 종료 시 스크래치 삭제 | ✅ | ✅ | ✅ |

### 13.2 지속 부하(5 MiB/s, 40초) — 소프트캡의 실제 크기

| | 디스크 피크 | 예산 대비 | 안정 후 |
|---|---|---|---|
| containerd | **9 MiB** | 예산 이내 | 8 MiB / 5파일 |
| enroot | **33 MiB** | **3.3배** | 8 MiB / 5파일 |
| apptainer | **33 MiB** | **3.3배** | 8 MiB / 5파일 |

오버슈트는 `4 × 2 MiB(로테이트분) + rate × 5초(활성 파일)`와 **정확히** 일치한다. 즉 rootless의
피크는 쓰기 속도에 **선형 비례**한다 — 50 MiB/s면 258 MiB.

### 13.3 에이전트가 죽어 있는 동안 — 여기가 실제 위험

커널을 5 MiB/s로 쓰게 두고 에이전트를 `SIGKILL` 한 뒤 32초 관측.

| | 커널 생존 | 에이전트 없는 동안 로그 | 재기동 후 |
|---|---|---|---|
| containerd | ✅ | **9.4 MiB에서 정지** (라이터가 별도 프로세스) | 세션 RUNNING, 8.4 MiB |
| enroot | ✅ | **75 → 117 → 159 → 201 MiB** (상한 없음) | 세션 RUNNING, 4 MiB로 회수 |

**rootless 백엔드는 에이전트가 떠 있지 않으면 로그 상한이 아예 없다.** 증가량 = 쓰기 속도 × 다운타임.
5 MiB/s로 1시간이면 18 GB다. 재기동하면 로테이터가 즉시 회수하고(4 MiB), 종료 시 정리도 정상이다 —
즉 **복구는 되지만 그 사이 디스크는 무방비**다.

> 왜 지금 구조인가: 컨테이너에 파이프를 쥐여 주면 하드캡을 얻지만, 읽는 쪽이 사라졌을 때
> 컨테이너의 stdout이 막혀 커널이 멈춘다. 코드 주석이 그 트레이드오프를 명시하고 있고, 커널이
> 에이전트보다 오래 사는 것이 전제이므로 그 선택 자체는 맞다. 문제는 **캡을 쥔 주체가 에이전트라는 점**이다.

**제안**: rootless의 로테이션을 **privnet으로 옮긴다.** privnet은 이미 이 두 백엔드 전용으로
별도 프로세스로 돌고, 필요한 권한을 갖고 있으며, 에이전트와 독립적으로 산다. 커널의 stdout 경로를
건드리지 않으므로 "읽는 쪽이 막히면 커널이 멈춘다"는 문제도 생기지 않는다.
(차선: 활성 파일이 한 주기에 `max_size`를 넘겨 자랐으면 다음 검사를 기다리지 않고 즉시 다시 자른다 —
정상 상태의 오버슈트는 줄지만 에이전트 부재 구간은 여전히 무방비다.)

### 13.4 정리되지 않는 잔여물

세션이 하나도 없는 상태에서:

| 경로 | 남은 것 |
|---|---|
| `bai-{enroot,singularity}/containerd-logs` | 8/28~29 커널의 로그 4~5개 |
| `bai-*/scratches` | 12 / 10 / 19개 (0.8~2.4 MB) |

정상 종료 경로는 로그·스크래치를 **모두 지운다**(오늘 종료된 커널은 하나도 안 남았고, 크래시 후
재기동→종료 경로도 깨끗했다). 남은 것들은 **에이전트가 강제 종료되고 그 커널 기록도 함께 사라진**
경우다. `unlink_log_files`는 컨테이너 제거 경로에서만 불리고, 로테이션 루프는 `*.log`를 훑되
**자르기만 하고 지우지 않는다** — 즉 주인 없는 로그/스크래치를 청소하는 주체가 없다.

**제안**: 에이전트 기동 시(이미 orphan cgroup은 회수하고 있다) 로그 루트와 스크래치 루트를 훑어
커널 레지스트리에도 런타임에도 없는 id의 디렉터리·로그 세트를 함께 회수한다.

---

## 14. "privnet도 죽는다" / "setsid면 충분한가" — 실측 답 (8/31)

### 14.1 setsid가 막는 것과 막지 못하는 것

`start_new_session=True`는 **세션과 프로세스 그룹**을 바꾼다. 즉 프로세스 그룹으로 가는 신호
(Ctrl+C, 터미널 HUP, `tmux kill-session`)만 막는다.

systemd의 기본 `KillMode=control-group`은 **cgroup**으로 죽인다 — 새 세션은 cgroup을 벗어나지
않으므로 setsid로는 안 막힌다. 실제로 커널이 살아남는 이유는 따로 있다:

```
agent  cgroup: /user.slice/.../tmux-spawn-....scope     (14 pids)
kernel cgroup: /backend-ai/4cc5a3e7-...                  ← 최상위, 에이전트 밖
=> 에이전트 cgroup의 pid 목록에 커널 없음
```

이 최상위 cgroup은 **privnet이 만들어 트리를 옮긴 것**이다(`_confine_via_privnet`).
그리고 그 위임은 **best-effort**다 — 실패하면 커널은 에이전트 cgroup에 그대로 남고,
그 노드에서는 `systemctl stop` 한 번에 커널이 함께 죽는다.

| 죽이는 방식 | setsid | cgroup 위임 | 결과 |
|---|---|---|---|
| Ctrl+C / 터미널 종료 / tmux kill | ✅ | — | 생존 |
| `systemctl stop` (KillMode=control-group) | ❌ | ✅ (성공했을 때만) | 위임 실패 노드에서는 사망 |
| `pkill -f <패턴>` | ❌ | ❌ | 사망 (오늘 이 세션에서 여러 번 자초함) |
| 에이전트가 든 컨테이너/파드 삭제 | ❌ | ❌ | 사망 (경계가 파드다) |

즉 **setsid만으로는 충분하지 않다.** 지금 안전한 이유는 setsid + privnet의 cgroup 위임 **둘 다**이고,
후자는 실패할 수 있는 경로다.

### 14.2 privnet도 죽는다 — 그래서 프로세스에 기대는 상한은 전부 조건부다

| 캡을 쥔 주체 | 에이전트 재시작 | privnet 사망 | 둘 다 사망 | 비용 |
|---|---|---|---|---|
| 에이전트 (현재 rootless) | ❌ | ✅ | ❌ | — |
| privnet (제안) | ✅ | ❌ | ❌ | 이동만 |
| 컨테이너별 라이터 (containerd 방식) | ✅ | ✅ | ✅ | 읽는 쪽이 막히면 커널이 멈춤 |
| **파일시스템 상한** | ✅ | ✅ | ✅ | 로그 라인 유실 |

privnet으로 옮기는 것은 **보장이 아니라 적용 범위 확대**다(에이전트 재시작은 흔하고 privnet 재시작은
드물다). 무조건적인 보장은 프로세스가 아닌 것만 줄 수 있다.

### 14.3 파일시스템 상한을 실제로 재봤다

로그 루트를 16 MiB tmpfs에 올리고, **에이전트를 죽여 로테이터를 없앤 뒤** 40 MiB를 썼다.

```
round 1: used=5.1M/16M   kernel alive=yes
round 3: used=16M/16M    kernel alive=yes     ← ENOSPC
...
round 8: used=16M/16M    kernel alive=yes
재기동 후: session RUNNING, kernel alive, bai session logs = 10 MiB
종료 후: tmpfs에 파일 0개
```

**핵심: stdout 쓰기가 ENOSPC로 실패해도 커널은 죽지 않는다.** 로그 라인은 유실되지만 세션은 멀쩡하고,
에이전트가 돌아오면 로테이터가 정상 동작하며 정리도 깨끗하다.

### 14.4 결론

- **로그**: 로테이션을 privnet으로 옮기고(적용 범위), 로그 루트에 파일시스템 상한을 두는 것(보장)을
  **함께** 한다. 어느 하나로는 부족하다.
- **커널 생존**: setsid는 유지하되, 안전을 실제로 담보하는 것은 cgroup 위임이므로
  **위임 실패를 조용히 넘기지 말아야 한다** — 실패한 노드는 `systemctl stop`에 커널을 잃는다.
  (현재는 경고만 남기고 커널을 띄운다.)

---

## 15. 백엔드 비교 — docker 대비 containerd / enroot / apptainer (8/31)

### 15.1 먼저 구조 — 넷이 아니라 둘이다

| | 에이전트 클래스 | 커널 클래스 | 코드량 |
|---|---|---|---|
| docker | `DockerAgent(AbstractAgent)` | `DockerKernel` | 3,575줄 |
| containerd | `ContainerdAgent(AbstractAgent)` | `ContainerdKernel` | 5,170줄 |
| enroot | **`EnrootAgent(ContainerdAgent)`** | `ContainerdKernel` | 611줄 |
| apptainer | **`SingularityAgent(ContainerdAgent)`** | `ContainerdKernel` | 727줄 |

> **privnet은 백엔드 속성이 아니라 권한 분리 스위치다.** `network-privnet-socket`이 설정되면
> netns 진입·iptables 인그레스·cgroup 위임을 privnet이 맡고, 없으면 에이전트가 직접 한다(그러려면
> 특권이어야 한다). 그 분기는 **`ContainerdAgent`의 코드**이므로 세 백엔드에 다 적용되고, privnet도
> containerd를 명시적으로 지원한다(`BACKENDAI_PRIVNET_CTRD_NS`, `_is_rootless()`는 containerd에서
> False를 돌려 netns owner uid 검사만 끈다 — containerd의 PID는 root 데몬이 주므로 위조가 불가능해서).
> containerd에서는 **선택**이고(이 테스트베드의 `agent-cd-104.toml`에는 설정이 없다), rootless 두
> 백엔드에서는 에이전트가 비특권이라 in-process 대안이 없어 사실상 필수다.
>
> 따라서 rootless의 권한 이점은 privnet이 아니라 **데몬 소켓이 없다는 것**이다. containerd는 privnet을
> 쓰더라도 컨테이너 생성을 위해 containerd 소켓(root 상당)이 여전히 필요하다.

`EnrootAgent`와 `SingularityAgent`가 오버라이드하는 메서드는 **`_create_runtime` 단 하나**다.
네트워킹·수명주기·스탯·서비스 포트·커밋·복구가 전부 `ContainerdAgent`의 것이고, 세 백엔드의 차이는
`OciRuntime` 심(seam) 뒤의 런타임 구현(+공용 `RootlessOciRuntime` 2,808줄)뿐이다.

**따라서 "containerd 대 enroot 대 apptainer"는 대부분의 축에서 같은 답이 나온다** — §12에서 세 배터리
결과가 동일했던 것이 우연이 아니다. 진짜 경계는 **docker ↔ containerd 계열**이다.

### 15.2 기능별

| 축 | docker | containerd | enroot | apptainer |
|---|---|---|---|---|
| 데몬 | dockerd (root 소켓) | containerd (root 소켓) | **없음** | **없음** |
| 에이전트 권한 | root 상당(소켓) | root 상당(소켓) | **비특권** | **비특권** |
| privnet(권한 분리) | 해당 없음 | **선택** | 사실상 필수 | 사실상 필수 |
| 커널 소유자 | dockerd | containerd-shim | 에이전트의 자식 | 에이전트의 자식 |
| 네트워크 심 | 레거시 `plugin/network.py` | **BEP-1062 `network_v2`** | **BEP-1062 `network_v2`** | **BEP-1062 `network_v2`** |
| 단일노드 클러스터 | docker 브리지 + 내장 DNS 별칭 | LOCAL 브리지 + 자체 리졸버 | LOCAL 브리지 + 자체 리졸버 | LOCAL 브리지 + 자체 리졸버 |
| 멀티노드 | 네트워크 플러그인(overlay/swarm) | **VXLAN 자체 구현** | **VXLAN 자체 구현** | **VXLAN 자체 구현** |
| cgroup 적용 | dockerd | runc (OCI spec) | **에이전트/privnet이 직접** | **에이전트/privnet이 직접** |
| 스탯 출처 | docker API | **cgroup fs** (강제) | **cgroup fs** (강제) | **cgroup fs** (강제) |
| 스탯 항목 | mem·io_read·io_write (docker API) | mem·io_read·io_write·net_rx·net_tx | mem·io_read·io_write·net_rx·net_tx | mem·io_read·io_write·net_rx·net_tx |
| 로그 캡 | dockerd `local` 드라이버 (**하드**) | `binary://` 라이터 (**하드**) | 에이전트 5초 루프 (**소프트**) | 에이전트 5초 루프 (**소프트**) |
| GPU 주입 | device requests | **CDI** | `NVIDIA_VISIBLE_DEVICES` → 98-nvidia 훅 | `--nvccli` |
| seccomp | dockerd에 프로필 전달(코드만 확인) | **Seccomp: 2** (filter) | **Seccomp: 2** | **Seccomp: 2** |
| AppArmor | **안 씀** (JAIL에서 `apparmor=unconfined`) | 안 씀(`02dbfd29e`에서 제거) | 안 씀 | 안 씀 |
| 커밋 산출물 | docker 이미지 | **OCI 레이어**(base와 diff, 레이어 공유) | `.sqsh` | 샌드박스 평탄화 |
| export | docker save | OCI tar | `.sqsh` 복사 | SIF/샌드박스 |
| 레지스트리 인증(pull) | dockerd가 전담 | **auth 전달됨** | ❌ 전달 안 됨 | ❌ 메타데이터 조회만 |

### 15.3 containerd 계열이 docker보다 나은 점

- **멀티노드가 자기 것이다.** docker는 overlay/swarm이나 외부 플러그인에 의존한다. containerd 계열은
  VXLAN·LOCAL 브리지·클러스터 DNS를 직접 갖는다 — §12에서 세 백엔드 모두 노드 간 L3 양방향 0% 손실,
  DNS 양방향 확인.
- **enroot/apptainer는 데몬 소켓이 아예 없다.** docker는 docker 소켓, containerd는 containerd 소켓이
  필요하고 둘 다 사실상 root다. privnet으로 네트워크 권한을 떼어내도 그 소켓은 남는다 — 소켓 자체가
  없는 것은 rootless 두 백엔드뿐이다.
- **커밋이 레이어를 공유한다**(containerd). base와 diff해 올리므로 전체 rootfs를 한 레이어로
  평탄화하지 않는다.

### 15.4 rootless 두 백엔드가 실제로 뒤지는 점

| 격차 | 실측/근거 | 영향 |
|---|---|---|
| **레지스트리 인증이 pull에 안 실림** | enroot는 코드에 TODO 주석, apptainer는 메타데이터 조회에만 사용 | 프라이빗 레지스트리는 `~/.docker/config.json` 같은 **주변 자격증명**에 의존 |
| **로그 캡이 소프트** | 5 MiB/s에서 피크 33 MiB (예산 10 MiB) | 정상 운영 중에도 3배 초과 |
| **에이전트가 죽으면 로그 상한 없음** | 32초에 201 MiB (containerd는 9.4 MiB 고정) | 다운타임 × 쓰기속도만큼 무제한 |
| **커밋 산출물이 백엔드 전용 포맷** | `.sqsh` / 샌드박스 | 다른 백엔드로 옮겨 실행 불가 |
| **cgroup을 스스로 만들어야 함** | 런타임에 cgroup 통합이 아예 없음 | 위임 실패 = 커널 거부 (`ea60bf73d`) |

앞의 셋은 `OciRuntime` 심 뒤의 런타임 특성이라 백엔드별로 고쳐야 하고, 마지막 둘은 공용
`RootlessOciRuntime`에서 한 번에 다뤄진다.

> 참고: 이 저장소의 GPU 플러그인은 `cuda_open`(전체 장치)뿐이다. fractional GPU 플러그인은 여기 없어
> 어느 백엔드에서도 시험 대상이 아니다 — 백엔드 간 차이가 아니라 저장소 범위의 문제다.

### 15.5 seccomp·스탯 실측 (8/31)

표의 이 두 행은 코드만 읽고 적었다가 정정했다. 살아있는 커널 안에서 다시 쟀다.

**seccomp** — `/proc/<커널 pid>/status` (2 = filter 모드):

| | 커널(`init.py`) | 필터 수 | 적용 지점 |
|---|---|---|---|
| containerd | **Seccomp: 2** | 1 | runc가 컨테이너 init부터 — 예외 프로세스 없음 |
| enroot | **Seccomp: 2** | 2 | 에이전트가 BPF로 컴파일 → 게이트의 installer가 exec 직전 |
| apptainer | **Seccomp: 2** | 1 | 에이전트가 BPF로 컴파일 → 게이트의 installer가 exec 직전 |

커널이 띄우는 것들(`ssh-agent`, `bai-krunner`, `ipykernel`, `dropbear`, `ttyd`)도 전부 2로 상속된다.
rootless 두 곳에서 `Seccomp: 0`인 프로세스는 **런타임 자신의 발판**이다 — enroot는 `enroot-nsenter`,
apptainer는 `starter`/`appinit`. 사용자 코드가 아니고, 필터는 그 아래 exec 직전에 걸린다.

> **측정 함정**: cgroup에서 "호스트 netns가 아닌 첫 프로세스"를 커널로 골랐더니 apptainer에선
> `appinit`이 잡혀 `Seccomp: 0`이 나왔다. 하마터면 "apptainer는 unconfined"로 보고할 뻔했다.
> 프로세스를 `init.py`로 특정하도록 고쳤다.

**스탯** — `_resolve_stat_mode`가 설정과 무관하게 `StatModes.CGROUP`을 강제하고(조회할 Docker 데몬이
없으므로), `get_cgroup_path`가 OCI spec의 `linux.cgroupsPath`와 **같은 상수**로
`/sys/fs/cgroup/backend-ai/<kernel-id>`를 짚는다. net만 cgroup v2에 회계가 없어
`/proc/<container_pid>/net/dev`(또는 고정된 netns)에서 읽는다.

같은 부하(64 MiB 쓰기 + 200 ping)를 주고 에이전트가 내보내는 `backendai_container_utilization`:

| 지표 | containerd | apptainer |
|---|---|---|
| cpu_used | 1346.23 | 1254.35 |
| mem (현재/용량) | 118 MB / 2 GiB | 135 MB / 2 GiB |
| io_read | 4096 | 8192 |
| net_rx / net_tx | 299978 / 292349 | 11167 / 3672* |

*apptainer 쪽은 부하 없이 잰 회차라 유휴 트래픽 값이다 — 항목 유무가 논점이고, 둘 다 전 항목이 실제 값으로 채워진다.

**결론: rootless 두 백엔드는 스탯에서 containerd와 동일하다.** 수집기·지표 키·값이 모두 같고,
docker와는 출처만 다르다(docker API ↔ cgroup fs).

**다만 둘 다 똑같이 비어 있는 것 두 가지** — 백엔드 차이가 아니라 공통 사안이다:

| 관측 | containerd | apptainer | 성격 |
|---|---|---|---|
| 매니저의 커널별 `live_stat` | **null** | **null** | 에이전트는 값을 내보내는데 GQL까지 안 온다 (에이전트 레벨 `live_stat`은 정상) |
| `io_write` | **0** | **0** | 64 MiB를 썼는데 0 — cgroup `io.stat`이 그 쓰기를 회계하지 않음 |

둘 다 이 배포/공용 경로의 문제이므로 백엔드 비교표에서는 제외했고, 별도로 확인할 항목이다.

---

## 16. 고아 상태 정리 (8/31)

§13.4의 미해결 — 에이전트가 커널을 두고 죽으면 로그와 스크래치가 영원히 남는 문제 — 를 처리했다.
로그 상한 자체는 에이전트에 그대로 두기로 했으므로(에이전트 부재 구간은 감수), 요구사항은 둘로 좁혀졌다:
**돌아왔을 때 계속 진행**되고, **잘못 남은 것은 정리**될 것.

앞의 것은 이미 성립한다(§13.3 실측: 재기동 시 로테이터가 즉시 회수, 세션 RUNNING 유지, 종료 시 잔여 0).
남은 것이 후자였다.

### 16.1 두 스윕

`_sweep_orphan_cgroups`가 이미 하던 일을 나머지 두 산출물로 넓혔다.

| | 위치 | 판정 기준 |
|---|---|---|
| 컨테이너 로그 | `RootlessOciRuntime.configure_logging` | `_pids`에 없고 **그리고** cgroup에 프로세스가 없을 것 |
| 스크래치 | `ContainerdAgent.__ainit__` 끝 | 커널 레지스트리·런타임의 컨테이너 목록·cgroup **셋 다** 죽었다고 할 것 |

스크래치는 커널의 `/home/work`라 오탐이 곧 실행 중 세션의 작업 파일 손실이다. 그래서 **서로 독립인 세 근거**를
요구하고, 하나라도 "살아있다"고 하면 건드리지 않는다. 런타임에 물어볼 수 없으면(예외) 스윕 자체를 포기한다 —
근거 하나가 빠진 상태의 나머지 둘로는 지우지 않는다.

### 16.2 로그 스윕의 위치 — `open()`이 아니다

처음엔 cgroup 스윕 옆(`open()`)에 뒀는데 **조용히 아무 것도 안 했다.** `_log_root`는 `configure_logging`에서
설정되고 그건 `open()` **뒤**다(코드 주석이 이미 그렇게 적고 있었다). 라이브에서 고아 로그 4개가 그대로 남아
발견했다. `configure_logging`으로 옮겼다 — 로그 위치와 커널 생사를 둘 다 답할 수 있는 첫 시점이다.

> 유닛 테스트만 봤으면 못 잡았다. 스윕 함수 자체는 정상 동작했고, **호출 지점이 틀렸을 뿐**이다.
> 그래서 "`configure_logging`이 트리거"라는 테스트를 따로 넣었다.

### 16.3 실측

| | 재기동 전 | 재기동 후 |
|---|---|---|
| containerd 스크래치 | 13개 (고아 12 + 살아있는 커널 1) | **1개** — 고아 12개 제거, 살아있는 것 유지 |
| enroot 로그 | 5개 (고아 4 + 살아있는 커널 1) | **1개** — 고아 4개 제거, 살아있는 것 유지 |
| 세션 | RUNNING | **RUNNING** (양쪽 다 계속 진행) |

뮤테이션 7종 중 6종 검출, 1종은 죽은 코드였음이 드러나(`_tmp` 가드는 UUID 검사가 이미 덮음) 제거했다.
`tests/unit/agent::` 전체 green.

---

## 17. VXLAN 구현 분석 (9/1)

`network/backends/vxlan.py` 773줄과 협력 모듈(`coordinator`, `local_subnet`, `vtep`, `path_mtu`)을
읽고, 확실치 않은 것은 실측했다. 아래 표기: **[측정]** 실제로 재봄 / **[코드]** 코드 근거만 /
**[잠재]** 지금 기본값에선 안 터지지만 조건이 바뀌면 터짐.

### 17.1 잘 되어 있는 것 (먼저)

- 명령 조립이 순수 함수이고 부작용은 주입 가능한 러너 뒤에 격리돼 있다 — 그래서 유닛 테스트가 실재한다.
- MTU를 **노드가 직접 재서** 매니저 값과 대조하고, setup에서는 거부·adopt에서는 경고로 갈랐다.
  부작용 이전에 검사하므로 반쯤 만들어진 상태가 남지 않는다.
- `coordinator.reconcile_peers`가 피어 단위로 실패를 격리하고, 장치 op가 성공해야 기록을 지운다.
- 브리지 FORWARD ACCEPT를 직접 넣어 Docker/하드닝 호스트의 DROP 정책에서 살아남는다.
- 도달성 프로브의 에러 메시지가 원인 후보(Calico의 4789 차단)와 조치를 함께 말한다.
- **[측정]** `bridge fdb append`를 같은 dst로 두 번 해도 커널이 중복 제거한다(엔트리 1개, del 한 번에 삭제).
  재기동 후 `add_peer`가 다시 불려도 FDB가 부풀지 않는다 — 의심했다가 재보고 접었다.

### 17.2 가장 큰 문제 — ESP 정책이 세션이 아니라 **노드 쌍**에 걸린다

`xfrm_add_args`가 만드는 정책의 선택자는 `src VTEP / dst VTEP / proto udp / dport` 넷뿐이다.
**`spi`도 `mark`도 `if_id`도 없다** — `spi`는 state에만 들어간다. 반면 키는 세션마다 새로 만든다
(`secrets.token_hex(32)`).

따라서 같은 두 노드를 잇는 암호화 세션이 둘 이상이면 **정책은 하나를 공유**한다.

| 상황 | 결과 |
|---|---|
| 세션 A·B가 같은 노드 쌍에서 동시 실행 | 정책 1개 + SA 2개(SPI·키 다름). 커널이 그중 하나를 고르므로 **B의 프레임이 A의 키로 암호화될 수 있다** — 세션별 키 격리가 실질적으로 성립하지 않는다 |
| 그 상태에서 **A만 종료** | `policy del`이 선택자로 지우므로 **B의 정책까지 사라진다**. B의 SA는 남지만 정책이 없으니 B의 VXLAN이 **평문으로 나간다** |

두 번째가 특히 나쁘다. 조용하고, 로그도 없고, 세션 B는 계속 정상 동작한다. 재현 조건은
"암호화 세션 두 개가 같은 노드 쌍에 겹침"이라 특별하지 않다. (기본 `vxlan_port`가 같아서 선택자가
정확히 겹친다. 세션마다 포트를 달리 주면 우연히 갈린다.)

**방향**: 정책을 세션 단위로 구분해야 한다 — XFRM `mark`(VNI 유래)를 상태·정책 양쪽에 달거나,
정책 `tmpl`에 `spi`를 박는다. 지우는 쪽도 같은 구분자로 지워야 한다.

### 17.3 암호화가 조용히 꺼지는 경로가 하나 더 있다

`setup_session_network`는 `self_member.vtep_ip`가 없으면 `_self_vteps`를 채우지 않고 **그대로 진행**한다.
그 뒤 `_program_encryption`은 "this node's VTEP is unknown" 경고 한 줄을 남기고 **return**한다.
즉 **암호화를 요청한 세션이 평문으로 뜬다.** 세션은 정상 RUNNING이고 아무도 모른다.

암호화가 요청됐는데 프로그래밍할 수 없으면 세션을 거부하는 편이 맞다 — cgroup 위임 실패를 거부하도록
바꾼 것(`ea60bf73d`)과 같은 논리다. 약속한 속성이 없는데 성공으로 보고하는 것이 문제다.

### 17.4 부분 실패가 정리되지 않는다

`_program_encryption`은 4개 `ip xfrm` 명령을 차례로 실행하고 **전부 성공한 뒤에야**
`_encrypted_peers`에 기록한다. 3번째에서 실패하면 SA 2개가 커널에 남고 기록은 없다 →
`teardown_session_network`가 그 피어를 unprogram하지 않는다.

이게 나쁜 이유는 이 파일 자신의 주석이 설명한다: SPI가 `(vni, src, dst)`에서 나오므로
**같은 VTEP 쌍에서 VNI가 재사용되면 다른 키로 같은 SPI를 계산해 트래픽이 통째로 죽는다**
(실측 기록: `SAD 2 / SPD 1+1`이 죽은 피어를 가리켜 100% 손실). 부분 실패가 정확히 그 상태를 만든다.

**방향**: 명령 하나라도 성공하면 즉시 기록하고(또는 try/finally로), 실패 시 그 자리에서 되감는다.

### 17.5 LOCAL 브리지 이름과 서브넷이 서로 다른 키에서 나온다 **[잠재]**

| | 브리지 이름 | 서브넷 |
|---|---|---|
| bridge 백엔드 | `bailo<index>` | index |
| **vxlan 백엔드** | **`bailo<vni>`** | **index** |

`local_subnet.py`의 설계 문서는 "인덱스가 명명하는 것 — 브리지 장치 `bailo<index>`와 그 게이트웨이
서브넷 — 은 노드 전역 이름"이라고 못박고 있다. vxlan에서는 그 불변식이 깨져 있다.

기본값에선 안 터진다: VNI는 4096부터(`DEFAULT_VNI_RANGE`), 인덱스는 0부터 풀 크기까지라 숫자가 안 겹친다.
다만 `vni_range`는 설정 가능하고, 낮은 대역을 쓰는 순간 **한 노드에서 같은 이름의 브리지에 서로 다른
게이트웨이/서브넷이 걸린다.** `setup_session_network`가 시작할 때 `bailo<vni>`를 무조건 지우므로,
살아있는 다른 세션의 LOCAL 브리지를 지울 수도 있다.

`attach_endpoint`의 `meta.vni is None` 폴백이 문자열 `"bailo0"`인 것도 같은 계열이다 — vxlan에서는
도달 불가한 방어 코드지만, 하필 인덱스 0의 실제 장치 이름이다.

### 17.6 ARP 억제는 컨테이너 트래픽에 적용되지 않는다 **[코드]**

`neigh_replace_args`의 주석은 "known remote endpoint never triggers a broadcast ARP over the tunnel"이라
말하지만, 엔트리는 **호스트 netns의 브리지 장치**에 박히고 vxlan 장치에는 `proxy` 플래그가 없다
(`nolearning`만 있다). 브리지에 박힌 permanent neigh는 **호스트가 보내는** 트래픽에만 답한다.

컨테이너끼리의 ARP는 여전히 브로드캐스트되어 head-end replication으로 **모든 피어 VTEP에 복제**된다.
동작에는 문제가 없고(그래서 C2가 통과한다), 피어 수가 적을 땐 무시할 만하다. 다만 주석이 말하는 최적화는
실현되지 않았고, 큰 클러스터에서는 ARP마다 N배 복제가 된다.

**방향**: vxlan 장치에 `proxy`를 켜서 커널이 대신 답하게 하거나, 엔트리를 컨테이너 netns 안에 넣는다.
(아직 측정하지 않았다 — tcpdump로 터널 위 ARP를 세면 바로 확인된다.)

### 17.7 우선순위

| | 항목 | 성격 |
|---|---|---|
| 1 | 17.2 ESP 정책의 노드 쌍 공유 → 다른 세션 종료 시 **평문으로 강등** | 보안, 조용함 |
| 2 | 17.3 VTEP 없을 때 암호화 요청이 조용히 무시 | 보안, 조용함 |
| 3 | 17.4 부분 실패한 SA가 정리되지 않음 → VNI 재사용 시 전면 손실 | 가용성 |
| 4 | 17.5 LOCAL 브리지 명명 불일치 | 잠재 (설정 의존) |
| 5 | 17.6 ARP 억제 미실현 | 성능/문서 정확성 |

## 18. rootless podman 백엔드 (9/1)

### 18.1 왜 레이어를 나눴나

`RootlessOciRuntime` 1,100줄 중 계약은 네 가지뿐이다 — 상태를 어디에 두는지, 커널이 어떤
uid로 떨어지는지, 특권 작업을 어디로 보내는지, 레지스트리 스킴을 어떻게 정하는지. 나머지
전부(PID 저널, 프로세스 핸들, cgroup, 로그 로테이터, 2단계 게이트)는 **enroot·apptainer에
모니터가 없어서 에이전트가 모니터 노릇을 해야 하기 때문에** 존재한다.

podman은 conmon을 들고 온다. 컨테이너를 reparent하고, stdio를 쥐고, 로그 상한을 강제하고,
에이전트보다 오래 사는 레코드를 유지한다. 그 기계장치를 하나도 필요로 하지 않으면서 계약은
똑같이 진다. 상속하면 대부분을 꺼야 한다.

```
OciRuntime
  ├─ ContainerdGrpcRuntime          (데몬 소유, root)
  └─ RootlessOciRuntime             ← 계약만 (이름 유지)
       ├─ PodmanRuntime             (conmon이 소유)
       └─ SelfHostedRootlessRuntime ← 기존 900여 줄
            ├─ EnrootRuntime
            └─ SingularityRuntime
```

게이트(`rootless/gate.py`)와 cgroup 감금(계약 클래스)은 두 종류 모두가 지므로 공유 위치로
올렸다. 프로세스 트리 순회만 self-hosted에 남았다 — 에이전트가 띄운 런치 트리는 거기에만 있다.

### 18.2 podman이 주는 것 / 주지 않는 것 (전부 실측)

| | 결과 |
|---|---|
| 2단계 시작 | **없음.** `podman start` = 즉시 exec. 같은 게이트로 흉내냄 |
| 게이트 후 PID | 릴리스 전후 **동일** (1122667 → 1122667). attach 대상이 유지됨 |
| netns 소유 uid | **1000** — privnet의 `expected_owner_uid` 검사를 그대로 통과 |
| cgroup 배치 | **불가.** rootless는 `--cgroup-parent`를 사용자 위임 서브트리 기준으로 해석 |
| 비특권 이동 | **불가.** 공통 조상 규칙 — `/sys/fs/cgroup/backend-ai/<kid>`가 쓰기 가능해도 EPERM |
| 로그 상한 | **conmon이 강제.** 1 MB 지정 + 4 MiB 기록 → 842 KB. 로테이터 불필요 |
| 이벤트 | `podman events --format json` — self-hosted가 폴링해야 하는 것을 그냥 준다 |

결론: cgroup은 다른 rootless 백엔드와 **똑같이 privnet**으로 간다. 게이트에 잡혀 있는 동안
프로세스가 하나뿐이라 트리 순회도 필요 없다.

### 18.3 살려 놓고 돌려서 나온 버그 3개

읽어서는 안 나오고 노드에서 돌려야 나오는 것들.

1. **`podman start`가 영원히 안 돌아옴.** conmon이 넘겨받은 stdio를 컨테이너 수명 내내 쥔다.
   파이프로 읽으면 EOF가 안 온다. 증상이 최악 — 컨테이너는 게이트에 도달해 그대로 있고,
   에러도 타임아웃도 없고 가리킬 자식 프로세스도 없다. **파일로 받으면** conmon이 계속 열고
   있어도 끝이 있다.
2. **커스텀 `XDG_RUNTIME_DIR`이 모든 이미지 pull을 조용히 깼다.** podman은 rootless userns를
   거기 두고 pause 프로세스가 쥔 것에 **합류**한다. 우리 디렉터리를 가리키면 합류할 게 없어
   /etc/subuid 범위 대신 **uid 하나만** 매핑한 네임스페이스를 만든다
   (`0 1000 1` vs 정상 `0 1000 1` + `1 100000 65536`). 다른 id 소유 레이어가 unpack에서 죽는다.
   → 커널 uid의 진짜 `/run/user/<uid>`를 쓰고, 없으면 `loginctl enable-linger`를 안내.
3. **로그 루트 디렉터리를 아무도 안 만든다.** conmon은 rootless 런치 안에서 로그를 열고
   디렉터리를 만들지 않는다. 이미지 pull과 컨테이너 생성이 다 끝난 뒤 *start*가 실패한다.
   containerd는 root 데몬이 경로를 만들어 줘서 겪을 일이 없었다.
4. **종료된 커널의 로그가 남았다** (F5/B4). 경로를 우리가 지었으니 podman은 자기 것으로 보지
   않는다. `remove_container`에서 `unlink_log_files`.

### 18.4 인수 테스트 결과 (단일 노드)

`./run.sh pm` — 피어 노드에 podman이 없어 멀티노드(B2/C1–C7/B3)는 실행 불가.

| 통과 | A1 A2 B1 B4 D1 D2 D4 E2 F3 G1 G4 |
|---|---|
| 확인된 사실 | seccomp filter 모드(커널+자손 6개), `memory.max=2147483648`/`cpuset.cpus=0-3`, 커널 cgroup이 에이전트와 분리, 에이전트 SIGKILL 후 커널 생존, 좀비 0 |

F1은 로그 파일 **모양**이 다르다 — conmon은 회전 형제를 두지 않고 한 파일에 전체 예산을 쓴다.
총량은 동일하므로 스위트의 백엔드 표에 `backend_log_files` 행을 넣어 표현했다.
