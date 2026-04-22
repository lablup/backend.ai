# Backend.AI K8s 마이그레이션 — 진행 현황 & TODO

| Field | Value |
|---|---|
| **Document ID** | TR-2026-004-TODO |
| **Last Updated** | 2026-04-22 (3차 — §6.9 storage-proxy Pod 배포 결과, I-29~I-31 추가) |
| **Branch** | `docs/dood` |
| **Related** | `simple_plan.md`, `k8s-control-plane-dood-agent-architecture.md` |

---

## 1. 완료된 작업

### 1.1 Control Plane on K8s (Helm: `deploy/helm/backend-ai-manager/`)
- [x] Manager Deployment / Service / ConfigMap (`manager.toml` 렌더링)
- [x] Docker 이미지 빌드 (`docker/manager/Dockerfile`)
- [x] 의존 컴포넌트 (v0.2.0부터 **자체 StatefulSet, replica=1 dev/smoke 구성**, I-18 해결)
  - [x] `postgres` (`postgres:16`, 1 replica)
  - [x] `redis` (`redis:7`, 1 replica, standalone)
  - [x] `etcd` (`quay.io/coreos/etcd:v3.5.15`, 1 replica, auth 비활성)
  - [ ] HA 전환 (CloudNativePG / Valkey / etcd-operator) — Plan 2+
- [x] Helm Hook Jobs
  - [x] `job-schema-migrate.yaml` — `backend.ai mgr schema oneshot`
  - [x] `job-etcd-seed.yaml` — 글로벌 config put-json
  - [x] `job-fixture-populate.yaml` — 기본 domain/group/scaling-group 시드 (keypair/CR은 I-22 참조)
- [x] Bootstrap fixture (`files/bootstrap-fixture.json`, `files/resource-slot-types.json`)
- [x] 기본 Secret 템플릿 (JWT, DB, Redis, etcd)

### 1.2 Agent Pod 실행 (Helm: `deploy/helm/backend-ai-agent/`)
- [x] DaemonSet + Docker 이미지 (`docker/agent/Dockerfile`)
- [x] DooD: `/var/run/docker.sock` hostPath 마운트
- [x] `hostNetwork: true`, `hostPID: true`, `privileged: true` 설정
- [x] hostPath 마운트: `/var/lib/backend.ai`, scratch, ipc, krunner stage
- [x] `agent.toml` ConfigMap (etcd 좌표, RPC/agent-sock 포트, reserved 리소스)
- [x] krunner 페이로드 공유 (agent Pod과 호스트 dockerd가 동일 경로로 bind-mount 소스를 보도록 구성)
- [x] GPU 지원 (v0.2.0부터) — `agent.gpu.enabled`일 때 `runtimeClassName: nvidia` + NVIDIA envs + `/usr/local/cuda` hostPath. CPU/GPU 두 release 분리 (`values-agent-cpu.yaml` / `values-agent-gpu.yaml`). 상세: §5.6

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
| I-8 | **Storage Proxy / vfolder NFS 마운트** (부분 완료) | §6.9: storage-proxy Pod 차트 + L1 NFS + vfolder CRUD/ls/mkdir 왕복까지 검증. **남은 작업**: agent 차트 `/vfroot` hostPath + kernel_config 주입, 실제 TUS 업로드, 세션 mount L2/L3 |
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

### 2.5 Storage-Proxy Pod 배포 중 새로 발견된 이슈 (2026-04-22)

§6.9 참조. 세 건 모두 "storage-proxy Pod가 기동 안 되거나 vfolder CRUD가 거부되는" 현상으로 묶이지만 원인은 서로 독립.

| # | 이슈 | 영향 | 대응 |
|---|---|---|---|
| I-29 | **Bootstrap fixture 가 vfolder 기능을 막고 있음** — `max_vfolder_count=0` (user policy), `allowed_vfolder_hosts: []` (keypair policy는 legacy `local:volume1`만), admin user `main_access_key=null`, etcd `volumes/_types/{user,group}` 미시드 | `./bai vfolder create` 가 4단계 거부 (user-owned not allowed → no main_keypair → create-vfolder not allowed) | `deploy/helm/backend-ai-manager/files/bootstrap-fixture.json` 와 etcd-seed ConfigMap 확장: (1) `user_resource_policies[*].max_vfolder_count` 기본값 상향, (2) `keypair_resource_policies[*].allowed_vfolder_hosts`에 `proxy1:volume1` 추가, (3) users[*].main_access_key 필드 세팅, (4) etcd-seed JSON에 `volumes._types.user=""`, `volumes._types.group=""` 키 추가 |
| I-30 | **Docker 빌드 이미지가 containerd `k8s.io` namespace에 안 보임** | `docker build -t ...:dev` 후 helm install 하면 `ImagePullBackOff` — kubelet은 containerd `k8s.io` ns 조회, docker는 `moby` ns 저장. 과거 manager/agent 이미지도 동일 문제였을 것 | 빌드 script 또는 README에 `docker save | sudo ctr -n k8s.io images import` 스텝 추가. 또는 `nerdctl build` 또는 containerd buildkit 직접 빌드로 전환. **영구 해결**: buildah/kaniko 전환 시 k8s.io ns 직접 저장 가능. 임시로 `Makefile`/`./dev build` 헬퍼 제공 권장 |
| I-31 | **Prometheus multiprocess dir 기본 경로가 상대 경로** (`./run/prometheus/<component>`) | storage-proxy 멀티워커 구조에서 워커 CWD 가 부모와 달라져 `FileNotFoundError: run/prometheus/storage/gauge_livesum_*.db` 로 크래시 | storage-proxy chart에서 `BACKENDAI_PROMETHEUS_DIR=/tmp/backend.ai/prometheus` 환경변수 세팅 + emptyDir mount로 해결 (chart에 반영됨). **상류 대응 후보**: `ai.backend.common.metrics.multiprocess.setup_prometheus_multiprocess_dir` 기본값을 `/tmp/backend.ai/prometheus/<component>` 같은 절대 경로로 변경 또는 명시적 에러 가이드. 같은 구조인 manager/agent는 CWD 가 `/root` / `/workspace` 으로 고정되어 운좋게 동작 중 |

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

