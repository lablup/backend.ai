# Tier 1 — 재시작·복구 매트릭스 (초안)

> 상태: **리뷰 대기**. 시나리오 목록 합의 전까지 구현 착수하지 않는다.
> 전제: 모든 시나리오는 `leak_guard`를 붙인다. 아래 "기대"는 그 위에 추가로 확인할 것만 적는다.
>
> 하네스(Tier 0)는 완성돼 있고, 이미 **결함 5건**을 잡았다 — "발견된 결함" 절 참조.
> 그중 3건은 실행으로 재현됐다. 시나리오는 그 결함들을 닫는 형태로 정렬돼 있다.

## 왜 이 그룹인가

`next.md` §3의 결함 이력과 `session_network.py`의 docstring이 같은 곳을 가리킨다 — **재시작 복구
경로**. 1·2차 리뷰에서 나온 파괴적 결함 2건(VTEP 가드 우회, M3 락 pop 순서)이 모두 여기였고,
단위 테스트로는 잡히지 않았다. 아래 시나리오 중 `회귀` 표시는 **이미 한 번 터진 결함**을 고정하는
것이므로 우선순위가 가장 높다.

## Docker가 기준값이다 — 다만 어디까지인지가 갈린다

**원칙: 기대값은 사람이 적지 않는다. Docker 백엔드가 실제로 하는 동작이 기준이다.**
다만 두 백엔드는 네트워크 **소유권 구조**가 다르고, 그 경계가 곧 이 원칙이 적용되는 경계다.

| | Docker | containerd (이 브랜치) |
|---|---|---|
| 오버레이 생성 | 매니저가 `docker network create -d overlay` (Swarm) | 에이전트가 vxlan 디바이스·브리지를 직접 만듦 |
| 에이전트가 하는 일 | 컨테이너 config에 네트워크 이름만 꽂음 (`join_network`) | VXLAN·FDB/ARP·IPAM·서브넷 블록·iptables·netns 전부 |
| 커널이 떠날 때 | **`leave_network`가 no-op (`pass`)** | detach + veth 삭제 + 주소 반환 + 블록 반납 |
| 데이터플레인 소유자 | dockerd / swarm | **에이전트 프로세스** |

여기서 나오는 결론 두 가지:

**(1) 사용자 관찰 가능한 계약 → Docker에서 뽑는다.** 커널 생존, 세션 유지, 재시작 후 재접속,
teardown 후 사용자 관점 상태, 에러 타입, MTU 동작, 세션 간 격리, 포트 퍼블리시, cgroup·rlimit 값.
이건 사람이 기대값을 적으면 안 되고, **같은 시나리오를 Docker 모드로 돌린 결과를 골든으로 삼는다**
(→ 아래 그룹 P). `mode`는 에이전트 설정의 단일 스위치(`docker` / `containerd`)라 같은 스위트를 두 번
돌릴 수 있다.

**(2) 내부 리소스 복구 → Docker에 기준값이 없다.** `_reclaim_orphans`, `net-ipam`,
`net-local-subnet` 저널, refcount 락, VTEP 발행, `_recover_attachment` — Docker에는 대응물이
아예 없다. `leave_network`가 no-op인 이유가 정확히 그것이다.

> 뒤집어 보면 이게 이 계획에서 가장 중요한 사실이다. Docker 기준으로는 **"에이전트 재시작 시
> 네트워크를 복구한다"는 문제 자체가 존재하지 않았다.** dockerd가 자기 상태를 자기가 복구했으니까.
> containerd 백엔드는 dockerd가 하던 일을 통째로 떠안았고, 따라서 **A·C 그룹은 패리티 검증이 아니라
> 이 브랜치가 새로 만들어낸 리스크**다. 실제로 지금까지 터진 파괴적 결함이 전부 여기 몰려 있는 것도
> 우연이 아니다. 이 그룹의 기대값을 Docker에서 뽑으려는 시도는 헛수고고, 코드의 불변식에서 뽑아야
> 한다 — 단, **최종 사용자 관점 결과는 여전히 Docker와 같아야 한다**(그건 그룹 P가 본다).

각 시나리오 표의 `기준` 열이 이 구분을 나타낸다: **D**=Docker에서 뽑음, **I**=불변식에서 뽑음.

## P. 백엔드 패리티 (골든)

같은 시나리오를 `mode=docker`와 `mode=containerd`로 각각 돌리고, **사용자 관찰 결과가 같은지**
비교한다. 기대값을 문서에 적지 않는 것이 핵심이다 — Docker 실행 결과가 곧 기대값이다.

