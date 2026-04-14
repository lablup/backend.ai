# Backend.AI K8s 마이그레이션 — 진행 현황 & TODO

| Field | Value |
|---|---|
| **Document ID** | TR-2026-004-TODO |
| **Last Updated** | 2026-04-14 |
| **Branch** | `docs/dood` |
| **Related** | `simple_plan.md`, `k8s-control-plane-dood-agent-architecture.md` |

---

## 1. 완료된 작업

### 1.1 Control Plane on K8s (Helm: `deploy/helm/backend-ai-manager/`)
- [x] Manager Deployment / Service / ConfigMap (`manager.toml` 렌더링)
- [x] Docker 이미지 빌드 (`docker/manager/Dockerfile`)
- [x] 의존 서브차트 구성
  - [x] `postgresql-ha` (Patroni, 3 replica + pgpool)
  - [x] `redis` (replication + Sentinel, 3 replica, quorum=2)
  - [x] `etcd` (3 replica, auth 비활성)
- [x] Helm Hook Jobs
  - [x] `job-schema-migrate.yaml` — `backend.ai mgr schema oneshot`
  - [x] `job-etcd-seed.yaml` — 글로벌 config put-json
  - [x] `job-fixture-populate.yaml` — 기본 domain/group/scaling-group/keypair 시드
- [x] Bootstrap fixture (`files/bootstrap-fixture.json`, `files/resource-slot-types.json`)
- [x] 기본 Secret 템플릿 (JWT, DB, Redis, etcd)

### 1.2 Agent Pod 실행 (Helm: `deploy/helm/backend-ai-agent/`)
- [x] DaemonSet + Docker 이미지 (`docker/agent/Dockerfile`)
- [x] DooD: `/var/run/docker.sock` hostPath 마운트
- [x] `hostNetwork: true`, `hostPID: true`, `privileged: true` 설정
- [x] hostPath 마운트: `/var/lib/backend.ai`, scratch, ipc, krunner stage
- [x] `agent.toml` ConfigMap (etcd 좌표, RPC/agent-sock 포트, reserved 리소스)
- [x] krunner 페이로드 공유 (agent Pod과 호스트 dockerd가 동일 경로로 bind-mount 소스를 보도록 구성)

---

## 2. 발견된 이슈

### 2.1 Critical — 배포 전 반드시 해결

| # | 이슈 | 영향 | 조치 |
|---|---|---|---|
| I-1 | **Manager 노드 고정 미구현** — Manager가 Docker Swarm Manager 역할을 해야 하므로 특정 노드에 pin 필요. 현재 `values.yaml`의 `manager.nodeSelector: {}` 비어 있음 | 재스케줄링 시 Swarm 멤버십 깨짐, 오버레이 네트워크 생성 실패 | `simple_plan.md §4.2` 가이드 반영: `nodeSelector` + taint + `podAntiAffinity` (HA 시 홀수 매니저) |
| I-2 | **`manager.dockerGid: 999` 하드코딩** — 노드별 docker 그룹 GID가 다를 수 있음 (Debian/Ubuntu 999, RHEL 계열 상이) | 노드 섞이면 `docker.sock` 접근 거부 | DaemonSet init-container에서 GID 감지 후 주입, 또는 노드별 values override |
| I-3 | **`CHANGE-ME-*` 기본 시크릿 노출** — values.yaml에 평문 기본값 | 설치 후 크리덴셜 누출 | External Secret / sealed-secret / 필수 `--set-string` 강제 (helm `required`) |
| I-4 | **etcd auth 비활성** (`etcd.auth.rbac.create: false`) | 클러스터 내 누구나 etcd 읽기/쓰기 가능 | RBAC 활성화 + Manager/Agent용 별도 계정 발급 |
| I-18 | **Bitnami 차트 의존성 제거** — 현재 `Chart.lock`의 `postgresql-ha 15.3.17`, `redis 20.13.4`, `etcd 10.7.3` 모두 `charts.bitnami.com/bitnami`. 2025-08-28부로 Bitnami 이미지 `docker.io/bitnamilegacy/*` 이동 + 보안 패치는 유료 구독(Bitnami Secure Images)으로만 제공 | 프로덕션 배포 시 CVE 패치 경로 없음 | **전 컴포넌트 OSS로 전환**: PostgreSQL → CloudNativePG, Redis → Valkey (또는 ot-redis-operator), etcd → 자체 StatefulSet (`quay.io/coreos/etcd:v3.5.x`). `simple_plan.md §4.6/4.7/4.7.1` 참조 |

### 2.2 Functional — 기능 검증 미완료