1. ~~**I-18** Bitnami → OSS~~ **완료** (§5.1, 단 HA 버전은 Plan 2+)
2. ~~**I-26** cuda_open slot name 오타~~ **완료** (§5.6.3, 커널에 GPU device attach 정상화)
3. ~~**I-28** Agent pod 재시작 후 첫 GPU 세션 hang~~ **완료** (§5.6.5, `containerPortRange`를 NodePort 범위 밖 [40000, 45000]로 이동)
4. **I-8 vfolder 스택** — storage-proxy Pod + vfolder CRUD 왕복 **완료** (§6.9). 남은 것: agent 차트 `/vfroot` hostPath 연결, 세션 mount L2/L3 검증
5. **I-29** bootstrap fixture 수정 (vfolder 허용 프리셋) — 차트 재설치 시 수동 `./bai` 복구 단계 불필요하게 만들기
6. **I-30** containerd `k8s.io` namespace 이미지 전달 자동화 — 빌드 스크립트 또는 nerdctl 전환
7. **I-31** storage-proxy prometheus multiproc 경로 상류 수정 (차트 workaround는 있음)
8. **I-24-FIX** krunner 볼륨 sentinel 체크 추가 (`agent/docker/kernel.py:524`) — 반복 재현 가능 버그
6. **I-22** keypair + container-registry fixture를 차트 hook으로 편입
7. **I-25** Multi-node 세션 스케줄러 분산 확인 (sokovan `cluster_mode` 처리)
8. **I-1** Manager 노드 pinning + Swarm manager 사전 조인 절차 문서화
9. **I-2** `dockerGid` 자동 감지
10. **I-6** Multi-node 세션 smoke test — CNI(Cilium) × Swarm 공존은 **검증됨** (§5.3). GPU/vfolder 포함 확장 테스트
11. **I-7** AppProxy Coordinator/Worker 차트 작성 (vfolder 다음 축)
12. **I-10** 레지스트리 크리덴셜 sync Job
13. **I-27** `gather_container_measures` DockerContainer API 오사용 (§5.6.4) — stats만 영향
14. **I-3, I-4** 프로덕션 시크릿/인증 강화
15. **I-5 후속** Fractional GPU (cuda.shares) + CUDA hook 주입 검증 (base CUDA path는 §5.6.6에서 완료)
16. **I-9** 추가 accelerator (ROCm/TPU) 검증

---

## 4. Out of Scope (Plan 1 미포함, Plan 2+ 이관)

- containerd 기반 DooD 전환
- VM 격리 (Kata / KubeVirt) — `support_vm_kata.md` 참조
- CNI 직접 호출 실험 (EXP-1/2/3)
- Service mesh, cert-manager, 멀티 리전

---

## 5. 첫 실제 배포 (2026-04-14 ~ 04-15, 3노드 클러스터)

실 클러스터(`charsyam-gen1` control-plane, `charsyam-nvidia` worker, `ser8` worker + Swarm leader, CNI = Cilium)에서 helm install → agent 등록 → cr.backend.ai 이미지 rescan → 세션 생성 / 멀티노드 세션까지 end-to-end 수행. 진행 중 발견된 실배포-한정 이슈들:

### 5.1 차트 구조 변경 (I-18 해결, `Chart.yaml` v0.1.0 → v0.2.0)

| 이전 | 이후 |
|---|---|
| `postgresql-ha` subchart (3 replica + pgpool) | 단일 StatefulSet `postgres:16` (replica=1) |
| `redis` subchart (replication + Sentinel, 3 replica) | 단일 StatefulSet `redis:7` (standalone) |
| `etcd` subchart (3 replica) | 단일 StatefulSet `quay.io/coreos/etcd:v3.5.15` (replica=1) |
| `manager.toml` redis sentinel 모드 | redis direct `addr` 모드 |

- `deploy/helm/backend-ai-manager/templates/deps.yaml` 신규 — 세 StatefulSet + Service 를 한 파일에 정의 (replica=1 dev/smoke 설정)
- `values.yaml` 내 `postgresql-ha`, `redis`, `etcd` 블록을 `postgres`, `redis`, `etcd` 단순 블록으로 교체
- `Chart.lock` 제거 (subchart 의존성 없음)
- HA 필요 시 각 StatefulSet replica 증가 + 별도 operator(CloudNativePG / Valkey / etcd-operator) 전환은 Plan 2+ 과제로 유지

### 5.2 배포 중 발견된 실문제와 해결

#### I-19. `StorageClass` 없음 — PVC 바인딩 실패
- **증상**: `postgres-0`, `etcd-0`, `redis-0` 전부 `Pending`, describe 시 "pod has unbound immediate PersistentVolumeClaims".
- **원인**: kubeadm 기본 클러스터는 default `StorageClass` 미제공.
- **해결**: `rancher/local-path-provisioner` 설치 후 default 지정. 노드별 로컬 경로에 자동 프로비저닝.
  ```
  kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.31/deploy/local-path-storage.yaml
  kubectl patch storageclass local-path -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
  ```
- **문서화 필요**: `simple_plan.md §6.1` prerequisite에 default StorageClass 요구사항 추가 (CSI NFS / local-path / hostpath 택 1).

#### I-20. Git LFS 포인터 파일 — agent 이미지 내 krunner 바이너리 실체화 안 됨
- **증상**: agent pod 부팅 시 `gzip.BadGzipFile: Not a gzipped file (b've')`. 원인 파일 내용이 `version https://git-lfs.github.com/spec/v1 ...` (132 바이트 LFS 포인터).
- **영향**: `backendai-socket-relay.img.<arch>.tar.gz`, `linuxkit-nsenter.img.<arch>.tar.gz` 로드 실패 → agent 기동 불가.
- **해결**: `git lfs install && git lfs pull` 후 agent 이미지 재빌드.
- **문서화 필요**: `docker/agent/Dockerfile` 상단 주석에 "LFS files required" 명시. CI에서 빌드 시 `git lfs pull` 단계 강제.

#### I-21. Manager pod — `swarm-manager` taint toleration 누락
- **증상**: `ser8` 고정 배치 시 `0/3 nodes ... untolerated taint {backendai.io/dedicated: swarm-manager}`.
- **원인**: ser8 노드에 Backend.AI 전용 taint 존재 (운영 관례), 기본 manager chart tolerations 비어 있음.
- **해결**: values override로 `manager.tolerations: [{key: backendai.io/dedicated, operator: Equal, value: swarm-manager, effect: NoSchedule}]` 추가.
- **차트 반영**: `values.yaml`의 `manager.tolerations` 주석에 해당 taint 예시 추가 권장.

#### I-22. Bootstrap fixture — API keypair 및 container registry 누락
- **증상**: fixture populate Job 완료 후에도 `keypair` 테이블 비어 `./bai login` 불가, `image rescan` 불가 (registry 없음).
- **원인**: `deploy/helm/backend-ai-manager/files/bootstrap-fixture.json`이 domains / users / groups 까지만 시드. 표준 `fixtures/manager/example-keypairs.json`, `example-container-registries-harbor.json`은 별도.
- **현재 우회**: manager pod에서 수동으로 `backend.ai mgr fixture populate /path/to/<fixture>.json` 실행.
- **차트 반영 권장**: `fixture.enabled` 하위에 `keypairs.enabled`, `containerRegistries.enabled` 플래그 추가하고 해당 fixture 파일을 ConfigMap으로 마운트 → populate Job 확장. 또는 post-install 전용 Job 분리.

#### I-23. Keypair resource policy — `max_containers_per_session: 1` 기본값이 multi-node 세션 차단
- **증상**: `--cluster-size 2 --cluster-mode multi-node` 세션 생성 시 `QuotaExceeded: You cannot create session with more than 1 containers`.
- **해결**: `./bai admin keypair-resource-policy update default --max-containers-per-session 4` (또는 origin fixture 수정).
- **차트 반영 권장**: `bootstrap-fixture.json` 또는 전용 fixture에서 기본 정책 `max_containers_per_session`을 더 큰 값으로 세팅 (최소 8~16 권장).

