# VXLAN 오버레이 클러스터 네트워크

## 관련 이슈

- BEP-1057 (Agent Re-architecture)
- BEP-1061 (Agent Kernel Lifecycle Structuring)

## 1. 동기

멀티 node 멀티 커널 세션은 커널 전체에 걸친 L2 domain 하나가 필요하다. 지금 그 domain 은 Docker
Swarm 오버레이 네트워크이고, 이 기능을 container runtime 하나에 묶는다. containerd, enroot,
apptainer 를 실행하는 에이전트는 세션의 네트워크에 합류할 방법이 없고, Docker Swarm 의 IPAM 과 VNI
할당은 Manager 가 제어하지 않는 daemon 내부에 있다.

이 제안은 멀티 커널 세션에 Backend.AI 가 직접 만드는 VXLAN 오버레이를 제공하므로 클러스터 네트워크를
runtime 밖으로 옮긴다. Manager 가 세션의 주소 공간과 터널 식별자를 할당한다. 각 에이전트는 runtime
중립적인 seam 이 고르는 backend 가 이끄는 CNI plugin chain 을 통해 자기 node 의 데이터 플레인을
설정한다. runtime 의 역할은 container 의 네트워크 네임스페이스를 전달하는 것뿐이다.

## 2. 설계

### 2.1 계층

| 계층 | 소유자 | 책임 |
|-------|-------|----------------|
| 컨트롤 플레인 | Manager | subnet, VNI, endpoint 별 IP, 암호화 키, 멤버십 |
| 에이전트 plugin | 에이전트 | node 데이터 플레인: 장치, FDB/ARP, 방화벽, XFRM |
| Backend | 에이전트 | L2 domain 을 실현하는 방식 (`vxlan`, `bridge`) |
| Runtime seam | 에이전트 | PID 로 찾는 container 의 netns |

초기 구현에서 지원하는 runtime 은 Docker 하나다. container locator 를 제공하고 클러스터 네트워크
capability 를 발행하는 agent discovery 도 Docker 뿐이다. containerd, enroot, singularity 는 각
discovery 가 두 계약을 구현할 때까지 계획 상태로 남는다. 최신이고 일치하는 capability record 가 없는
member 에이전트는 CNI 클러스터 네트워크 세션을 거부당한다.

에이전트는 member record 를 발행해 세션에 합류하고, 자기 teardown 이 끝난 뒤에야 그 record 를
제거한다. Manager 는 할당을 재사용하기 전에 이 record 를 읽는다.

### 2.2 컨트롤 플레인

할당 상태는 etcd 의 `network/ipam/*` 와 `network/session/{id}/*` 아래에 있고,
compare-and-swap 으로 claim 한다.

| 키 | 담는 것 |
|-----|-------|
| `network/ipam/allocated/{block}` | pool 의 unit block 하나를 소유한 세션 |
| `network/ipam/vni/{vni}` | VNI 하나를 소유한 세션 |
| `network/session/{id}/meta` | generation, subnet, VNI, backend, MTU, VXLAN port, key, key id |
| `network/session/{id}/ipam/{ip}` | 오버레이 주소를 가진 container |
| `network/session/{id}/endpoints/{container}` | ip, mac, agent, cluster hostname |
| `network/session/{id}/members/{agent}` | 에이전트의 VTEP 과 teardown 확인 |
| `network/agent/{id}/caps` | node 의 데이터 플레인이 할 수 있는 것 |

`create_network` 는 세션 id 에 대해 멱등이고, 재사용된 식별자를 fence 하려고 generation token 을
사용한다. claim 과 발행은 compare-and-swap 을 사용한다. 재시도한 시작은 기존 할당으로 수렴하고,
정리는 모든 member 가 teardown 을 확인한 뒤에야 할당을 해제한다.

Manager 는 lease 를 가진 leader lock 아래에서 pagination 된 etcd scan 을 조정한다. 조정은 상태를
한정된 크기로 유지하고, 빠진 claim 과 오래된 부분 생성 기록을 수리하며, 읽을 수 없는 record 는 절대
삭제하지 않는다. scheduler requeue 와 network rollback 상태 전이는 하나의 database 트랜잭션으로
commit 한다.

node 마다 두는 host-local IPAM 이 아니라 중앙 IPAM 이 node 에 걸쳐 늘어난 subnet 에서 주소가 겹치지
않게 보장한다. endpoints 테이블은 각 에이전트가 FDB 와 ARP 를 설정하는 입력이기도 하다.