| ID | 시나리오 | 비교 대상 | 상태 |
|---|---|---|---|
| P1 | 단일 커널 세션 생성 → 사용 → 삭제 | 커널 상태 전이, 접속 가능 포트, 종료 코드 | ⬜ |
| P2 | 2노드 클러스터 세션 | `/etc/hosts`, `BACKENDAI_CLUSTER_HOSTS`, 전 커널쌍 연결성 | ⬜ |
| P3 | agent 재시작 (SIGTERM/SIGKILL) | 재시작 후 커널 생존 여부와 사용자 관점 재접속 | ⬜ |
| P4 | MTU 경계 동작 | `ping -M do` 통과/실패 경계값 | ⬜ |
| P5 | 세션 간 격리 | 도달 가능/불가 매트릭스 | ⬜ |
| P6 | 포트 퍼블리시 | 바인딩 주소, 도달성 | ⬜ |
| P7 | cgroup·rlimit 값 | 컨테이너 안에서 읽은 limit 값 | ⬜ |
| P8 | 실패 경로의 에러 | 사용자에게 보이는 에러 타입·메시지 | ⬜ |
| P9 | GPU 세션의 `cuda_mem`/`cuda_util` | Docker에서 나오는 측정치가 containerd에서도 나와야 함 (현재 containerd는 0) | 🔴 ⬜ |

**주의**: 한 세션이 두 백엔드에 걸칠 수 없다(`require_members_can_serve_driver`가 driver 능력으로
멤버를 거른다). P는 "두 백엔드 혼합"이 아니라 **같은 스위트의 두 번 실행**이다.

**HOST 네트워크 세션은 패리티 대상이 아니다.** `HostNetworkPlugin`은 v1 엔트리포인트
(`backendai_network_agent_v1`)에만 등록돼 있고 `AbstractNetworkAgentPlugin[DockerKernel]`로 타입까지
묶여 있다. containerd가 쓰는 v2 레지스트리에는 `vxlan`뿐이고, `NetworkBackendKind`도 `VXLAN`/`BRIDGE`
둘뿐이라 HOST가 없다 — **containerd 백엔드에 존재하지 않는 모드**다. P를 확장할 때 HOST 세션을 넣으면
containerd 쪽이 통째로 실패하는데, 그건 버그가 아니라 미구현이다.

### Docker 기준선 상태 (측정함)

Docker collector(`collectors/docker_objects.py`)를 이 호스트에 돌린 결과:

| 항목 | 결과 |
|---|---|
| 클러스터 네트워크(`bai-multinode-*`) 잔존 | **0** |
| 주인 없는 netns 샌드박스 | **0** — `/var/run/docker/netns/`의 16개 전부 주인 확인됨 |
| exited kernel 컨테이너 | **4** (2026-05-26 ~ 06-28 종료, 미제거) |

exited 4개는 매니저 DB에 **레코드가 없었다**(kernels 63행, 해당 id 0행 / sessions 0행). halfstack
DB가 리셋된 뒤 남은 옛 찌꺼기이고 에이전트 버그가 아니다. `docker rm`(`-v` 없이 — `volume` 하나가
모든 커널이 공유하는 krunner 볼륨) 후 재측정:

| 항목 | 전체 스캔 | 필터 결과 |
|---|---|---|
| networks | 6 | 클러스터 네트워크 **0** |
| containers | 46 | `kernel.*` **0** |
| sandboxes | 파일 16 (점유 14 + 호스트/swarm 3 − 중복 1) | 주인 없음 **0** |

**Docker 기준선 = 깨끗**, `quiesced=True`. 전체 스캔 수를 함께 남기는 이유는 "깨끗해서 0"과
"collector가 망가져서 0"을 구분하기 위해서다. P 그룹의 전제 조건은 충족됐다.

> **netns를 원시 목록으로 수집하면 안 된다.** 건강한 호스트는 컨테이너 수만큼 샌드박스를 갖는다.
> 파일 목록만 보고 "쌓여 있다"고 판단하면 실행 중인 서비스 전부를 누수로 신고하게 되고, 실제로
> 이 문서 작성 중 그 오경보를 한 번 냈다. collector는 `docker ps -a`의 `SandboxKey`와 대조해
> **주인 없는 것만** 리소스로 센다. `1-<netid>`(오버레이 네트워크 자신의 샌드박스)와 swarm의
> 영구 `ingress`는 네트워크 소유라 제외한다.

### 정리 중 발견 — scratch 디렉터리 (미해결)