#### I-24. krunner docker volume — 반쯤 초기화된 상태가 영구 방치됨 (★ 루트 원인)
- **증상**: 특정 노드에서 커널 컨테이너 생성 시 `error mounting ... to rootfs at /opt/backend.ai/lib/python3.13/site-packages/ai/backend/kernel ... mkdirat /.../merged/opt/backend.ai/lib: read-only file system`.
- **재현 조건**: 과거 시점에 krunner-env 추출이 한 번 실패해서 `backendai-krunner.v<N>.<arch>.<distro>` 볼륨이 **빈 상태로만** 생성되고 남은 경우.
- **코드 경로**: `src/ai/backend/agent/docker/kernel.py:524-534`
  ```python
  try:
      vol = DockerVolume(docker, volume_name)
      await vol.show()
      # 볼륨 "존재"만 확인 — 내용 검증 없음
  except DockerError as e:
      if e.status == 404:
          do_create = True
  ```
- **왜 RO 에러로 표출되는가**: agent는 `/opt/backend.ai`에 krunner 볼륨을 **READ_ONLY**로 먼저 마운트하고, 그 안쪽 `.../site-packages/ai/backend/{kernel,helpers}` 경로에 bind-mount를 추가 시도. 정상 볼륨이면 해당 mountpoint dir이 이미 존재하지만, 빈 볼륨이면 runc가 mkdir을 시도하다 RO 레이어에서 EROFS.
- **즉시 우회**: 문제 노드에서 `docker volume rm backendai-krunner.v<N>.<arch>.<distro>` 후 agent pod 재시작 → 재추출.
- **항구 수정 제안** (I-24-FIX):
  - `prepare_krunner_env_impl`이 볼륨 존재 확인 시 sentinel 파일(예: `/lib/python<ver>/site-packages/ai/backend/kernel/__init__.py` 또는 별도 `.ready`) 추가 체크
  - 누락 시 `do_create = True`로 강제 재추출

#### I-25. Multi-node 세션 커널 배치 전략 — binpack 기본
- **관찰**: `--cluster-size N`의 총 요청 리소스가 단일 agent 용량 이내면 **binpack으로 한 노드에 몰림**. 초과하면 자동 분산.
- **검증 사례** (3노드 클러스터, ser8 cpu:15 / nvidia cpu:31):
  - `cluster-size=2 -r cpu=1` (총 2 cpu) → 2개 모두 nvidia
  - `cluster-size=2 -r cpu=12` (총 24 cpu) → 2개 모두 nvidia (31 > 24)
  - `cluster-size=3 -r cpu=12` (총 36 cpu, nvidia 단독 초과) → **main1=nvidia, sub1=nvidia, sub2=ser8** ✓
- **Phase 5 성공조건 (§2.5) 재검증**: (a) 양 노드 overlay `6zsx0hpvzop3`/`8ptoukankkbs`/`nc8shf8vcdhl` 공유 ✅ (b) 노드 간 분산 ✅ (c) `main1` → `sub1:2200` SSH 배너 왕복 ✅ — 세 조건 모두 만족.
- **Cross-node overlay 양방향 검증**: `main1`(nvidia) ↔ `sub2`(ser8) + `sub2`(ser8) ↔ `sub1`(nvidia) 모두 DNS resolve + TCP 2200 SSH 배너 왕복 성공. Cilium(VXLAN 8472)와 Swarm(VXLAN 4789) 포트 공존 실증.
- **남은 과제**: anti-affinity 혹은 spread-first 옵션이 UI/API에서 노출되는지 확인 (현재는 리소스 압박으로만 분산 유도 가능).

### 5.3 검증된 엔드-투-엔드 플로우 (2026-04-15 현재)

| 단계 | 결과 |
|---|---|
| `helm install` → manager + deps(postgres/redis/etcd, replica=1) Running | ✅ |
| Hook Jobs (`schema-migrate`, `etcd-seed`, `fixture-populate`) Completed | ✅ |
| Agent DaemonSet 2개 ALIVE (ser8, nvidia) + etcd 등록 (`/sorna/local/nodes/agents/...`) | ✅ |
| `./bai admin agent list` 2 agents ALIVE | ✅ |
| `backend.ai mgr fixture populate example-keypairs.json` (admin API keypair 시드) | ✅ (수동) |
| `backend.ai mgr fixture populate example-container-registries-harbor.json` (cr.backend.ai 등록) | ✅ (수동) |
| `backend.ai mgr image rescan -p stable cr.backend.ai` 수백 이미지 등록 | ✅ |
| Single-node 세션 (`cr.backend.ai/stable/python:3.13-ubuntu24.04-amd64`) → sshd/ttyd/jupyter/jupyterlab/vscode 서비스 기동 | ✅ |
| Multi-node 세션 분산 배치 (`cluster-size=3 -r cpu=12` → nvidia 2 + ser8 1) | ✅ |
| Cross-node overlay DNS + 양방향 TCP (main1 nvidia ↔ sub2 ser8, SSH 2200 배너 왕복) | ✅ |
| CNI(Cilium VXLAN 8472) × Docker Swarm(VXLAN 4789) 공존 | ✅ 포트 충돌 없음 |

### 5.4 차트 외 필수 선행 작업 (runbook 추가 필요)

`simple_plan.md §6.1` prerequisite에 포함 권장:

1. **default StorageClass 보유** (I-19)
2. **Git LFS pull 완료** 후 docker 이미지 빌드 (I-20)
3. **노드별 docker group GID 통일** 또는 `manager.dockerGid` values override (I-2)
4. **manager 고정 노드의 taint/label** 명시적 문서화 (I-21)
5. **Docker Swarm** leader init + worker join (manager 이미지 빌드 전 또는 helm install 전)
6. **CNI VXLAN 포트 사전 확인** — Cilium 기본(8472)는 OK, Flannel/Calico-VXLAN이면 Swarm `--data-path-port 7789` 필수
7. **keypair + container registry fixture populate** 단계 (I-22)

### 5.5 미검증 / 미완료 항목 (2026-04-15 기준)

현재 Plan 1 범위 안에서 남아있는 것:

#### 기능 미검증
| # | 항목 | 상태 | 비고 |
|---|---|---|---|
| I-5 | Fractional GPU / CUDA hook | 부분 | CUDA device 감지 + 커널 attach + 컨테이너 내부 `nvidia-smi`/`libcuda`/`cudaMalloc` end-to-end 검증(§5.6). fractional(cuda.shares) + CUDA hook 주입은 별도 |
| I-9 | Accelerator plugin (CUDA/ROCm/TPU) 동작 확인 | 부분 | CUDA(cuda_open): end-to-end 검증(§5.6). ROCm/TPU는 하드웨어 부재 |
| I-28 | ~~Agent pod 재시작 후 첫 GPU 세션 hang~~ | **해결** | §5.6.5 — `containerPortRange`가 K8s NodePort와 충돌. [40000,45000]로 이동으로 fix |
| I-6 확장 | GPU 포함 multi-node 세션 | 미검증 | CPU-only multi-node는 §5.3에서 완전 검증. GPU 분산 별도 |
| I-8 | vfolder / storage-proxy 마운트 | 미구현 | Agent 차트에 vfolder hostPath 옵션 없음. `simple_plan.md §4.5` 호스트 pre-mount 방식 반영 필요 |
| I-7 | AppProxy Coordinator / Worker chart | 부재 | Web UI 접근 및 service-port proxy 경로 미구성 |
| Web Server | Web 콘솔 (`ai.backend.web`) chart | 부재 | 현재 REST API 직접 호출로만 동작 |
| Multi-node spread 옵션 | 스케줄러 anti-affinity / spread-first | 미확인 | 현재는 리소스 압박으로만 분산 유도 (I-25) |

#### 운영 / 관측 미구축
| # | 항목 | 상태 |
|---|---|---|
| I-10 | registry 크리덴셜 sync Hook Job | 미구현 |
| I-11 | init-container 헬스체크 (`pg_isready`, `etcdctl endpoint health`, `redis-cli ping`) | 부분 (busybox `nc`만 사용) |
| I-12 | Manager/Agent Liveness·Readiness probe | Manager tcpSocket만, Agent 없음 |
| I-13 | Priority class (`backendai-agent-critical`) | 미지정 |
| I-14 | 커널 컨테이너 로그/메트릭 수집 (Prometheus/Loki 통합) | 미설계 |
| I-15 | DB 마이그레이션 실패 시 rollback 시나리오 검증 | 미검증 |
| I-24-FIX | krunner 빈-볼륨 sentinel 체크 (`agent/docker/kernel.py:524`) | 코드 수정 미반영 (제안만) |
| I-27 | `gather_container_measures` DockerContainer API 오사용 (`cuda_open/plugin.py:285-288`) | 미수정, stats만 영향 |
| I-22 | keypair / container-registry fixture 차트 hook 편입 | 수동 실행 단계 유지 |
| I-3, I-4 | 프로덕션 시크릿 / etcd RBAC | 미강화 |

#### HA / 확장
| 항목 | 상태 |
|---|---|
| postgres / redis / etcd HA (CloudNativePG / Valkey / etcd-operator) | Plan 2+ (현재 전부 replica=1) |
| Manager replica=N + Swarm manager 홀수 | replica=1 고정 |
| DaemonSet gen1 포함 | 제외 (docker 미설치, 의도적) |

#### 문서
| 항목 | 상태 |
|---|---|
| I-16 노드 prerequisite 런북 | 미작성 (§5.4는 초안) |
| I-17 업그레이드 / 롤백 가이드 | 미작성 |

**즉시 다음에 손대기 좋은 3개**: **I-8 vfolder 스택** (§6 계획 참조 — L1 NFS pre-mount → L2 storage-proxy 차트), **I-22** (chart hook 편입으로 설치 자동화 완성), **I-24-FIX** (krunner 빈 볼륨 sentinel — 드물지만 반복 가능한 버그).

---

### 5.6 GPU 노드 검증 (2026-04-21, charsyam-nvidia, RTX 4070 Laptop)

범위: agent가 GPU를 감지하고 Manager → Scheduler → Agent → 커널 컨테이너까지 device가 attach되는 경로. 커널 내부에서 CUDA 애플리케이션이 실제 실행되는 것은 §5.6.5 I-28 때문에 미검증이지만, **같은 이미지 + 동일 runtime으로 수동 `docker run`** 시 `nvidia-smi`와 `libcuda` 로드가 정상임을 확인하여 GPU/runtime 경로 자체는 검증됨.

#### 5.6.1 접근: nvidia runtime 기반 (hostPath 라이브러리 주입 X)

agent pod 자체를 **`runtimeClassName: nvidia`로 실행**. hostPath로 NVIDIA `.so`를 주입하는 변형을 시도하지 않음. 이유:

- 호스트에 NVIDIA driver + nvidia-container-toolkit + `nvidia-container-runtime` 바이너리가 이미 설치돼 있음
- containerd에 `nvidia` runtime plugin이 구성돼 있음 (`/etc/containerd/config.toml` 하위에 `plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia.options.BinaryName = "/usr/bin/nvidia-container-runtime"`)
- 클러스터에 `RuntimeClass/nvidia` (handler=nvidia) 기존 등록됨 (160일 전)

이 조합이면 agent pod에 device + libnvidia-ml.so + libcuda.so 등이 자동 주입됨. pod env로 `NVIDIA_VISIBLE_DEVICES=all` + `NVIDIA_DRIVER_CAPABILITIES=compute,utility` 설정.

**단, libcudart는 자동 주입되지 않음.** nvidia-container-toolkit은 "compute" capability가 있어도 CUDA base 이미지가 아닌 컨테이너에는 CUDA runtime을 주입하지 않는다 (이미지가 `ENV CUDA_VERSION=...` 또는 `LABEL com.nvidia.cuda`를 가진 경우에만 주입). 우리 agent 이미지는 `python:3.13.7-slim` 기반이므로 제외됨.

cuda_open 플러그인은 `_load_library("libcudart.so.{major}")`로 CUDA runtime을 로드하므로 (cuda_open/nvidia.py:591) libcudart가 없으면 `could not load the CUDA runtime library` 경고와 함께 `CUDA acceleration is disabled` 로 빠짐.

**해결**: 호스트의 `/usr/local/cuda`를 hostPath로 read-only 마운트하고 `LD_LIBRARY_PATH`에 `/usr/local/cuda/lib64:/usr/local/cuda/targets/x86_64-linux/lib` 추가. 그러면 `libcudart.so.13`을 로드할 수 있음.

커널 컨테이너 (DooD)의 경우는 cuda_open 플러그인이 docker 생성 옵션에 `HostConfig.Runtime=nvidia`를 넣음 (`plugin.py:400-401`). 호스트 dockerd가 nvidia runtime으로 커널 컨테이너를 기동 → 커널 내부에는 full CUDA(libcudart 포함)가 자동 주입됨.

#### 5.6.2 차트 변경 (backend-ai-agent v0.1.0 → v0.2.0)

`deploy/helm/backend-ai-agent/values.yaml`:
- `agent.gpu` 블록 추가: `enabled` (기본 false), `runtimeClassName` (기본 `nvidia`), `visibleDevices` (기본 `all`), `driverCapabilities` (기본 `compute,utility`), `hostCudaPath` (기본 `/usr/local/cuda`)
- `agent.affinity: {}` 필드 추가 (CPU/GPU 노드 분리용 nodeAffinity 지원)