### 2.3 에이전트 plugin

plugin 은 세션에서 node 쪽 절반을 노출한다.

| verb | 계약 |
|------|----------|
| `setup_session_network` | node 가 세션을 운반할 준비를 갖추게 한다 |
| `attach` | container 의 netns 를 세션의 L2 에 올린다 |
| `detach` | host veth, host-local 주소, MASQ 규칙을 해제한다 |
| `add_peer` / `del_peer` | remote endpoint 하나를 설정한다. 둘 다 멱등 |
| `teardown_session_network` | node 에 이 세션의 흔적을 남기지 않는다 |

node 의 권한 있는 동작은 별도 `privnet` daemon 에 위임할 수 있으므로 에이전트 자체에는
`CAP_NET_ADMIN` 이 필요 없다. 선택 사항이다. `network-privnet-socket` 이 이를 선택하며, 설정하지
않으면 에이전트가 프로세스 안에서 작업을 수행한다. 각 에이전트는 설정된 daemon socket 하나를
소유한다. 한 host 의 두 에이전트가 서로 충돌하는 세션 상태를 설정하는 것은 etcd claim 이 여전히
차단한다.

#### 2.3.1 node 당 daemon 하나 (계획)

지금은 에이전트 여럿을 실행하는 node 가 에이전트마다 daemon 을 하나씩 실행한다. 목표는 node 당
daemon 하나가 그 위의 모든 에이전트를 맡는 구성이다. daemon 은 권한을 모으려고 존재하는데,
daemon N 개는 `CAP_NET_ADMIN` N 벌, journal N 개, socket N 개다. node 전체가 공유하는 claim 저장소
셋(VNI registry, ESP pair journal, LOCAL subnet)은 지금 권한이 에이전트마다 나뉘어 있기 때문에만
존재한다.

공유하면 안 되는 것은 식별자다. node 전체 claim 은 모두 소유자를 가지며, 에이전트 N 개를 맡는
daemon 은 각 claim 에 자기 이름이 아니라 요청한 에이전트를 표시해야 한다. 한 runtime 의 container 를
다른 runtime 의 목록으로 판단해 정리하면 실행 중인 커널이 공개한 port 를 가져간다.

| 관심사 | 계약 |
|---|---|
| 호출자 식별 | 에이전트마다 socket 하나를 두고 daemon 설정에서 에이전트 id 에 묶는다. 에이전트를 이름으로 지정하는 요청 field 는 받지 않는다. 그러면 어떤 호출자든 다른 에이전트의 규칙을 claim 할 수 있다. |
| 경계 강도 | 에이전트마다 uid 를 다르게 두면 그 묶음을 kernel 이 강제한다. uid 를 공유하는 에이전트는 kernel 에게 하나의 principal 이고 서로의 socket 에 그대로 접근할 수 있으므로, 이 묶음은 무결성 경계이지 보안 경계가 아니다. daemon 은 어느 쪽인지 log 로 남긴다. |
| 소유자 표시 | daemon 자신의 에이전트 id 를 사용하는 모든 곳이 호출자의 것으로 바뀐다. VNI claim, ESP pair claim, port-forward tag, `owner_agent_id` 비교 |
| Container 생존 | 에이전트마다 `ContainerLocator` 하나. "이 container 가 아직 있는가"는 그 에이전트 자신의 runtime 만 답할 수 있다. |
| 에이전트별 상태 | 세션, journal, LOCAL subnet allocator 는 daemon 단위가 아니라 에이전트 단위로 둔다. |
| LOCAL block | 에이전트별로 유지한다. 같은 node 에 있는 에이전트 둘에 걸친 세션은 지금 daemon 둘이 주는 것과 똑같이 에이전트마다 block, `bailo` bridge, subnet 을 하나씩 가진다. |
| Journal 배치 | `<state_dir>/<agent_id>/...`. 이미 있던 root 는 그것을 기록한 단일 에이전트에 귀속된다. 자기 record 를 찾지 못하는 daemon 은 아무것도 복구하지 않는다. |

변하지 않는 것: 에이전트는 여전히 네트워크 권한을 가지지 않고, node 전체 claim 저장소는 지금의
on-disk 모양과 소유자 tag 를 유지한다. 소유자가 호출자에게서 올 뿐이다.

### 2.4 VXLAN backend

멀티 node 데이터 플레인이다. 세션마다 오버레이 하나를 두고, 모든 member node 가 같은 세션 record
로부터 만들어 내며, 네트워크 트래픽에서 배우는 것은 없다.