`docker rm`은 bind 마운트를 지우지 않는다. 확인해보니 **커널이 사라진 뒤에도 scratch 디렉터리가
남는다**. `MountCollector`는 `findmnt` 기반이라 이걸 못 본다(마운트 해제된 디렉터리라서). 그래서
`ScratchDirCollector`를 추가했다 — 살아있는 컨테이너 *레코드*가 없는 디렉터리만 리소스로 센다.

현재 이 호스트:

| scratch root | 고아 |
|---|---|
| `./scratches` (halfstack의 실제 `scratch-root`) | 1 — `783ad6cc…` |
| `/var/lib/backend.ai/scratches` (옛 설정) | 4 — 방금 지운 커널 3개분 + `ff534fb1…` |

**`783ad6cc…`가 문제다.** DB에서 `TERMINATED` (2026-07-10, `agent=i-charsyam-nvidia`) — 즉 커널이
정상 종료됐는데 scratch가 12일째 남아 있다. DB 리셋 찌꺼기가 아니라 **실제 라이프사이클에서 나온
잔여물**이다. 나머지 4개는 DB에 레코드가 없어 판단 불가(옛 찌꺼기로 보인다).

이후 하네스로 **생성 중단 경로에서 같은 클래스를 재현**했다(BUG3). 정상 종료 경로도 새는지는
아직 미확정이다(BUG4). 자세한 내용과 시나리오 매핑은 "발견된 결함" 절 참조 — B7 / A8.

> scratch는 사용자 work 데이터를 담고 있으므로 **하네스는 검출만 하고 절대 지우지 않는다.**

`scratch_roots` 기본값(`/var/lib/backend.ai/scratches`)은 dev 셋업과 다르다. 틀린 root를 가리키면
조용히 0을 반환하는 대신 **raise** 하도록 했다 — 그게 이 스위트가 낼 수 있는 최악의 거짓 음성이다.
`BAI_DATAPLANE_SCRATCH_ROOTS`로 에이전트의 `scratch-root`에 맞춰야 한다.

## 축

| 축 | 값 |
|---|---|
| 죽는 대상 | agent / containerd / privnet / etcd / 노드 전체 |
| 방식 | SIGTERM(graceful) / SIGKILL |
| 타이밍 | 정상 운영 중 / 세션 생성 중 / teardown 중 |
| 노드 | 단일 / 2노드(coordinator·peer) / 한 호스트 2에이전트 |

전 조합은 100개가 넘는다. 아래는 **불변식 기준으로 고른 부분집합**이다 — 각 시나리오는 지켜야 할
불변식 하나에 대응하고, 그 불변식이 코드 어디에 적혀 있는지 함께 적었다.

---

## A. 에이전트 재시작 (단일 노드)

| ID | 시나리오 | 기대 | 기준 | 근거 | 상태 |
|---|---|---|---|---|---|
| A1 | 세션 2커널 실행 중 agent SIGTERM → 재시작 | 커널 생존. 재시작 전후 스냅샷 **완전 동일**(delta 0). coordinator/orchestrator/tracker/attachment 재구성 | D+I | `recover()` | ⬜ |
| A2 | 같은 조건, SIGKILL | A1과 동일 | D+I | `recover()` | ⬜ |
| A3 | 재시작 **후** 정상 teardown | 모든 리소스 baseline 복귀. 특히 host veth와 IPAM lease | D+I | `_recover_attachment` — 복원 실패 시 detach 불가 | ⬜ |
| A4 | agent 다운 중 커널 task 사망 → 재시작 → `clean_kernel` | veth·주소 반환. sentinel PID 경로가 동작 | I | `_recover_attachment` 회귀 (이전엔 None 반환 → 노드 수명 내내 누수) | 🔴회귀 ⬜ |
| A5 | agent 다운 중 매니저가 session meta 삭제 → 재시작 | 컨테이너는 untracked, **블록·주소는 회수되지 않음**(live니까) | I | `_reclaim_orphans` — live 기준, resume 성공 기준 아님 | 🔴회귀 ⬜ |
| A6 | 재시작 시점에 etcd 도달 불가 | resume 실패해도 커널 생존·블록 유지. etcd 복구 후 재수렴 | I | `recover()`의 per-session try/except | ⬜ |
| A7 | 한 호스트 2에이전트, agent1만 재시작 | **agent2의 커널·주소·블록 무사** | I | `_live_containers` 비필터 뷰 — 필터하면 남의 커널을 orphan으로 오인 | 🔴회귀 ⬜ |
| A8 | 커널 정상 생성 → 정상 종료 | scratch 디렉터리 반환 | D+I | 결함 **BUG4** — `783ad6cc`가 12일째 잔존. 정상 경로 누수 여부 미확정 | ⬜ |
| A9 | 포트를 퍼블리시한 커널 실행 중 agent 재시작 | published port가 재시작 전과 **동일하게 열거**됨. 포트 풀이 이중 할당하지 않음 | I | `port_forward.py`: *"iptables itself is the record … an agent restart can enumerate the published ports without any journal of its own"* — 명시된 불변식인데 대응 시나리오가 없었다. 라이브에서 이 경로가 실제로 실패했다(BUG1 환경) | ⬜ |