`deploy/helm/backend-ai-agent/templates/daemonset.yaml`:
- `.Values.agent.gpu.enabled`로 다음을 조건부 렌더링:
  - podSpec `runtimeClassName`
  - 컨테이너 env: `NVIDIA_VISIBLE_DEVICES`, `NVIDIA_DRIVER_CAPABILITIES`, `LD_LIBRARY_PATH`
  - `host-cuda` hostPath volume + `/usr/local/cuda` read-only mount
- `.Values.agent.affinity`를 `with` 블록으로 추가

신규 파일:
- `deploy/helm/values-agent-cpu.yaml`: 기본 agent release 오버라이드. `affinity: nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution`로 `accelerator NotIn [gpu]` 제한.
- `deploy/helm/values-agent-gpu.yaml`: GPU 전용 release. `nodeSelector: accelerator=gpu` + `agent.gpu.enabled: true`.

**두 개의 helm release로 분리하는 이유**: `runtimeClassName: nvidia`는 cluster 차원 리소스지만 각 노드 containerd에 실제 `nvidia` runtime이 등록돼 있어야 pod 기동이 됨. non-GPU 노드(ser8)에 등록돼 있지 않을 가능성이 크므로 하나의 DaemonSet에 `runtimeClassName`을 붙이면 non-GPU 노드에서 pod가 깨짐. 두 release로 mutually exclusive하게 배포:

```bash
helm upgrade --install bai-agent deploy/helm/backend-ai-agent \
  -n backend-ai -f deploy/helm/values-agent-cpu.yaml

helm install bai-agent-gpu deploy/helm/backend-ai-agent \
  -n backend-ai -f deploy/helm/values-agent-gpu.yaml
```

GPU 노드에는 `kubectl label node <name> accelerator=gpu` 선행.

#### 5.6.3 I-26 (FIXED) — cuda_open `get_attached_devices` slot name 오타

- **증상**: agent가 GPU 감지(`detected devices: [CUDADevice(model_name: RTX 4070 Laptop GPU, ...)]`) + `CUDA acceleration is enabled.` + Manager DB에 `cuda.device: "1"` 기록까지 모두 정상. 세션 `cpu=2, mem=4g, cuda.device=1`로 enqueue → `i-charsyam-nvidia`에 할당 → `resource allocations done` 까지 진행. 그러나 커널 부착 단계에서 `attached devices: {'cuda': [], ...}` (빈 배열). 커널 컨테이너에 GPU가 전혀 주입되지 않음.
- **원인**: `src/ai/backend/accelerator/cuda_open/plugin.py:416-417`이 `SlotName("cuda.devices")` (복수형)로 조회:
  ```python
  device_ids: list[DeviceId] = []
  if SlotName("cuda.devices") in device_alloc:
      device_ids.extend(device_alloc[SlotName("cuda.devices")].keys())
  ```
  실제 등록된 slot은 `cuda.device` (단수, `plugin.py:92`):
  ```python
  slot_types: Sequence[tuple[SlotName, SlotTypes]] = (
      (SlotName("cuda.device"), SlotTypes("count")),
  )
  ```
  나머지 plugin 내부 참조(line 188, 349, 446, 450, 455, 460)는 모두 단수 `cuda.device`. 416-417만 복수형 — 2022-07-22 (commit 685c50b017) 이후 줄곧 dead code. device_ids가 항상 비어 `attached_devices`가 빈 배열 반환 → 커널에 GPU device attach 누락.
- **수정**: `cuda.devices` → `cuda.device`.
- **후속 검증**: 재배포 후 `attached devices: {'cuda': [{'device_id': '0', 'model_name': 'NVIDIA GeForce RTX 4070 Laptop GPU', 'data': {'smp': 36, 'mem': 8184725504}}], ...}` 로 정상 부착 확인.

#### 5.6.4 I-27 (FOUND, 미수정) — `gather_container_measures` DockerContainer API 오사용

- `src/ai/backend/accelerator/cuda_open/plugin.py:285-288`이 `container_info = await docker.containers.get(cid)` 반환값을 dict로 간주:
  ```python
  container_info = await docker.containers.get(cid)
  nvidia_device_reqs = [
      x
      for x in container_info.get("HostConfig", {}).get("DeviceRequests", [])
      ...
  ]
  ```
- aiodocker의 `docker.containers.get(cid)`는 `DockerContainer` 래퍼 객체를 반환. `.get()`은 해당 객체에 없어 `AttributeError: 'DockerContainer' object has no attribute 'get'`.
- **영향**: GPU 컨테이너의 `gather_container_measures`가 매 5초 예외로 실패 (stats 수집만 중단). 커널 생성/실행/GPU allocation에는 영향 없음. 로그가 시끄러워짐.
- **수정 방안**: inspect JSON을 명시 호출.
  ```python
  container = await docker.containers.get(cid)
  container_info = await container.show()
  ```
- **commit 027d9e8d7** (`feat(BA-4944): per-container CUDA metric collection #9787`)에서 유입된 것으로 보임.

#### 5.6.5 I-28 (FIXED) — `containerPortRange`가 K8s NodePort 범위와 충돌

**증상**: Agent pod 재시작 후 *첫* GPU 세션은 항상 실패(세션이 `CREATING`→`TERMINATED`), 같은 agent 위 두 번째 세션부터 성공. 9회 재현 테스트 100% 일관.

**범인**: Backend.AI agent 기본 `container.port-range = [30000, 32000]`이 Kubernetes **NodePort 기본 범위 (30000-32767)** 와 완전히 겹침.

호스트 `charsyam-nvidia`에는 `kube-system/gpu-agent` NodePort 서비스가 `:30000`에 노출돼 있어서 kube-proxy가 iptables DNAT rule을 설치해둔 상태:

```
KUBE-EXT-FKJSPAFAUGLF36EM  /* kube-system/gpu-agent */  tcp dpt:30000
```

Agent pod이 hostNetwork=true로 동작하고 port pool이 30000부터 시작하므로 첫 kernel container가 REPL(2000) → host 30000 매핑을 받음. Docker는 `docker-proxy`를 127.0.0.1:30000에 띄우지만, iptables DNAT rule이 먼저 match해서 loopback으로 들어오는 TCP를 gpu-agent service endpoint로 라우팅. 결과:

- Agent의 ZMQ PUSH가 `tcp://127.0.0.1:30000`에 connect → 실제로는 gpu-agent FastAPI (`server: uvicorn`, paths `/gpus`, `/cdi/rebuild`, `/create_pod`)에 도달
- TCP handshake는 성공하지만 ZMQ greeting frame이 HTTP 서버에 의해 거부됨 → `EVENT_HANDSHAKE_FAILED_NO_DETAIL` (errno 32, EPIPE)
- ZMQ는 1초 간격으로 무한 재시도 → 메시지 영원히 전달되지 않음
- Kernel runner(`bai-krunner`)는 정상이지만 `insock.recv_multipart()`에서 데이터를 받지 못해 agent가 타임아웃으로 포기