| 요소 | 계약 |
|---------|----------|
| 식별자 | 세션마다 VNI 하나를 Manager 가 `4096..16777215` 에서 할당한다. UDP port 4789 (운영자가 옮길 수 있다) |
| Node 장치 | `baivx<vni>` (VXLAN, node 의 uplink 위) 를 `baibr<vni>` 에 slave 로 두고, container 는 그 bridge 에 veth 하나를 받아 안에서 `baimulti0` 로 보인다 |
| 주소 | 중앙 IPAM. Manager 가 `10.128.0.0/12` 에서 세션의 block 을 잘라 container 가 시작하기 전에 모든 endpoint 에 IP 를 할당한다. DHCP 없음, host-local IPAM 없음 |
| Peer | FDB 와 ARP 는 세션의 endpoints 테이블에서 remote endpoint 별로 멱등하게 설정한다. multicast 없음, flood-and-learn 없음 |
| Peer 교환 | etcd endpoints 테이블이 기록이다. node 는 UDP(`7947`, HMAC, 전체 상태)로도 서로에게 endpoint 를 알리므로 peer 가 etcd 를 다시 읽기 전에 수렴한다. field 를 이해하는 node 는 그 field 에 따라 동작하고, 이해하지 못하는 node 는 무시한다. version gate 는 없다 |
| MTU | Manager 가 오버레이 MTU 를 정한다. node 는 자기 uplink 가 실제로 나르는 크기를 재고 둘이 다르면 세션을 거부한다. 가득 찬 frame 이 사라지게 두지 않는다 |
| 단일 node 세션 | VXLAN 을 건드리지 않는다. node-local bridge backend 가 node 자체 pool(기본 `172.30.0.0/16`, 세션마다 /26)에서 block 을 자른다 |

node 는 `setup_session_network` 부터 자기 teardown 확인이 도착할 때까지 세션의 member 다. Manager
는 모든 member 가 그것을 마친 뒤에야 VNI 나 block 을 재사용한다.

#### 2.4.1 암호화

| 요소 | 계약 |
|---------|----------|
| 전송 | transport mode 의 ESP, `rfc4106(gcm(aes))`, ESN, replay window. profile 이름 `esp-aesgcm-esn-v1` |
| 범위 | 클러스터 전체 키. ESP 정책은 바깥 packet 으로 고르며 그 packet 에는 세션 식별자가 없다 |
| Keyring | slot 셋을 두어 rotation 이 겹칠 수 있다. 이전 키는 복호화하고 새 키는 암호화한다 |
| 선택 | member VTEP 사이의 VXLAN 트래픽만 표시해 암호화한다. 세션이 암호화되면 평문 경로는 통과시키지 않고 버린다 |
| 정책 | 세션 단위 `required` 는 profile 이 없는 member 를 거부한다. `prefer` 는 그 세션을 평문으로 실행하고 그 사실을 알린다 |
| Rotation | `rotate-overlay-key --confirm-drained`. 암호화된 세션이 하나라도 있으면 거부하므로 어느 세션도 이전 키를 발행하지 않는다 |

#### 2.4.2 데이터 플레인을 실제와 맞게 유지

위의 모든 것은 host 의 무엇이든 흔들 수 있는 kernel 상태에 있다. 3초마다 실행되는 watchdog 이 node 가
가져야 할 것과 실제 가진 것을 비교하고, 장치, bridge 멤버십, 방화벽 chain 과 그 위치, ESP 상태를
다시 적용한다. node 가 소유하지만 세션이 사라진 방화벽 규칙은 node 자신의 장치에서만 되찾는다.
재시작한 에이전트는 아직 실행 중인 container 와 journal 로 자기 관점을 다시 만들고, 찾은 모든
세션을 다시 수렴시킨 뒤에 새 세션을 받는다.

#### 2.4.3 준비 상태

에이전트는 자기가 서비스할 수 있는 backend, 보유한 암호화 profile, VTEP, boot id 를
`network/agent/{id}/caps` 아래에 발행하고 1분마다 갱신한다. RPC transport 가 응답한 뒤에야
발행하고, 멈추기 전에 철회하며, 권한 있는 helper 에 접근할 수 없을 때는 에이전트 heartbeat 를 전혀
보내지 않는다. 장치를 만들 수 없는 node 는 scheduler 의 관점에서 빠져 그 사실을 알리며, 서비스할 수
없는 세션을 받지 않는다.