**A7 셋업**: 한 호스트에 에이전트 2개. 하네스가 직접 띄운다 — 아래 "2에이전트 구성" 참조.

## B. 세션 생성 중 중단

| ID | 시나리오 | 기대 | 기준 | 근거 | 상태 |
|---|---|---|---|---|---|
| B1 | `ensure_session` 성공 직후 취소 | 데이터플레인·멤버십·블록 전부 롤백 | D+I | `362672685` 취소 롤백 커밋 | ⬜ |
| B2 | CNI attach 성공 후 DB 단계 실패 | CNI 리소스 롤백 | D+I | `b036089cd` | ⬜ |
| B3 | 포트 예약 후 컨테이너 create 실패 | 예약 포트 반환 | D+I | `5529d7952`, `f60595402` | ⬜ |
| B4 | 컨테이너 create 후 start 전 실패 | 컨테이너·스냅샷 제거, veth·주소 반환 | D+I | `4530934bb` | ⬜ |
| B5 | 생성 한복판에서 agent SIGKILL → 재시작 | 반쯤 만들어진 리소스가 orphan sweep으로 회수 | I | `_reclaim_orphans` | ⬜ |
| B6 | 세션의 커널 A가 이미지 pull 중, 커널 B가 조기 실패 | **세션 네트워크가 무너지지 않음** (B가 마지막 커널로 오인되지 않음) | I | `tracker.reserve` — 컨테이너가 아닌 `ensure_session` 시점부터 카운트 | 🔴회귀 ⬜ |
| B7 | `apply_network` 실패 → 커널 정리 | **scratch 디렉터리 반환** | I | 결함 **BUG3** — 하네스가 재현함(`8a3bffe5`). `scratch prepared` 다음 단계가 실패하면 scratch가 남음 | 🔴재현됨 ⬜ |

## C. teardown 중 중단 / 동시성

| ID | 시나리오 | 기대 | 기준 | 근거 | 상태 |
|---|---|---|---|---|---|
| C1 | teardown 중 SIGKILL → 재시작 | 남은 리소스 회수, delta 0 | I | `_reclaim_orphans` | ⬜ |
| C2 | 마지막 커널 teardown과 새 커널 `ensure_session` 동시 | 데이터플레인 중복 셋업 없음, 디바이스 삭제 후 재생성 없음 | I | `_session_locked` refcount — 옛 pop 순서에서 실패 확인됨 | 🔴회귀 ⬜ |
| C3 | 한 호스트 2에이전트, agent1의 마지막 커널만 teardown | agent1은 **withdraw만**, 브리지·블록 유지 | I | `teardown_session`의 `running` 분기 | 🔴회귀 ⬜ |
| C4 | 같은 세션 동시 teardown ×N | 블록 이중 반납 없음, 다음 세션이 살아있는 브리지를 삭제하지 않음 | I | `local_subnet_of`가 비할당 lookup | 🔴회귀 ⬜ |
| C5 | 50세션×4커널 동시 생성 → 동시 삭제 | 중복 IP 0, 중복 VNI 0, 중복 블록 0. delta 0 | D+I | SubnetAllocator/VNIAllocator CAS 스캔 | ⬜ |

## D. containerd

| ID | 시나리오 | 기대 | 기준 | 근거 | 상태 |
|---|---|---|---|---|---|
| D1 | containerd graceful restart | **shim 생존 → 커널 생존**. 재연결 후 task 목록이 재시작 전과 일치. health checker unhealthy→healthy 전이가 로그/메트릭에 보임 | I | `health/containerd.py`. 아래 주석 참조 | ⬜ |
| D2 | containerd SIGKILL | D1과 동일 | I | 아래 주석 참조 | ⬜ |
| D3 | containerd 다운 중 커널 생성 요청 | `BackendAIError` 계열로 실패. 부분 리소스 0 | **D** | 내장 예외 금지 규칙 | ⬜ |
| D4 | containerd 응답 지연(수십 초) | 에이전트가 같이 죽지 않음. 명령 타임아웃이 에러로 표면화 | **D** | | ⬜ |