두 번째 세션부터 성공하는 이유: 첫 실패 세션이 port 30000-30014를 여전히 점유한 상태에서 agent가 30015+ 를 배정 → NodePort 서비스와 안 겹침 → ZMQ handshake 정상.

**증거** (warm `127.0.0.1:30015` vs cold `127.0.0.1:30000`에 ZMQ PUSH monitor 붙여 비교):

```
cold (port 30000):  EVENT_CONNECTED → EVENT_HANDSHAKE_FAILED_NO_DETAIL → EVENT_DISCONNECTED → retry (infinite)
warm (port 30015):  EVENT_CONNECTED → EVENT_HANDSHAKE_SUCCEEDED
```

**Fix**: `deploy/helm/backend-ai-agent/values.yaml`에서 기본값을 `containerPortRange: [40000, 45000]`으로 변경. NodePort 범위(30000-32767) 밖으로 이동.

**검증**: 40000 범위 적용 후 agent pod 재시작 직후 첫 GPU 세션이 **12초 내 RUNNING 진입**, 첫 container의 REPL port가 40000. `nvidia-smi -L` 컨테이너 내부에서 정상 동작.

**Docs를 위한 일반화**: Backend.AI agent를 K8s hostNetwork 모드로 배포할 때 `container.port-range`는 반드시 클러스터의 NodePort range(`kube-apiserver --service-node-port-range`)와 겹치지 않아야 함. 특히 호스트 자체가 K8s 노드라 kube-proxy가 iptables rule을 관리하면 loopback 바인딩도 가로채짐 — K8s에서는 `hostNetwork` Pod이 host netns의 iptables 체인을 모두 통과함.

#### 5.6.6 검증된 end-to-end 단계

| 단계 | 결과 |
|---|---|
| `nvidia` RuntimeClass + containerd nvidia runtime + host toolkit 상태 점검 | ✅ |
| agent pod에 `runtimeClassName: nvidia` + NVIDIA envs + hostPath `/usr/local/cuda` 적용 | ✅ |
| cuda_open GPU 감지 (NVML + libcudart) | ✅ `CUDADevice(..., model_name: NVIDIA GeForce RTX 4070 Laptop GPU, ...)` |
| agent self-register → etcd `/sorna/local/nodes/agents/i-charsyam-nvidia: running` | ✅ |
| Manager DB `agents.available_slots."cuda.device" = "1"` + `schedulable: True` | ✅ |
| 세션 enqueue `{cpu:2, mem:4g, cuda.device:1}` → scheduler가 `i-charsyam-nvidia`에 할당 | ✅ `used.cuda.device: 1.000000` |
| agent `DiscretePropertyAllocMap.allocate()` 성공 | ✅ `resource allocations done` |
| **(I-26 수정 후)** `get_attached_devices()`가 GPU를 반환하고 커널 컨테이너 docker config에 device inject | ✅ attached `device_id: '0'` |
| 커널 컨테이너 생성 (`HostConfig.Runtime=nvidia` + `NVIDIA_VISIBLE_DEVICES=0`) | ✅ 컨테이너 시작됨 |
| 커널 service ready (sshd / ttyd / jupyter / jupyterlab / vscode / tensorboard) | ✅ 2초 내 `service apps initialized` |
| 세션 상태 `RUNNING` 진입 | ✅ |
| 커널 안에서 `nvidia-smi -L` | ✅ `GPU 0: NVIDIA GeForce RTX 4070 Laptop GPU (UUID: GPU-7a825f44-...)` (agent 보고 UUID와 일치) |
| `LD_LIBRARY_PATH=/usr/local/nvidia/lib64`, `NVIDIA_VISIBLE_DEVICES=all`, `NVIDIA_DRIVER_CAPABILITIES=compute,utility` 주입 | ✅ |
| `/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-uvm*`, `/dev/nvidia-modeset` 전부 노출 | ✅ |
| `libcuda.so.1` + `libcudart.so.12` 로드 | ✅ |
| CUDA runtime API: `cudaGetDeviceCount() = 1`, `cudaDeviceGetPCIBusId(0) = "0000:01:00.0"` (agent 보고 hw_location과 일치) | ✅ |
| CUDA compute: `cudaMalloc(1MB)` + `cudaFree` | ✅ rc=0, rc=0 |

#### 5.6.7 추가 runbook 항목 (§5.4 보강 권장)

GPU 노드를 추가할 때:
1. 노드에 NVIDIA driver + nvidia-container-toolkit 설치
2. containerd `config.toml`에 `nvidia` runtime 등록 (`nvidia-ctk runtime configure --runtime=containerd --set-as-default=false`)
3. 클러스터에 `RuntimeClass/nvidia` 존재 확인 (handler=nvidia)
4. 호스트에 `/usr/local/cuda` (CUDA toolkit) 설치 — libcudart 제공용
5. 노드 label: `kubectl label node <name> accelerator=gpu`
6. `helm upgrade --install bai-agent-gpu deploy/helm/backend-ai-agent -n backend-ai -f deploy/helm/values-agent-gpu.yaml`
7. 로그 확인: `kubectl logs ... -c agent | grep "detected devices"` — CUDADevice 배열이 비어있지 않아야 함

---

## 6. 다음 단계 — vfolder / storage-proxy 도입 (2026-04-21 기준 계획)

현재 데모 가능한 최소 기능은 완료 (control plane + agent 등록 + 단일/멀티노드 CPU 세션 + 단일노드 GPU 세션 end-to-end). 사용자 관점으로 제품화하려면 3가지 축이 남음: **vfolder / storage-proxy**, **AppProxy**, **Web Server**. 이 중 가장 손대기 쉬운 vfolder 축부터 진행.

### 6.1 배경 — 이 클러스터에 NFS 인프라가 없음

실 운영 환경은 전용 NFS 서버가 있지만 현재 3노드 lab 클러스터에는 공유 스토리지가 없음. 개발/검증 용도로 **NFS 서버를 Docker 컨테이너로 띄워서** 사용 — 실제 운영에서는 외부 NFS(또는 CephFS/S3)로 교체 가능한 구조로 만듦.

### 6.2 테스트 수준 L1 → L2 → L3 단계별 계획

| 수준 | 목표 | 작업 | 검증 기준 |
|---|---|---|---|
| **L1. 공유 scratch (vfolder API 없음)** | 모든 노드에서 보이는 공유 디렉터리가 커널 컨테이너에 마운트됨 | (1) NFS 서버 Docker 컨테이너 ser8에 배포<br>(2) 각 agent 노드에 `/vfroot` NFS mount (systemd-mount)<br>(3) agent 차트에 optional `hostPath: /vfroot` → 커널 mount 옵션 추가 | 세션 두 개(같은 노드/다른 노드)에서 같은 파일을 읽고 쓸 수 있음 |
| **L2. vfolder API (단일노드)** | `./bai vfolder create/upload/download/mount` end-to-end | (4) `deploy/helm/backend-ai-storage-proxy/` 신규 차트 작성<br>(5) storage-proxy Deployment (1 replica, ser8 pin, hostPath `/vfroot`)<br>(6) Service 2포트: `6021` (manager API), `6022` (client API)<br>(7) manager etcd-seed Job에 volume proxy 등록 추가<br>(8) storage backend (`vfs` driver) 정의 | 세션 create 시 `--mount myfolder:/work` 적용, 업로드한 파일이 컨테이너 내부에서 보임 |
| **L3. vfolder multi-node** | 다른 노드에서도 같은 vfolder 접근 | L2 + 모든 agent 노드가 같은 `/vfroot` NFS pre-mount 이미 완료(L1에서 구현됨) | 다른 노드에 스케줄된 세션에서 동일 vfolder 파일 접근 |