### 2.5 클러스터 이름 해석

세션마다 node 에 resolver 를 두고 endpoints 테이블에서 `cluster_hostname -> overlay ip` 를
응답하므로, 커널이 공유 `/etc/hosts` 기록 없이 이름으로 peer 에 접근한다. container 의
`/etc/resolv.conf` 는 세션의 gateway 를 첫 번째로 지정한다. 응답의 TTL 은 5초이므로 새 주소로
재시작한 커널은 다음 lookup 에서 찾힌다. resolver 가 소유하지 않은 이름은 upstream 으로 전달한다.

## 3. 호환

Docker Swarm 오버레이 plugin 은 남는다. `network.inter_container.default-driver` 가 둘 중에서 고르고,
운영자는 `forced_backend` 로 backend 를 고정할 수 있다.

| Runtime backend | Docker Swarm `overlay` | BEP-1079 `cni` |
|-----------------|-----------------|----------------|
| Docker | 지원 | 지원 |
| containerd | 미지원 | 계획 |
| enroot / singularity | 미지원 | 계획 |
| Kubernetes | 범위 밖 | 범위 밖 |

Kubernetes 는 범위 밖이다. pod 의 네트워크는 이 에이전트가 아니라 클러스터가 제공한다. pod 를
붙이는 CNI chain 은 그 container 보다 먼저 실행되고 주소는 클러스터 자체 IPAM 에서 온다.
Kubernetes 가 제공하는 네트워크에 맞추는 일은 별도 제안이다.

발행된 runtime 식별자와 boot 식별자가 오래된 capability 광고를 fence 한다. 식별자를 발행하지 않는
이전 에이전트는 Docker Swarm 경로와 호환되지만 CNI 경로에서는 fail closed 한다.

## 4. 운영

- `backend.ai mgr network audit` 는 저장된 값이나 secret 을 반환하지 않고 손상된 record, 고아
  claim, key 불일치를 보고한다.
- `backend.ai mgr network audit --repair` 는 CAS 로 보호된 조정을 한 번 실행한다.
- `backend.ai mgr network quarantine` 는 CAS 로 검증한 고아를 삭제 전에 보존된 격리 key 로
  복사한다. 세션 metadata 는 격리할 수 없다.
- `backend.ai mgr network overlay-key-status` 는 활성 key id 와 lifecycle 시각만 보고한다.
- `backend.ai mgr network rotate-overlay-key --confirm-drained` 는 암호화된 세션이 없고 이전
  Manager 가 중지됐음을 Manager 가 확인한 뒤에만 rotation 한다.

에이전트 배포판에는 `backendai-privnet.service` 가 포함된다. 시작 시 symlink, 외부 socket, socket
이 아닌 경로, 이미 실행 중인 daemon 을 거부하고, 소유한 오래된 socket 만 제거한다.

Prometheus 규칙은 할당 고갈, 유효하지 않은 record, 조정 실패, 멈춘 reconciler 에 알림을 보낸다.
함께 배포하는 Grafana 대시보드는 allocator 와 조정의 건강 상태를 보여준다.

## 5. 릴리스 게이트

운영 환경으로 올리려면 다음을 모두 만족해야 한다.

1. pagination, compare-and-swap 경합, lease, 오래된 generation, scheduler rollback, key rotation,
   audit, repair, 격리를 포함한 단위 테스트와 실제 etcd 테스트가 통과한다.
2. 권한 있는 멀티 node 데이터 플레인 suite 가 Docker 에서 `BAI_REQUIRE_DATAPLANE=1`,
   `BAI_DATAPLANE_PRIVNET_MODE=1`, 모든 node 에서 접근 가능한 privnet socket 과 함께 실행된다.
   inventory, 자격 증명, 배치가 빠진 것은 skip 이 아니라 실패다.
3. suite 는 암호화된 node 간 트래픽, DNS, MTU, 에이전트 재시작 수렴, teardown, 그리고 누출된
   link, 규칙, XFRM 상태, 주소, subnet claim, VNI 가 없음을 검증한다.
4. branch 전체 diff 에 대해 format, lint, type check, test 가 통과한다.

이 문서는 maintainer 가 승인할 때까지 Draft 로 남는다. `Target-Version` 과
`Implemented-Version` 은 `proposals/README.md` 의 상태 전이를 통해서만 효력을 가진다. merge 되지
않은 구현 branch 의 코드가 BEP 를 Implemented 로 만들지 않는다.