**D1·D2가 `D`가 아니라 `I`인 이유**: 두 런타임이 구조적으로 다르다. dockerd 재시작은 기본적으로
컨테이너를 정지시키고(`live-restore` 설정에 좌우됨), containerd 재시작은 shim이 별도 프로세스라
task가 생존한다. "Docker와 같아야 한다"가 성립하지 않고, Docker 쪽 기대값 자체가 데몬 설정에 따라
달라진다. 불변식(shim 생존 + 에이전트 재연결)에서 뽑아야 한다.

## E. privnet

| ID | 시나리오 | 기대 | 기준 | 근거 | 상태 |
|---|---|---|---|---|---|
| E1 | privnet SIGKILL → 재시작 | 저널 소유권 유지, 세션 생존 | I | `a755356df` helper 재시작 복구 | ⬜ |
| E2 | privnet 소켓 끊긴 상태에서 attach 요청 | 명확한 에러, 반쯤 만든 veth 없음 | I | | ⬜ |
| E3 | privnet 모드에서 agent 재시작 | 저널은 privnet 소유 → 에이전트가 reclaim 시도하지 않음 | I | `_reclaim_orphans`의 `None` 분기 | ⬜ |
| E4 | privnet 다운 중 커널 생성 | 생성이 **실패로 매니저에 전파**됨. 세션이 CREATING에 매달리지 않음 | I | 결함 **BUG1** — 재현함. 에이전트는 즉시 실패했으나 커널은 10분 뒤에도 PREPARED | 🔴재현됨 ⬜ |
| E5 | privnet 도달 불가 시 에러 타입 | `BackendAIError` 계열. 로그에서 원인 식별 가능 | I | 결함 **BUG2** — 현재 `ConnectionRefusedError`(내장 예외), `exception.message`가 `111`뿐 | 🔴재현됨 ⬜ |

## F. etcd

| ID | 시나리오 | 기대 | 기준 | 근거 | 상태 |
|---|---|---|---|---|---|
| F1 | etcd 정지 → 재개 | watch 재구독. **핫 스핀 없음**(재시작 동안 agent CPU 정상) | I | `_watch` 백오프 — 정상 종료 경로에도 sleep | 🔴회귀 ⬜ |
| F2 | etcd 다운 중 피어 합류 → etcd 복구 | 15초 이내 FDB/ARP에 반영 | I | `_reconcile_periodically` | 🔴회귀 ⬜ |
| F4 | 피어 1개의 device op 실패 주입 | 나머지 피어는 정상 프로그래밍됨 | I | `reconcile_peers` 격리 | 🔴회귀 ⬜ |

**F3 제거됨** (read↔subscribe 갭에 키 변경 주입): 재현이 etcd 내부 타이밍에 의존해 결정론적으로
만들기 어렵고, F2가 같은 불변식(주기 재수렴)을 훨씬 덜 인위적인 방법으로 덮는다. ID는 재사용하지
않는다.

## G. 클러스터 세션 (2노드 + 단일노드)

| ID | 시나리오 | 기대 | 기준 | 근거 | 상태 |
|---|---|---|---|---|---|
| G1 | peer 노드 agent 재시작 | 이쪽 노드의 FDB/ARP **유지**. 멤버 레코드가 `vtep_ip: null`로 덮이지 않음 | I | `_self_member` VTEP 가드 — `_resume_session` 우회가 파괴적이었음 | 🔴회귀 ⬜ |
| G2 | peer 노드 전체 재부팅 | stale VTEP 키 회수, 재합류 후 연결성 복구 | D+I | `f0efbee9f` | ⬜ |
| G4 | VTEP 설정 불량 노드가 세션 참여 시도 | `UnusableVtep`로 거부. **메시 무손상** | I | `ensure_session` + `_resume_session` 양쪽 가드 | 🔴회귀 ⬜ |
| G5 | 크로스노드 연결성 매트릭스 | 전 커널쌍 ICMP/TCP 양방향 성공. **음성 대조군**: 노드 간 UDP 4789를 잠시 막으면 연결이 끊겨야 한다 | **D** | 아래 주석 | ⬜ |
| G6 | MTU 경계 (`ping -M do -s 1422/1423`) | Docker 오버레이와 **같은 경계값**에서 통과/실패. 대용량 TCP 전송 완료 | **D** | `5e1b3b476` MTU 블랙홀 | 🔴회귀 ⬜ |
| G7 | 세션 간 격리 | 다른 세션 커널에 도달 불가 | **D** | `664a4ab9a` LOCAL 브리지 격리 (최신 커밋) | 🔴회귀 ⬜ |
| G8 | torchrun/NCCL allreduce 2노드 | 완주. 마스터가 오버레이 IP에 바인딩(루프백 아님) | **D** | M6 `/etc/hosts` 회귀 | 🔴회귀 ⬜ |
| G9 | **단일노드 클러스터 세션** (`cluster_size>1` + `SINGLE_NODE`) | 피어가 노드 로컬 /26에 **결정론적으로** 배치됨. 모든 커널의 `/etc/hosts`가 전체 피어를 담고 자기 호스트명이 `127.0.1.1`로 덮이지 않음. `BACKENDAI_CLUSTER_HOSTS` 전 커널 동일. 전 커널쌍 연결성 | D+I | M6 (`a4a3414e6`, `16401871d`, `e23bb2c51`) — 2노드와 **완전히 다른 경로**이고 결함이 가장 많이 나온 곳 | 🔴회귀 ⬜ |