### 6.3 L1 세부 작업

**NFS 서버 컨테이너 (ser8)**
```bash
mkdir -p /srv/bai-shared/vfroot
# Ubuntu 24.04은 nfsd 모듈 기본 제공
docker run -d --name bai-nfs --privileged --restart unless-stopped \
  -v /srv/bai-shared:/srv/bai-shared \
  -e SHARED_DIRECTORY=/srv/bai-shared \
  -p 2049:2049 \
  itsthenetwork/nfs-server-alpine:latest
```

**각 agent 노드에 NFS 마운트**
```bash
# charsyam-nvidia에서
apt-get install -y nfs-common
mkdir -p /vfroot
echo "ser8:/srv/bai-shared/vfroot  /vfroot  nfs4  rw,hard,timeo=600,retrans=2  0 0" >> /etc/fstab
mount /vfroot
# ser8도 동일 (서버와 같은 노드지만 mount 경로는 /vfroot로 통일)
```

**agent 차트 변경** (`deploy/helm/backend-ai-agent/values.yaml` + `templates/daemonset.yaml`)
- `agent.vfolderHostPath` 필드 추가 (기본 disabled, `"/vfroot"` 등)
- 활성화 시 DaemonSet에 `hostPath: /vfroot` volume + container mount 추가
- 세션 create 시 `mounts` 필드에 vfolder spec 전달되면 agent가 자동 bind (기존 `mount_vfolders` 경로 — 하지만 vfolder 메타데이터 없으면 호출 안 됨)

**L1 한계**: Backend.AI의 `mount_vfolders`는 Manager가 kernel_config에 vfolder 목록을 주입해야 작동. Manager는 DB의 vfolder 레코드를 보고 주입. vfolder 레코드를 만들려면 storage-proxy 등록이 필요. 즉 L1만으로는 "세션에 공유 경로가 자동으로 붙는다"가 구현 안 됨.

**L1의 실제 검증**: agent 차트의 hostPath 옵션이 정상 적용되는지, NFS mount가 각 노드에서 유지되는지, 수동으로 `docker run -v /vfroot:/work ...` 해봤을 때 양 노드에서 같은 파일이 보이는지까지. vfolder API를 안 쓰므로 세션 생성 시 mount 적용은 불가능 — L2에서 해결.

### 6.4 L2 세부 작업 — storage-proxy 차트 신규

**차트 구조** (`deploy/helm/backend-ai-storage-proxy/`)
- `Chart.yaml` — appVersion 26.4.0
- `values.yaml` — replica=1, nodeSelector(ser8), hostPath vfroot, etcd 좌표, secret
- `templates/deployment.yaml` — storage-proxy pod
- `templates/service.yaml` — manager API (6021), client API (6022)
- `templates/configmap-storage-proxy-toml.yaml` — `storage-proxy.toml` 렌더링

**storage-proxy.toml 핵심 필드**
```toml
[storage-proxy]
ipc-base-path = "/tmp/backend.ai/ipc"
event-loop = "uvloop"
node-id = "storage-proxy-1"

[api.manager]
service-addr = { host = "0.0.0.0", port = 6021 }
secret = "..."  # manager와 공유

[api.client]
service-addr = { host = "0.0.0.0", port = 6022 }

[[volume]]
name = "default"
backend = "vfs"
path = "/vfroot"

[etcd]
namespace = "local"
addr = { host = "bai-etcd.backend-ai.svc.cluster.local", port = 2379 }
```

**Manager 쪽 etcd 등록** (`backend-ai-manager` 차트의 `etcdSeed` Job 확장)
```
/sorna/local/volumes/_types                        → ["proxy1"]
/sorna/local/volumes/proxies/proxy1/client_api     → http://storage-proxy.ingress/client-api
/sorna/local/volumes/proxies/proxy1/manager_api    → http://bai-storage-proxy:6021
/sorna/local/volumes/proxies/proxy1/secret         → (manager secret)
/sorna/local/volumes/proxies/proxy1/default_host   → proxy1:default
```

**관리자 CLI로 storage host 등록**
```
./bai admin vfs-storage create --name default --proxy proxy1 ...
```

**검증 시나리오**
1. `./bai vfolder create test-folder` → DB + filesystem에 디렉터리 생성
2. `./bai vfolder upload test-folder <file>` → storage-proxy client API로 업로드, `/vfroot/test-folder`에 파일 존재
3. 세션 생성 시 `--mounts test-folder` → 컨테이너 내부 `/home/work/test-folder`에서 파일 보임
4. 세션 종료 후 vfolder 내용 유지
5. `./bai vfolder download test-folder <file>` → storage-proxy client API로 다운로드

### 6.5 L3 세부 작업 — multi-node 확장

L2에서 `/vfroot`를 모든 agent 노드에 pre-mount하는 것만 보장하면 multi-node는 자동 동작. 확인 사항:

- GPU 노드와 CPU 노드 둘 다 `/vfroot` mount 살아있는지
- `./bai session enqueue ... --agent-list i-charsyam-nvidia` / `--agent-list i-ser8` 로 강제 배치 후 같은 vfolder 접근 가능 여부
- 멀티노드 클러스터(`cluster-size=2`)에서 main1 / sub1 모두 vfolder 접근

### 6.6 작업 순서 & 예상 소요

| 순서 | 작업 | 예상 |
|---|---|---|
| 1 | L1.1 NFS Docker 컨테이너 기동, 3노드 중 2개 (ser8 + charsyam-nvidia)에 `/vfroot` mount | 30분 |
| 2 | L1.2 agent 차트에 optional `vfolderHostPath` 추가, 수동 `docker run -v` 검증 | 1시간 |
| 3 | L2.1 storage-proxy 차트 작성 (Deployment / Service / ConfigMap) | 반나절 |
| 4 | L2.2 storage-proxy 이미지 빌드 (`docker/backend.ai-storage-proxy.dockerfile` 재사용) | 1시간 |
| 5 | L2.3 manager etcd-seed Job에 volume proxy 등록 추가 | 1시간 |
| 6 | L2.4 storage host DB 레코드 (fixture or CLI) | 1시간 |
| 7 | L2.5 `./bai vfolder create/upload/download/mount` end-to-end 테스트 | 반나절 (디버깅 포함) |
| 8 | L3 multi-node smoke (existing cluster-size=2 CPU 세션 + vfolder) | 1시간 |