| # | 이슈 | 비고 |
|---|---|---|
| I-5 | **Fractional GPU / CUDA hook** DooD 경로에서 end-to-end 검증 안 됨 | 커널 컨테이너가 호스트 dockerd로 생성되므로 동작할 것으로 예상되나 실제 smoke test 필요 |
| I-6 | **Multi-node 세션 (Swarm overlay × K8s CNI 공존) 미검증** — 최우선 기능 검증 대상 | 아래 §2.5 참조 |
| I-7 | **AppProxy / Web Server 차트 부재** | 현재 Manager + Agent만 차트화. AppProxy Coordinator/Worker, Web Server 차트 추가 필요 |
| I-8 | **Storage Proxy / vfolder NFS 마운트 미구현** | Agent 차트에 vfolder hostPath 마운트 항목 없음. `simple_plan.md §4.5` (호스트 pre-mount) 방식 반영 필요 |
| I-9 | **Accelerator 플러그인 (CUDA / ROCm / TPU)** 이미지 포함 여부 미검증 | `docker/agent/Dockerfile`에 plugin wheel 설치 경로 점검 |

### 2.3 Operational — 운영/관측

| # | 이슈 | 비고 |
|---|---|---|
| I-10 | **레지스트리 크리덴셜 동기화 Hook 미구현** | K8s Secret ↔ etcd `config/docker/registry/...` 복사 post-install Job 필요 (`simple_plan.md §4.11`) |
| I-11 | **Init-container 헬스체크 없음** | `pg_isready`, `etcdctl endpoint health`, `redis-cli ping` 추가로 race condition 제거 |
| I-12 | **Liveness/Readiness probe 미정의** | Manager/Agent Pod에 probe 추가 |
| I-13 | **Priority class 미지정** | Agent eviction 방지 위해 `backendai-agent-critical` 필요 |
| I-14 | **로그/메트릭 수집 경로 미정** | 커널 컨테이너는 K8s 외부 dockerd 소유 → Prometheus/Loki 통합 전략 필요 |
| I-15 | **DB 마이그레이션 실패 시 롤백 전략** | 현재 Job 단발 실행. pre-upgrade hook + `helm rollback` 시나리오 검증 필요 |

### 2.4 Documentation

| # | 이슈 | 비고 |
|---|---|---|
| I-16 | 노드 prerequisite 문서 (Docker, NVIDIA driver, NFS, Swarm init/join, taint/label) 부재 | `simple_plan.md §6.1` 기반으로 runbook 작성 |
| I-17 | 업그레이드/롤백 가이드 부재 | |

---

## 2.5 I-6 상세 — Multi-node smoke test (CNI 공존 검증)

**범위 (GPU/vfolder/accelerator 제외)**: K8s CNI가 이미 구성된 2노드 위에서 Docker Swarm overlay로 CPU 멀티커널 세션이 동작하는가.

### 핵심 리스크 — CNI별 VXLAN 포트 충돌 매트릭스

Docker Swarm overlay 기본 포트는 **UDP 4789**. CNI 종류에 따라 충돌 여부가 갈림:

| CNI | 기본 캡슐화 | 기본 포트 | Swarm 4789 충돌 |
|---|---|---|---|
| Cilium (VXLAN) | VXLAN | UDP 8472 | ❌ |
| Cilium (Geneve / native) | Geneve / 없음 | 6081 / — | ❌ |
| **Flannel (vxlan)** | VXLAN | **UDP 4789** | **⚠️ 충돌** |
| **Calico (VXLAN mode)** | VXLAN | **UDP 4789** | **⚠️ 충돌** |
| Calico (IPIP / BGP) | IPIP / 없음 | — | ❌ |
| Weave | VXLAN (fastdp) | UDP 6784 | ❌ |

**충돌 시 증상**: `docker swarm init`은 성공하지만 overlay 컨테이너 간 통신만 조용히 실패 (CNI가 먼저 4789 점유, Swarm 패킷 drop). `tcpdump -i any udp port 4789`에서 Swarm 트래픽 0.

**정책**: 현재 CNI가 무엇이든 항상 `--data-path-port 7789`로 분리 init. 향후 CNI 교체/Cilium 옵션 변경/Multus+macvlan 추가 시 무성무취 장애 방지.

**사전 확인** (운영팀이 VXLAN 포트를 변경했을 가능성):
```bash
kubectl get felixconfiguration default -o yaml | grep -i vxlan       # Calico
kubectl -n kube-flannel get cm kube-flannel-cfg -o yaml | grep -i port # Flannel
```

### 전제 조건
- [ ] 2노드 K8s 클러스터, CNI 정상 동작 (`kubectl get nodes` Ready)
- [ ] 각 노드에 Docker CE 설치 완료
- [ ] I-1 (Manager pin), I-2 (dockerGid) 선결