---

**G5의 음성 대조군이 필요한 이유**: 연결성 테스트는 *틀린 이유로* 통과할 수 있다. 트래픽이 우리가
만든 VXLAN 터널을 지나가는지, 아니면 다른 경로로 가는지 구분하지 못하기 때문이다. 구체적인 실패
모드가 하나 있다 — `BAI_DATAPLANE_NODES`를 잘못 설정해 양쪽이 같은 호스트를 가리키면 G5는 오버레이가
완전히 죽어 있어도 자명하게 통과한다. UDP 4789를 잠시 막아 연결이 **끊기는지** 보면 그것이 증명된다.

> 4789 차단을 독립 시나리오로 두지 않는 이유: 막으면 안 되고 풀면 되는데 그 사이에 **에이전트는
> 아무것도 하지 않는다**(etcd는 4789를 쓰지 않으므로 컨트롤 플레인도, 주기 재수렴도 영향 없다).
> 독립 시나리오였다면 리눅스 커널과 iptables가 동작하는지를 검증하는 셈이다.

## 발견된 결함 (하네스 실행으로 확인)

Tier 0 하네스를 세우고 시나리오를 짜는 과정에서 나온 것들. 각 결함은 대응 시나리오 ID를 갖는다 —
**시나리오가 통과하면 결함이 닫힌 것**이다.

| ID | 결함 | 상태 | 시나리오 |
|---|---|---|---|
| **BUG1** | privnet 다운 시 커널 생성 실패가 매니저에 전파되지 않음 → 세션이 CREATING에 무한 대기 | 재현됨 | E4 |
| **BUG2** | privnet 도달 불가가 내장 예외 `ConnectionRefusedError`로 노출 (`exception.message` = `111`) | 재현됨 | E5 |
| **BUG3** | `apply_network` 실패 시 직전 단계가 만든 scratch 디렉터리가 롤백되지 않음 | 재현됨 | B7 |
| **BUG4** | 정상 TERMINATED 커널의 scratch 잔존 (`783ad6cc`, 12일) | **미확정** | A8 |
| **BUG5** | containerd 커널의 GPU 사용량이 항상 0으로 보고됨 | 확인됨 | P9 |

### BUG1–BUG3 재현 기록 (2026-07-22)

세션 `dataplane-smoke-1` 생성 → 종료. Loki에서 확인한 에이전트 타임라인:

```
05:12:05.175  rpc::create_kernel(k:8a3bffe5…)
05:12:05.186  scratch prepared              ← 마지막 성공 단계
05:12:05.???  apply_network → ensure_session → coordinator.start
              → privnet/client.py setup_session_network
              → ConnectionRefusedError: [Errno 111]  (/tmp/backend.ai/net-privnet.sock)
   (10분 경과 — 커널 행은 계속 PREPARED, containerd에 컨테이너 없음)
05:22:35      수동 terminate → "unknown kernel" / "no container_id" / "already dead?"
```

매니저의 `scheduling-history`는 같은 시각에 `create_kernels SUCCESS "Kernel creation requested"`.
**에이전트는 즉시 실패했는데 매니저는 성공으로 기록했다** — BUG1.

종료 후 `leak_guard` delta:

```
LEAKED: 1
  + scratch-dir|…/scratches/8a3bffe5-d35c-4358-8eb4-50eead10c218
COLLATERAL: 0
```

BUG3. `MountCollector`(findmnt)로는 안 보이고 `ScratchDirCollector`만 잡는다.