총합 약 **2일** (실제 디버깅 고려하면 3일 여유).

### 6.7 L1 시작 전 체크리스트

- [ ] ser8에 docker 여유 공간 (`df -h /var/lib/docker`) 10GB+ 확인
- [ ] charsyam-nvidia에 `nfs-common` 패키지 설치 가능 확인
- [ ] ser8 방화벽에서 :2049 오픈 (기존 6001/6007 외에)
- [ ] ser8의 nfsd kernel module 로드 가능 (`modprobe nfsd`)
- [ ] agent 차트의 nodeSelector/affinity와 NFS mount가 호환되는지 (현재 CPU release는 NotIn gpu, GPU release는 accelerator=gpu — 둘 다 ser8 + nvidia에서 동작, NFS는 양쪽에 필요)

### 6.8 범위 외 (이번 작업에 포함 안 함)

- **AppProxy 차트** (I-7): 별도 다음 사이클
- **Web Server 차트**: 별도
- **S3 / CephFS 백엔드**: Plan 2+
- **NFS HA** (keepalived, DRBD 등): 운영 배포 시
- **PersistentVolume CSI 통합** (`csi-driver-nfs`): K8s-native 선호 시 대안

### 6.9 L1 + L2 실행 결과 (2026-04-22)

§6.3 L1 + §6.4 L2 작업 실제 수행. **storage-proxy Pod 자체는 정상 기동 + vfolder CRUD/ls/mkdir 왕복까지 검증 완료.** 단, 계획에서 명시하지 않았던 bootstrap fixture 공백과 이미지 전달 경로 문제가 수면 위로 올라와 I-29/I-30/I-31로 새로 적재.

**확정된 구조 (계획 대비 차이)**

| 결정 | 계획 §6.4 | 최종 | 이유 |
|---|---|---|---|
| 네트워크 노출 | Service (clusterIP) + 2포트 | `hostNetwork: true` + ser8 pin, Service 없음 | client API(6021) 가 사용자 머신 + kernel 컨테이너 양쪽에서 reachable 해야 함. ClusterIP는 kernel(DooD Docker bridge)에서 해석 안 되고, NodePort는 번거로움. hostNetwork + host IP 하나로 통일 |
| manager API port | 6021 | 6022 | 계획이 API 두 개를 뒤집어 적어두었음 (실제 `src/ai/backend/storage/config` halfstack.toml 기준 client=6021, manager=6022) |
| etcd 등록 주체 | manager etcdSeed Job | 동일 — 단 seed를 `etcd-seed.json`(config prefix)과 `volumes-seed.json`(volumes prefix) 2개로 분리하고 같은 Job에서 `mgr etcd put-json` 을 두 번 호출 | Backend.AI etcd가 `/sorna/<ns>/{config,volumes,...}/` 로 top-level 네임스페이스를 구분하므로 prefix 하나(`config`)로는 `volumes/`에 못 씀 |
| 볼륨 경로 | `/vfroot` (root of NFS export) | `/vfroot/volume1/` (서브디렉터리) | 향후 추가 볼륨(volume2, ...) 병치를 위해 per-volume subpath 유지 |
| Dockerfile | `docker/backend.ai-storage-proxy.dockerfile` (`pip wheel from dist/`) 재사용 | `docker/storage-proxy/Dockerfile` 신규 (Pants 기반, manager/agent 패턴과 동일) | 신규 Dockerfile이 git-lfs pull 과 pants 빌드를 self-contained 로 수행 — `dist/` 사전 빌드 의존 제거 |

**실제 배포 순서 (이후 재현 runbook)**

1. `itsthenetwork/nfs-server-alpine` 컨테이너 ser8에 `docker run`, `/srv/bai-shared/vfroot` export
2. 3노드(`ser8`, `charsyam-nvidia`, `charsyam-gen1`) `/etc/fstab` 에 `192.168.0.156:/ /vfroot nfs4 rw,hard,timeo=600,retrans=2,_netdev,nofail 0 0` 추가 후 `mount -a`
3. `docker build -f docker/storage-proxy/Dockerfile -t backend.ai-storage-proxy:dev .`
4. **`docker save backend.ai-storage-proxy:dev | sudo ctr -n k8s.io images import -`** ← I-30. 이 스텝이 없으면 ImagePullBackOff
5. `helm install bai-sp deploy/helm/backend-ai-storage-proxy -n backend-ai -f deploy/helm/values-storage-proxy-local.yaml`
6. `helm upgrade bai deploy/helm/backend-ai-manager -n backend-ai -f deploy/helm/values-local.yaml` — post-upgrade etcd-seed Job 이 `/sorna/local/volumes/proxies/proxy1/*` 키 5개 주입
7. `kubectl rollout restart deployment bai-backend-ai-manager` — manager 가 부팅 시에만 volume 설정 읽으므로 재기동 필수
8. **bootstrap 복구 4단계** (I-29 해소 전까지 매번 필요):
   - `./bai admin resource-policy user update default --max-vfolder-count 100`
   - `./bai admin resource-policy keypair update default --json '{"allowed_vfolder_hosts":[{"host":"proxy1:volume1","permissions":["create-vfolder","modify-vfolder","delete-vfolder","mount-in-session","upload-file","download-file","invite-others","set-user-specific-permission"]}]}'`
   - `./bai user update <admin-uuid> '{"main_access_key":"AKIAIOSFODNN7EXAMPLE"}'`
   - `kubectl exec -n backend-ai bai-etcd-0 -- etcdctl put /sorna/local/volumes/_types/user "" ; ... put /sorna/local/volumes/_types/group ""`
9. `./bai vfolder create --name test-folder --host proxy1:volume1`

**검증된 경로 (end-to-end)**

- `./bai vfolder create` → manager → storage-proxy manager API (6022) → `mkdir /vfroot/volume1/<user>/<uuid>/<...>/` → NFS 서버 `/srv/bai-shared/vfroot/volume1/...` 에 실체 생성 ✅
- `./bai vfolder mkdir <id> subdir` → 동일 경로로 전파 ✅
- `kubectl exec storage-proxy-pod -- sh -c 'echo X > /vfroot/.../direct.txt'` → `./bai vfolder ls <id>` 로 조회 ✅ (반대 방향 왕복)

**아직 검증 안 된 것**

- **TUS 업로드 실체 전송**: `./bai vfolder upload` 가 토큰/URL만 발급하고 종료. 실제 바이트 전송은 TUS 클라이언트 필요 — 별도 smoke 필요. mkdir 왕복이 증명되었으니 동일 경로로 동작할 것으로 기대.
- **세션 mount (L2/L3)**: agent 차트에 `/vfroot` hostPath 가 아직 없음. kernel_config 에 mounts 주입되어도 agent 노드에 경로가 없어 bind 실패. **I-8 남은 작업** 으로 유지.
- **multi-node vfolder** (L3): L2 위에 agent 차트 수정만 들어가면 자동. GPU 세션 노드에서 같은 vfolder 파일 접근 확인 필요.