### 필수 설정: Swarm을 비충돌 포트로 init
```bash
# Swarm leader 노드에서 (= Manager Pod이 pin될 노드)
sudo docker swarm init \
  --advertise-addr <NODE_A_IP> \
  --data-path-port 7789 \
  --default-addr-pool 172.30.0.0/16 \
  --default-addr-pool-mask-length 24

# worker 노드 join
sudo docker swarm join --token <worker-token> <NODE_A_IP>:2377

# 방화벽: 2377/tcp, 7946 (tcp+udp), 7789/udp
```
- `--data-path-port 7789`: CNI가 쓰는 4789 회피
- `--default-addr-pool`: CNI podSubnet과 겹치지 않도록

### 검증 단계
1. [ ] **Phase 0** — 충돌 사전 점검: `ss -ulnp | grep 4789`, `ip -d link show | grep vxlan`, CNI podSubnet vs docker 기본 풀 비교
2. [ ] **Phase 1** — Swarm init/join + 방화벽 (위 스크립트)
3. [ ] **Phase 2** — Helm 설치 (GPU 비활성 values, Manager pin 적용)
4. [ ] **Phase 3** — Sanity: Manager Pod에서 `aiodocker.Docker().system.info()['Swarm']['LocalNodeState'] == "active"`, `./bai admin agent list`에 ALIVE 2개
5. [ ] **Phase 4** — 세션 생성:
   ```bash
   ./bai session create <cpu-image> \
     --cluster-size 2 --cluster-mode multi-node \
     --resources cpu=1,mem=1g --name mn-test
   ```
6. [ ] **Phase 5 성공 조건 (3가지 모두 충족)**
   - (a) 양 노드에서 `docker network ls | grep bai-multinode` 동일 네트워크 확인
   - (b) `main1`은 node-a, `sub1`은 node-b에 분산 (`docker ps` 확인)
   - (c) `./bai session exec mn-test main1 -- ping -c 3 sub1` 성공 + alias DNS resolve + TCP 포트 왕복
7. [ ] **Phase 6** — 세션 destroy 후 overlay 네트워크 양 노드에서 cleanup 확인

### 실패 시 진단
| 증상 | 점검 |
|---|---|
| overlay 생성되나 ping 실패 | 양 노드 `tcpdump -i any udp port 7789`. MTU 불일치 시 `/config/plugins/network/overlay/mtu` = CNI MTU − 50 (overlay.py:56) |
| Swarm init 실패 | 4789 점유 중 — `--data-path-port` 재확인 |
| 한 노드에만 뜸 | `--cluster-mode multi-node` 누락 또는 scaling group 바인딩 |
| `swarm not active` | Manager Pod이 leader 노드에 pin 안 됨 (I-1) |
| `permission denied /var/run/docker.sock` | I-2 dockerGid 불일치 |

### 관련 코드
- Manager overlay 생성: `src/ai/backend/manager/network/overlay.py:24-97`
- Scheduler launcher 호출: `src/ai/backend/manager/sokovan/scheduler/launcher/launcher.py:481-520`
- Agent overlay join: `src/ai/backend/agent/docker/intrinsic.py:667-689`
- etcd 설정: `/config/network/inter-container/default-driver` (= `"overlay"`)

---

## 3. 다음 스프린트 우선순위

1. **I-18** Bitnami → OSS 차트 전환 (CloudNativePG / Valkey / 자체 etcd) ← **blocking, 가장 먼저**
2. **I-1** Manager 노드 pinning + Swarm manager 사전 조인 절차 문서화 ← **blocking**
3. **I-2** `dockerGid` 자동 감지
4. **I-6** Multi-node 세션 smoke test — **CNI × Swarm 공존 검증이 최우선 기능 관문** (GPU/vfolder 제외, §2.5 체크리스트)
4. **I-7** AppProxy Coordinator/Worker 차트 작성
5. **I-8** vfolder NFS 마운트 옵션 Agent 차트에 추가
6. **I-10** 레지스트리 크리덴셜 sync Job
7. **I-3, I-4** 프로덕션 시크릿/인증 강화
8. (I-6 통과 이후) **I-5, I-9** GPU / accelerator 검증

---

## 4. Out of Scope (Plan 1 미포함, Plan 2+ 이관)

- containerd 기반 DooD 전환
- VM 격리 (Kata / KubeVirt) — `support_vm_kata.md` 참조
- CNI 직접 호출 실험 (EXP-1/2/3)
- Service mesh, cert-manager, 멀티 리전