**주의**: 이 재현은 privnet이 죽은 환경에서 나왔다. BUG3가 *생성 중단 경로* 전용인지, BUG4(정상 종료
경로)와 같은 뿌리인지는 **아직 구분되지 않았다.** A8이 그것을 가른다.

### BUG5 — GPU stats가 containerd에서 비는 이유 (분석 완료, 수정 보류)

> 이 항목은 데이터플레인 스위트의 범위 밖이지만, P9의 기대값을 정하려면 원인을 알아야 하므로 기록한다.

이 코드베이스는 이미 **"런타임 중립적인 형태로 되묻는다"** 를 채택했다:

- `get_resource_spec_from_container(container_info)` — 컨테이너의 `/home/config` 마운트 소스에서
  `resource.txt`(에이전트가 쓴 할당)를 읽는다. docstring: *"Runtime-neutral by intent."*
- `containerd/agent.py:1885-1893` — containerd 백엔드가 `HostConfig.Mounts`를 **합성**해서 같은
  헬퍼가 양쪽 백엔드에서 동일하게 동작하게 만든다.

문제는 **stats 경로 하나만 이 컨벤션에서 빠져 있다**는 것:

| 경로 | container_info 출처 | containerd |
|---|---|---|
| `restore_from_container(container, alloc_map)` | 에이전트가 `container.backend_obj`를 넘김 | ✅ |
| `gather_container_measures(ctx, container_ids)` | 플러그인이 `aiodocker`로 직접 조회 | ❌ 404 |

`AbstractComputePlugin.gather_container_measures`가 **컨테이너 ID만** 받기 때문에, 플러그인은
런타임에 되묻는 것 말고 방법이 없다. 그래서 `cuda_open`은 Docker 전용 `HostConfig.DeviceRequests`를
읽고, 엔터프라이즈 플러그인은 올바른 중립 헬퍼를 쓰면서도 그릇을 `aiodocker`로 떠온다. 둘 다
containerd에서 `DockerError(404)` → `continue` → **측정치 0**. 예외가 아니라 WARNING이라 조용하다.

호출부는 필요한 것을 이미 들고 있다 (`agent.py:1404`):

```python
for kernel_obj in [*self.kernel_registry.values()]:
    ...
    container_ids.add(ContainerId(kernel_obj.container_id))   # container_id만 남기고 버림
```

버려지는 `kernel_obj`에 `resource_spec`이 있다(`kernel.py:187`). 재시작 후에도 유효하다 —
`kernel_registry/types.py:59`의 영속화 스키마에 `resource_spec`이 포함되고, 컨테이너에서 복구하는
로더도 `loader/container.py:47`에서 이를 채운다.

**수정 방향**: `collect_container_stat`이 `container_ids` 대신 커널 객체(또는
`{container_id: resource_spec}` 매핑)를 넘긴다. `restore_from_container`가 이미 `Container`를 받는
선례가 있으므로 새 개념 도입이 아니라 **일관성 보수**다. 되묻는 구조는 유지된다.

**보류 사유**: `AbstractComputePlugin`은 사외 플러그인도 구현하는 공개 API라 시그니처 변경의 하위
호환 전략(optional 인자 추가 vs 새 메서드)을 먼저 정해야 한다. 이는 이 스위트의 결정 사항이 아니다.

**미확인**: k8s 백엔드(`kubernetes/intrinsic.py`)가 같은 누락인지, 선례가 있는지 안 봤다.

---

## 실행 드라이버 (결정됨)

세션을 만드는 경로를 그룹별로 나눈다. 빠른 것과 현실적인 것을 갈라 쓰되, 하네스 표면이 두 배가
되는 값은 치른다.

| 드라이버 | 그룹 | 이유 |
|---|---|---|
| **에이전트 RPC 직접** | A, C, D, E, F | 복구·동시성·인프라 장애는 반복 횟수가 많다(C5는 200커널). 매니저를 끼면 한 라운드가 몇 배 길어지고, 실패했을 때 원인이 에이전트인지 매니저인지 흐려진다. 매니저가 쓰는 etcd 레코드(meta/endpoints/ipam)는 테스트가 직접 심는다. |
| **매니저 API (SDK v2)** | B, G | 생성 롤백과 2노드 워크로드는 매니저의 상태와 맞물릴 때만 의미가 있다. G8(torchrun)은 애초에 매니저 없이는 성립하지 않는다. |

