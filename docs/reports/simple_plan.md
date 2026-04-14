# Backend.AI K8s Migration: Plan 1 (Minimal Effort)

| Field | Value |
|---|---|
| **Document ID** | TR-2026-004 |
| **Date** | 2026-04-08 |
| **Author** | Backend.AI Architecture Team |
| **Status** | Draft |
| **Classification** | Internal Implementation Plan |
| **Related Documents** | `k8s-control-plane-dood-agent-architecture.md`, `support_vm_kata.md` |
| **Scope** | Minimal-effort path to deploy Backend.AI on Kubernetes with the smallest code changes and operational complexity |
| **Estimated Effort** | 2-4 weeks (1-2 engineers) |

---

## Table of Contents

1. [Goal](#1-goal)
2. [Scope and Non-Goals](#2-scope-and-non-goals)
3. [Architecture Summary](#3-architecture-summary)
4. [Selected Choices](#4-selected-choices)
5. [Helm Chart Structure](#5-helm-chart-structure)
6. [Deployment Steps](#6-deployment-steps)
7. [Required Code Changes](#7-required-code-changes)
8. [Explicitly Deferred Features](#8-explicitly-deferred-features)
9. [Effort Estimate](#9-effort-estimate)
10. [Risk Summary](#10-risk-summary)

---

## 1. Goal

Deploy Backend.AI on Kubernetes with the **least possible code changes** and **simplest operational model**, while preserving full GPU feature support (multi-GPU, fractional GPU, all accelerator plugins) and existing Docker Swarm overlay networking.

This plan is the fastest path to a working K8s deployment. It deliberately defers complexity (containerd migration, VM-based isolation, advanced HA, etc.) to later phases.

---

## 2. Scope and Non-Goals

### In Scope

- Control plane (Manager, PostgreSQL, Redis, etcd, AppProxy, Web Server) on Kubernetes via Helm
- Agent as K8s DaemonSet with Docker-out-of-Docker (DooD)
- Kernel containers continue to run via host Docker daemon (no change)
- Existing Docker Swarm overlay networking for multi-node sessions (no change)
- Host-level NVIDIA driver and Container Toolkit installation (manual)
- Single Redis with basic HA via Bitnami Sentinel
- Single PostgreSQL instance (or external managed DB)
- Host pre-mounted NFS for vfolder storage
- Helm-based installation, upgrade, rollback

### Non-Goals (Explicitly Excluded)

- containerd-based DooD (stays with Docker)
- VM-based isolation (Kata Containers, KubeVirt) — see `support_vm_kata.md`
- NFS Mounter DaemonSet (host pre-mount only)
- NVIDIA GPU Operator (host-level install only)
- Multi-region / multi-cluster deployment
- Live migration
- Advanced storage backends (CephFS via CSI, etc.)
- Custom CNI integration for kernel containers
- Service mesh (Istio, Linkerd)
- TLS certificate automation (cert-manager)
- Advanced monitoring beyond basic Prometheus

---

## 3. Architecture Summary

```
┌───────────────── Kubernetes Cluster ──────────────────────────┐
│                                                                │
│  ┌─── Control Plane Namespace (backendai-system) ──────────┐  │
│  │                                                          │  │
│  │  Manager (Deployment, 2 replicas)                        │  │
│  │  PostgreSQL (StatefulSet, single instance)               │  │
│  │  Redis (Bitnami Sentinel, 3 pods)                        │  │
│  │  etcd (StatefulSet, 3 nodes)                             │  │
│  │  AppProxy Coordinator (Deployment, 1 replica)            │  │
│  │  AppProxy Worker (Deployment, 2 replicas)                │  │
│  │  Web Server (Deployment, 2 replicas + Ingress)           │  │
│  │                                                          │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │ ZeroMQ RPC via K8s Service DNS                │
│                 │                                               │
│  ┌──────────────▼─── Agent DaemonSet (GPU node pool) ──────┐  │
│  │                                                          │  │
│  │  Agent Pod (per node)                                    │  │
│  │    ├── hostNetwork: true                                 │  │
│  │    ├── /var/run/docker.sock mounted (DooD)              │  │
│  │    ├── /mnt/vfolder mounted (host pre-mounted NFS)      │  │
│  │    └── Privileged for GPU access                         │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │ Docker API via socket                         │
└─────────────────┼───────────────────────────────────────────────┘
                  │
                  ▼ (host-level operations, outside K8s)
┌─── Host (per agent node) ────────────────────────────────────┐
│                                                               │
│  Pre-installed:                                              │
│    - NVIDIA driver (apt install nvidia-driver-535)          │
│    - NVIDIA Container Toolkit                                │
│    - Docker daemon                                           │
│    - NFS mount at /mnt/vfolder (fstab)                       │
│    - Backend.AI taint: backendai.io/dedicated=agent:NoSchedule │
│                                                               │
│  Docker daemon manages:                                      │
│    - Kernel containers (created by Agent via socket)         │
│    - Docker Swarm overlay network for multi-node sessions    │
│    - Image pulls (auth from etcd)                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. Selected Choices

The following are the minimum-effort selections from the main architecture document. Each choice prioritizes speed of delivery over future flexibility.

### 4.1 Container Runtime: Docker (not containerd)

| Reason | Details |
|---|---|
| Zero code changes | Existing `DockerAgent` + `aiodocker` work as-is |
| Production-proven | Already used in current bare-metal deployments |
| Swarm overlay included | Multi-node session networking works out of the box |
| Familiar tooling | `docker ps`, `docker logs`, `docker exec` for debugging |

**Trade-off accepted**: Two container runtimes on the node (Docker for kernels, containerd for K8s pods). This is acceptable.

### 4.2 Networking: Docker Swarm Overlay (no change)

| Reason | Details |
|---|---|
| Already in production | Same path as bare-metal deployment |
| No new networking code | Manager's overlay network plugin works unchanged |
| No CNI integration risk | Avoids EXP-1/2/3 (CNI direct invocation) entirely |
| No performance regression | Identical to current network performance |

**Trade-off accepted**: Cannot integrate with K8s NetworkPolicy or service mesh for kernel containers.

> **IMPORTANT — Manager node pinning required**: Because the Manager participates in the Docker Swarm as a **Swarm Manager** (to create/manage overlay networks for multi-node sessions), the Manager Pod **must be pinned to a specific node** that has been joined to the Swarm as a manager. Rescheduling the Manager to another node would break Swarm membership and overlay network operations.
>
> Apply via Helm values:
> ```yaml
> manager:
>   nodeSelector:
>     backendai.io/role: swarm-manager
>   tolerations:
>     - key: backendai.io/dedicated
>       operator: Equal
>       value: swarm-manager
>       effect: NoSchedule
> ```
> And label/taint the target node:
> ```bash
> kubectl label node <node> backendai.io/role=swarm-manager
> kubectl taint node <node> backendai.io/dedicated=swarm-manager:NoSchedule
> docker swarm init  # or `docker swarm join --token <manager-token> ...`
> ```
>
> For HA: Swarm requires an odd number of managers (3 or 5). If running multiple Manager replicas, each replica must be pinned to a distinct pre-joined Swarm manager node (use `podAntiAffinity` + per-replica `nodeSelector`).

> **IMPORTANT — Docker group GID portability**: Both the Manager Pod (when it talks to the host Swarm daemon) and the Agent Pod (DooD) mount `/var/run/docker.sock` from the host. The in-container user must belong to the *host's* docker group GID, which is **not** stable across distros (Debian/Ubuntu: `999`, RHEL/Rocky/AlmaLinux: often `995` or site-specific, hardened images: arbitrary).
>
> A single hardcoded value in `values.yaml` (e.g., `manager.dockerGid: 999`) breaks on any node whose docker group differs. Mitigations:
> 1. **Init-container GID detection** (recommended): on Pod start, `stat -c '%g' /var/run/docker.sock` → write to a shared emptyDir, and launch the main container with that value as a supplementary group (requires `runAsNonRoot` + `supplementalGroups` patched at runtime, or entrypoint wrapper that `exec setpriv --groups=$GID ...`).
> 2. **Per-node values override**: enforce a homogeneous distro/GID across the agent pool, documented as a prerequisite.
> 3. **`hostUsers: false` + user namespace remap** (K8s 1.30+): only works when the kernel supports shifted UID/GID mounts — still experimental for hostPath sockets.

> **IMPORTANT — CNI ↔ Swarm VXLAN port conflict**: Docker Swarm overlay defaults to **UDP 4789**, which is the same port used by Flannel (vxlan backend) and Calico (VXLAN mode). Co-locating Swarm with one of these CNIs on the same node causes silent overlay failures: `docker swarm init` succeeds, but cross-node container traffic is dropped because the CNI grabs the socket first.
>
> | CNI | Default encap | Default port | Conflicts with Swarm 4789? |
> |---|---|---|---|
> | Cilium (VXLAN) | VXLAN | UDP 8472 | No |
> | Cilium (Geneve / native routing) | Geneve / none | 6081 / — | No |
> | **Flannel (vxlan)** | VXLAN | **UDP 4789** | **Yes** |
> | **Calico (VXLAN mode)** | VXLAN | **UDP 4789** | **Yes** |
> | Calico (IPIP / BGP) | IPIP / none | — | No |
> | Weave | VXLAN (fastdp) | UDP 6784 | No |
>
> **Policy**: regardless of which CNI is currently deployed, always initialize Swarm with `--data-path-port 7789` so a future CNI swap, Cilium tunnel-port change, or addition of another VXLAN tool (Multus + macvlan-overlay, etc.) cannot silently break multi-node sessions. Verify the operator-modifiable VXLAN port on existing CNI before install:
> ```bash
> kubectl get felixconfiguration default -o yaml | grep -i vxlan   # Calico
> kubectl -n kube-flannel get cm kube-flannel-cfg -o yaml | grep -i port  # Flannel
> ```

### 4.3 GPU Driver: Host-Level Installation (no GPU Operator)

| Reason | Details |
|---|---|
| Simplest setup | `apt install nvidia-driver-535 nvidia-container-toolkit` |
| No K8s coupling | Driver lifecycle independent of K8s |
| Fast reboot recovery | Driver immediately available after reboot |
| Standard debugging | `nvidia-smi` works on host directly |

**Trade-off accepted**: Manual driver management per node (use Ansible or node images for scale).

### 4.4 GPU Management: Backend.AI Only (no NVIDIA Device Plugin)

| Reason | Details |
|---|---|
| No conflict | Backend.AI manages all GPU allocation via etcd |
| No code changes | Existing accelerator plugins work as-is |
| Full feature support | Multi-GPU, fractional GPU (CUDA hooks), MIG all work |
| Taint isolation | GPU nodes tainted to prevent K8s GPU workloads |

### 4.5 Storage: Host Pre-Mounted NFS

| Reason | Details |
|---|---|
| Simplest setup | fstab or systemd mount on each node |
| No DaemonSet | No mountPropagation complexity |
| Same as bare-metal | No change from current production model |
| Independent of Agent | Agent restart does not affect NFS mounts |

**Trade-off accepted**: Infrastructure team must mount NFS on each node (use cloud-init or Ansible).

### 4.6 Redis HA: Valkey (OSS fork) with Sentinel

> **Bitnami 유료화 대응**: 2025-08-28부로 Bitnami 이미지가 `docker.io/bitnamilegacy/*`로 이동되고 최신 보안 패치는 Bitnami Secure Images (유료 구독)로만 제공됨. **Plan 1은 전 컴포넌트 OSS로만 구성한다.**

| Reason | Details |
|---|---|
| BSD 라이선스, 장기 지원 | Valkey는 Redis 7.4 기반 커뮤니티 포크 (Linux Foundation, AWS/Google/Oracle 후원) |
| Backend.AI 호환 | Redis 프로토콜 100% 호환, 기존 Sentinel 클라이언트 코드 그대로 사용 |
| 공식 Helm 차트 | `valkey-io/valkey` (replication + Sentinel 모드 지원) |
| 대안 | `ot-container-kit/redis-operator` (Sentinel/Cluster 둘 다 지원, Operator 방식) |

### 4.7 PostgreSQL HA: CloudNativePG Operator

| Reason | Details |
|---|---|
| CNCF Sandbox 프로젝트 | Apache-2.0, EDB 주도, 활발한 커뮤니티 |
| Operator 네이티브 | `Cluster` CRD 하나로 HA, 백업, PITR, 롤링 업그레이드 관리 |
| Patroni 불필요 | 자체 failover 로직 내장, etcd 의존성 없음 |
| Backend.AI 호환 | 표준 PostgreSQL 프로토콜, 연결 문자열만 주입 |
| External option | AWS RDS / Google Cloud SQL / Azure Database도 동일 방식으로 DB URL만 주입 |

### 4.7.1 etcd: 자체 StatefulSet (의존성 제거)

| Reason | Details |
|---|---|
| 공식 차트 부재 | etcd-io는 Helm 차트 공식 제공 안 함, etcd-operator는 사실상 아카이브 |
| 요구사항 단순 | Backend.AI는 read/write/watch + 옵션 RBAC만 사용 — 70줄 StatefulSet으로 충분 |
| OSS 이미지 | `quay.io/coreos/etcd:v3.5.x` (Apache-2.0) 직접 사용 |
| 구성 | 3 replica StatefulSet + headless Service + PVC (8Gi) + 기본 RBAC |

### 4.8 Agent Networking: hostNetwork: true

| Reason | Details |
|---|---|
| Manager RPC works | Manager can reach Agent at node IP |
| Kernel REPL works | Agent can reach kernel via host loopback (127.0.0.1) |
| No CNI needed | Bypasses K8s pod network entirely |

### 4.9 Init Containers: Native Client Health Checks

| Reason | Details |
|---|---|
| Robust | Uses `etcdctl endpoint health`, `pg_isready`, `redis-cli ping` |
| No race conditions | Verifies actual service readiness, not just port open |
| Minimal extra images | Only 3 small clients needed |

### 4.10 DB Migration: Helm Pre-Upgrade Hook

| Reason | Details |
|---|---|
| Standard pattern | Helm pre-upgrade Job runs `alembic upgrade head` |
| Atomic | Migration must succeed before Manager Pod is updated |
| Automatic | No manual intervention required |

### 4.11 Image Registry Auth: Helm Post-Install Hook Sync

| Reason | Details |
|---|---|
| Single source | K8s Secret is the only place credentials are stored |
| Automatic sync | Helm hook copies credentials to etcd on install/upgrade |
| No dual management | Updating K8s Secret + `helm upgrade` is enough |

---

## 5. Helm Chart Structure

```
backendai/                              # Umbrella chart
├── Chart.yaml
├── values.yaml                         # Single source of truth
├── charts/                             # External dependencies
│   ├── etcd/                           # bitnami/etcd
│   ├── postgresql/                     # single instance or external
│   └── redis/                          # bitnami/redis (Sentinel mode)
└── templates/
    ├── namespace.yaml
    ├── secrets.yaml                    # DB, etcd, Redis credentials
    ├── manager-deployment.yaml
    ├── manager-service.yaml
    ├── manager-configmap.yaml
    ├── agent-daemonset.yaml
    ├── appproxy-coordinator-deployment.yaml
    ├── appproxy-worker-deployment.yaml
    ├── webserver-deployment.yaml
    ├── webserver-ingress.yaml
    └── jobs/
        ├── sync-registry-creds.yaml    # post-install/post-upgrade
        ├── db-migrate-manager.yaml     # pre-install/pre-upgrade
        └── db-migrate-appproxy.yaml    # pre-install/pre-upgrade
```

**Total Helm dependencies**: 3 external charts (etcd, postgresql, redis)

---

## 6. Deployment Steps

### 6.1 Prerequisites (per node)

```bash
# 1. Install Docker
apt install docker-ce

# 2. Install NVIDIA driver and toolkit
apt install nvidia-driver-535
apt install nvidia-container-toolkit
systemctl restart docker

# 3. Verify
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 4. Mount NFS for vfolder
echo "nfs-server:/export /mnt/vfolder nfs vers=4.1,hard 0 0" >> /etc/fstab
mount -a

# 5. Apply Backend.AI taint
kubectl taint nodes <node-name> backendai.io/dedicated=agent:NoSchedule

# 6. Label node
kubectl label nodes <node-name> backendai.io/role=agent
```

### 6.2 Cluster Setup

```bash
# Create namespace
kubectl create namespace backendai-system

# Create secrets
kubectl create secret generic backendai-etcd-credentials \
  --from-literal=password='XXX' -n backendai-system

kubectl create secret generic backendai-db-credentials \
  --from-literal=password='XXX' -n backendai-system

kubectl create secret generic backendai-redis-credentials \
  --from-literal=password='XXX' -n backendai-system

kubectl create secret docker-registry harbor-credentials \
  --docker-server=harbor.internal \
  --docker-username=USER \
  --docker-password=PASS \
  -n backendai-system
```

### 6.3 Install

```bash
helm install backendai ./backendai \
  -n backendai-system \
  --create-namespace \
  -f values.yaml
```

### 6.4 Verify

```bash
kubectl get pods -n backendai-system
# Expected: All pods Running

# Check Agent registered to etcd
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl get /backend/agents --prefix

# Test session creation
./bai session create python:3.11 --resources cuda.device=1
```

### 6.5 Upgrade

```bash
# Standard Helm upgrade triggers DB migration hook automatically
helm upgrade backendai ./backendai \
  -n backendai-system \
  --set manager.image.tag="25.13.0"
```

---

## 7. Required Code Changes

| Component | Change | Effort |
|---|---|---|
| **Agent** | None — uses existing `DockerAgent` with DooD | 0 days |
| **Agent** | Verify `BACKEND_ETCD_ADDR` env var override (already supported) | 0 days |
| **Agent** | Add `BACKEND_AGENT_HOST_OVERRIDE` injection via Downward API in DaemonSet | 1 day |
| **Manager** | Verify `BACKEND_DB_ADDR`, `BACKEND_REDIS_*` env var overrides (already supported) | 0 days |
| **Manager** | Update `announce-addr` to use K8s Service DNS in config template | 1 day |
| **Helm chart** | Write Helm chart from scratch | 5-10 days |
| **CI/CD** | Add Helm chart linting and basic deployment test | 2-3 days |
| **Documentation** | Installation guide, upgrade guide, troubleshooting | 3-5 days |

**Total: ~2-4 weeks for 1-2 engineers**

---

## 8. Explicitly Deferred Features

The following features are **deliberately excluded** from Plan 1. They can be added in future phases if needed:

| Feature | When to Add | Estimated Additional Effort |
|---|---|---|
| containerd-based DooD | When dual-runtime overhead becomes problematic | 2-3 months |
| Multi-region deployment | When geographic distribution is required | 1-2 months |
| Service mesh (mTLS, observability) | When zero-trust networking required | 1 month |
| TLS automation (cert-manager) | When manual cert renewal becomes operational burden | 1 week |
| Advanced storage (CephFS CSI, dynamic PVC) | When NFS becomes bottleneck | 2-4 weeks |
| Live migration | When zero-downtime upgrades required | Major (KubeVirt) |
| VM-based isolation (Kata, KubeVirt) | When security/compliance requires hardware isolation | 12-18 months (see `support_vm_kata.md`) |
| PostgreSQL HA (CloudNativePG) | When PostgreSQL is single point of failure | 1-2 weeks |
| Backup automation | When manual backup becomes risky | 1-2 weeks |
| Custom CNI for kernels | When K8s NetworkPolicy needed for kernels | Months (see CNI EXP-1/2/3) |
| GPU Operator-based driver install | When fleet of nodes needs centralized driver mgmt | 1 week |
| NFS Mounter DaemonSet | When fully Helm-managed NFS mount is required | 1 week |

---

## 9. Effort Estimate

| Phase | Activity | Duration |
|---|---|---|
| Week 1 | Helm chart skeleton, control plane templates | 5 days |
| Week 2 | Agent DaemonSet, init containers, secrets | 5 days |
| Week 3 | DB migration hooks, registry sync hook, integration testing | 5 days |
| Week 4 | Documentation, deployment guide, polishing | 5 days |
| **Total** | | **~4 weeks (1-2 engineers)** |

This estimate assumes:
- Existing K8s + Helm familiarity
- Test cluster available with GPU nodes
- No major refactoring of Backend.AI Agent or Manager code
- No regulatory or security review delays

---

## 10. Risk Summary

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| GPU device plugin conflict | Low | Medium | Do not install device plugin on agent nodes |
| Docker Swarm overlay + K8s CNI overlap | Medium | Medium | Use distinct CIDR ranges (172.30.0.0/16 for Swarm) |
| Agent pod eviction | Low | High | Use `priorityClassName: backendai-agent-critical` |
| Manager rescheduled off Swarm manager node | Medium | High | Pin Manager Pod via `nodeSelector` + taint to the Swarm manager node (see §4.2) |
| Docker group GID mismatch between nodes | Medium | High | `docker.sock` host mount requires the in-Pod user to belong to the host's docker group GID (Debian/Ubuntu: 999, RHEL/Rocky: varies). A single hardcoded `dockerGid` in `values.yaml` breaks on mixed-distro clusters — detect GID at Pod start (init-container reads `stat -c '%g' /var/run/docker.sock` and injects as supplementary group) or set per-node values override |
| CNI ↔ Swarm VXLAN port conflict (4789) | High (Flannel/Calico-VXLAN) / None (Cilium) | High | Always init Swarm with `--data-path-port 7789` regardless of current CNI; see §4.2 conflict matrix |
| NFS mount disappears | Low | High | Host-level mount independent of Agent pod |
| Image registry auth desync | Low | Medium | Helm post-install hook re-syncs on every upgrade |
| DB migration failure | Medium | High | Helm pre-upgrade hook aborts upgrade on failure |
| Manager rolling update breaks RPC | Low | Medium | Test rolling update in staging first |
| etcd quorum loss during install | Low | High | Use 3-node etcd, verify quorum before Manager starts |

---

## Conclusion

Plan 1 represents the **fastest viable path** to deploying Backend.AI on Kubernetes — approximately 4 weeks of focused work for 1-2 engineers. It preserves all existing GPU features and uses Backend.AI's current networking model unchanged.

Trade-offs are explicit and documented: containerd migration, VM-based isolation, advanced HA, and other complex features are deferred to later phases. This plan creates a working foundation that can be incrementally improved without architectural rewrites.

**When to choose Plan 1:**
- First K8s deployment (no prior production experience on K8s)
- Single-cluster, single-region deployment
- Trusted users (no need for VM-based isolation)
- Standard Linux distros with manageable node count
- Time pressure / proof-of-concept requirements

**When NOT to choose Plan 1:**
- Multi-tenant with untrusted code (need VM isolation — see `support_vm_kata.md`)
- Strict compliance requirements (need hardware-enforced isolation)
- Large-scale deployment with 100+ nodes (need GPU Operator, NFS Mounter DaemonSet, advanced automation)
- Multi-cluster federation requirements