**자격증명 격리 (실행하며 확인된 요구사항)**: `./bai`의 설정 경로는 `Path.home() / ".backend.ai"`
로 고정돼 있고 env 오버라이드가 없다(`client/cli/v2/helpers.py:22`). 하네스가 개발자의 실제 config를
덮어쓰지 않으려면 **`HOME`을 테스트 전용 디렉터리로 돌려** 별도 키페어를 써야 한다. 또한 키페어당
동시 세션 한도(기본 5)가 있으므로, 시나리오용 키페어는 사람이 쓰는 것과 **분리돼야 한다** — 그렇지
않으면 개발자의 실행 중인 세션이 한도를 채워 스위트가 실패한다(실제로 발생).

**주의 — RPC 드라이버의 고유 위험**: 테스트가 심는 etcd 레코드가 매니저가 실제로 쓰는 것과
어긋나면, 시나리오는 통과하는데 프로덕션은 깨지는 최악의 조합이 된다. 레코드 작성은 반드시
`common/network/keys.py`와 `SessionNetMeta.to_etcd_payload()` 등 **매니저와 공유하는 코드**로만
하고, 손으로 쓴 JSON 리터럴을 두지 않는다. 이 규칙은 `AGENTS.md`에도 넣는다.

## 2에이전트 구성 (결정됨)

A7·C3용 두 번째 에이전트는 **하네스가 직접 띄운다**(fixture 기동/종료). 핵심은 두 에이전트가
**같은 containerd 네임스페이스와 같은 호스트 상태 저장소를 공유**해야 한다는 것 — 저널이 공유되는
상황이 바로 A7·C3가 방어하는 대상이다.

| 갈라야 하는 것 | 공유해야 하는 것 |
|---|---|
| `agent-id`, rpc-listen-addr, service-addr, agent-sock-port, pid-file, scratch-root | containerd namespace(`backend-ai`), `/var/lib/backend.ai/net-local-subnet`, `net-ipam`, etcd namespace, 노드 네트워크 풀 |

리스크: 에이전트 기동 로직이 하네스로 새어 들어오고 실패 모드가 늘어난다. 완화 — 두 번째 에이전트는
`configs/agent/`의 실제 템플릿을 오버라이드해서 띄우고, 기동 실패는 skip이 아니라 **에러**로
표면화한다(조용히 안 도는 하네스가 가장 나쁘다).

## 남은 결정 (이의 없으면 아래 기본값으로 진행)

| # | 항목 | 기본값 |
|---|---|---|
| 1 | B1–B4 실패 주입 방법 | **(a) 해당 단계 직전 SIGKILL + (b) etcd/containerd 차단만.** 테스트 전용 fault-injection 설정값은 프로덕션 경로를 오염시키므로 넣지 않는다 |
| 2 | G2(노드 재부팅) 환경 | multipass VM 2대 전제. 물리 2노드에서는 skip |
| 3 | C5 규모 | 10세션×2커널로 시작해 통과하면 50×4로 올린다 |

## 범위에서 뺀 것 (Tier 1 아님)

- 소크/장기 안정성 → Tier 5
- 성능 기준선(iperf3, 생성 지연 p99) → Tier 6
- 스케일 경계(VNI 고갈, 블록 고갈) → Tier 6
- `bailo{n}` 이름공간 충돌(비기본 `local-network-block-size`) → Tier 3, 별도

### 리뷰에서 이월한 것

Tier 1을 끝낸 뒤 재검토한다. 전부 "가치는 있으나 지금 순위가 아니다"에 해당한다.

| 항목 | 이월 사유 |
|---|---|
| vfolder 마운트 세션 teardown | 현재 전 시나리오가 마운트 없는 세션이라 갭은 맞다. 다만 `MountCollector`가 이미 검출 가능하므로, 다른 시나리오에 vfolder를 붙이는 것만으로 대부분 덮인다 |
| 이미지 pull 실패 (사설/자체서명 레지스트리) | B그룹이 pull 이후 단계를 덮는다. pull 경로는 `410b5bec3`에서 라이브 검증된 이력이 있다 |
| GPU 디바이스 반환 (`alloc_map`) | 이 호스트에 GPU가 있는지부터 미확인. BUG5(P9)와 함께 다루는 편이 낫다 |
| 이미지 commit 후 스냅샷·content 누수 | `9478a2895`에서 레이어 공유·GC 생존을 라이브 검증한 이력이 있다 |

### 대상이 없어서 뺀 것

- **HOST 네트워크 세션** — containerd 백엔드에 존재하지 않는다(P그룹 절의 주석 참조)
- **오버레이 블랙홀 감지** (구 G3) — 감지 메커니즘 자체가 없어 검증할 대상이 없다. 4789 차단은
  G5의 음성 대조군으로만 쓴다
