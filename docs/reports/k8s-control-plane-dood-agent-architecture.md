# Backend.AI K8s Control Plane + DooD Agent Architecture Proposal

| Field | Value |
|---|---|
| **Document ID** | TR-2026-002 |
| **Date** | 2026-04-08 |
| **Author** | Backend.AI Architecture Team |
| **Status** | Draft |
| **Classification** | Internal Technical Reference |
| **Scope** | K8s-native control plane deployment, DooD-based agent architecture, container runtime selection (Docker vs containerd) |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Introduction and Motivation](#2-introduction-and-motivation)
   - 2.1 [Background](#21-background)
   - 2.2 [Goals](#22-goals)
   - 2.3 [Scope](#23-scope)
   - 2.4 [Assumptions and Prerequisites](#24-assumptions-and-prerequisites)
3. [Current Architecture Overview](#3-current-architecture-overview)
   - 3.1 [Component Topology](#31-component-topology)
   - 3.2 [Agent-Kernel Relationship](#32-agent-kernel-relationship)
   - 3.3 [Infrastructure Dependencies](#33-infrastructure-dependencies)
4. [Proposed Architecture: K8s Control Plane + DooD Agent](#4-proposed-architecture-k8s-control-plane--dood-agent)
   - 4.1 [Architecture Overview](#41-architecture-overview)
   - 4.2 [Control Plane Components](#42-control-plane-components)
   - 4.3 [Agent Pod with DooD](#43-agent-pod-with-dood)
   - 4.4 [Kernel Container Lifecycle](#44-kernel-container-lifecycle)
   - 4.5 [Networking Architecture](#45-networking-architecture)
   - 4.6 [Storage Architecture](#46-storage-architecture)
   - 4.7 [GPU and Accelerator Passthrough](#47-gpu-and-accelerator-passthrough)
     - 4.7.1 [Two-Layer GPU Management](#471-two-layer-gpu-management)
     - 4.7.2 [NVIDIA Driver and Container Toolkit (Host-Level Prerequisite)](#472-nvidia-driver-and-container-toolkit-host-level-prerequisite)
     - 4.7.3 [Agent Pod GPU Access](#473-agent-pod-gpu-access)
     - 4.7.4 [Kernel Container GPU Allocation](#474-kernel-container-gpu-allocation)
     - 4.7.5 [Fractional GPU Hook Library Distribution](#475-fractional-gpu-hook-library-distribution)
     - 4.7.6 [MIG Partitioning](#476-mig-partitioning)
     - 4.7.7 [GPU Health Monitoring and Failure Handling](#477-gpu-health-monitoring-and-failure-handling)
     - 4.7.8 [Compute Plugin Image Strategy](#478-compute-plugin-image-strategy)
     - 4.7.9 [VM-Based Isolation Alternatives (External Document)](#479-vm-based-isolation-alternatives-external-document)
5. [Container Runtime Analysis: Docker vs containerd](#5-container-runtime-analysis-docker-vs-containerd)
   - 5.1 [DooD with Docker (docker.sock)](#51-dood-with-docker-dockersock)
   - 5.2 [DooD with containerd (containerd.sock)](#52-dood-with-containerd-containerdsock)
   - 5.3 [Feature Parity Matrix](#53-feature-parity-matrix)
   - 5.4 [Performance Comparison](#54-performance-comparison)
   - 5.5 [Security Comparison](#55-security-comparison)
   - 5.6 [Operational Complexity](#56-operational-complexity)
   - 5.7 [Runtime Selection Recommendation](#57-runtime-selection-recommendation)
   - 5.8 [CNI Integration Strategy for containerd DooD](#58-cni-integration-strategy-for-containerd-dood)
6. [Control Plane Installation (Helm)](#6-control-plane-installation-helm)
   - 6.1 [Dependency Chain and Bootstrap Order](#61-dependency-chain-and-bootstrap-order)
   - 6.2 [Service Discovery Architecture](#62-service-discovery-architecture)
   - 6.3 [Helm Chart Structure](#63-helm-chart-structure)
   - 6.4 [Global Values Configuration](#64-global-values-configuration)
   - 6.5 [Component Environment Variable Injection](#65-component-environment-variable-injection)
   - 6.6 [Boot Sequence and Init Containers](#66-boot-sequence-and-init-containers)
   - 6.7 [Installation Commands](#67-installation-commands)
   - 6.8 [Container Image Management](#68-container-image-management)
   - 6.9 [Database Migration Strategy (Alembic)](#69-database-migration-strategy-alembic)
   - 6.10 [Redis High Availability](#610-redis-high-availability)
7. [Detailed Component Design](#7-detailed-component-design)
   - 7.1 [Control Plane Pod Specifications](#71-control-plane-pod-specifications)
   - 7.2 [Agent DaemonSet Design](#72-agent-daemonset-design)
   - 7.3 [Kernel Container Management](#73-kernel-container-management)
   - 7.4 [Service Discovery and Communication](#74-service-discovery-and-communication)
8. [Migration Path from Current Architecture](#8-migration-path-from-current-architecture)
   - 8.1 [Agent Code Changes Required](#81-agent-code-changes-required)
   - 8.2 [Manager Code Changes Required](#82-manager-code-changes-required)
   - 8.3 [Configuration Changes](#83-configuration-changes)
9. [Risk Analysis](#9-risk-analysis)
   - 9.1 [Technical Risks](#91-technical-risks)
   - 9.2 [Operational Risks](#92-operational-risks)
   - 9.3 [Mitigation Strategies](#93-mitigation-strategies)
10. [Alternative Approaches](#10-alternative-approaches)
    - 10.1 [Pure K8s-native (Kernels as Pods)](#101-pure-k8s-native-kernels-as-pods)
    - 10.2 [Hybrid: Agent on Host + Control Plane on K8s](#102-hybrid-agent-on-host--control-plane-on-k8s)
    - 10.3 [K8s Operator Pattern](#103-k8s-operator-pattern)
11. [Required Experiments](#11-required-experiments)
    - 11.1 [EXP-1: CNI Direct Invocation for DooD Containers](#111-exp-1-cni-direct-invocation-for-dood-containers)
    - 11.2 [EXP-2: CNI IPAM Coexistence with K8s Pods](#112-exp-2-cni-ipam-coexistence-with-k8s-pods)
    - 11.3 [EXP-3: Cross-Node Connectivity via Host CNI](#113-exp-3-cross-node-connectivity-via-host-cni)
    - 11.4 [EXP-4: GPU Device Access from DooD Kernel Containers](#114-exp-4-gpu-device-access-from-dood-kernel-containers)
    - 11.5 [EXP-5: Agent Pod Restart and Kernel Recovery](#115-exp-5-agent-pod-restart-and-kernel-recovery)
    - 11.6 [EXP-6: containerd DooD Basic Lifecycle](#116-exp-6-containerd-dood-basic-lifecycle)
    - 11.7 [EXP-7: vfolder Bind Mount Path Consistency](#117-exp-7-vfolder-bind-mount-path-consistency)
    - 11.8 [EXP-8: Docker Swarm Overlay Coexistence with K8s CNI](#118-exp-8-docker-swarm-overlay-coexistence-with-k8s-cni)
    - 11.9 [Experiment Execution Priority](#119-experiment-execution-priority)
12. [Conclusions and Recommendations](#12-conclusions-and-recommendations)
13. [References](#13-references)

---

## 1. Executive Summary

This report proposes an architecture where Backend.AI's control plane (Manager, etcd, PostgreSQL, Redis) runs as Kubernetes pods, while the Agent runs as a DaemonSet pod using Docker-out-of-Docker (DooD) to launch kernel (compute session) containers directly on the host's container runtime.

**Key findings:**

- DooD architecture preserves Backend.AI's existing Docker-based kernel lifecycle management while gaining K8s operational benefits (rolling updates, self-healing, declarative configuration) for the control plane.
- **containerd is recommended over Docker** as the DooD runtime target for new deployments. containerd is the standard K8s CRI runtime, eliminates the Docker daemon dependency, and provides equivalent functionality for Backend.AI's use cases. Docker remains a viable option for environments where it is already deployed or where Docker Compose-based tooling is required.
- Agent DaemonSet pods require `privileged` or specific capability grants to access the host container runtime socket, GPU devices, and host network/storage paths.
- The proposed architecture supports full GPU passthrough (multi-GPU, fractional GPU), vfolder bind mounts, and overlay networking without the limitations observed in VM-based isolation (e.g., Kata Containers).
- Migration from the current bare-metal/VM agent deployment is incremental: the existing `DockerAgent` codebase requires minimal changes since DooD containers share the same Docker/containerd API surface.

---

## 2. Introduction and Motivation

### 2.1 Background

Backend.AI currently supports two agent backends: `docker` (production) and `kubernetes` (experimental). The `docker` backend is the mature, feature-complete implementation used in production deployments. Agents are typically deployed directly on bare-metal or VM hosts, alongside infrastructure services (etcd, Redis, PostgreSQL) that may be co-located or on separate hosts.

This deployment model has operational challenges:
- **Infrastructure provisioning**: Each agent node requires manual or Ansible-based setup of the Docker daemon, agent process, compute plugins, and network configuration.
- **Control plane management**: Manager, etcd, PostgreSQL, and Redis require separate deployment, monitoring, and lifecycle management outside of Kubernetes.
- **Scaling**: Adding agent nodes requires manual registration with the manager cluster.
- **Updates**: Rolling updates of the agent require custom orchestration.

### 2.2 Goals

1. **K8s-native control plane**: Run Manager, etcd, PostgreSQL, and Redis as standard K8s workloads, leveraging StatefulSets, Services, ConfigMaps, and Helm charts.
2. **K8s-managed agent lifecycle**: Deploy agents as a DaemonSet, gaining automatic scheduling to GPU nodes, rolling updates, and health-based restarts.
3. **Preserve kernel management model**: Continue using Docker/containerd APIs directly for kernel container lifecycle, preserving the full feature set (multi-GPU, fractional GPU, overlay networks, bind mounts).
4. **Minimal code changes**: Leverage the existing `DockerAgent` implementation with DooD rather than requiring a new K8s-native kernel management layer.

### 2.3 Scope

This document covers:
- Architecture design for K8s-based control plane deployment
- DooD agent pod design and host resource access patterns
- Container runtime selection (Docker daemon vs containerd) for kernel management
- Migration path and required code changes
- Risk analysis and alternative approaches

### 2.4 Assumptions and Prerequisites

This architecture is based on the following explicit assumptions. These must hold true for the design to work as described, and they define the boundary between Kubernetes's management domain and Backend.AI's management domain.

#### 2.4.1 GPU Resources Are Not Managed by Kubernetes

Kubernetes does **not** schedule, allocate, or track GPU resources on Backend.AI agent nodes. Specifically:

- The NVIDIA device plugin (`nvidia-device-plugin-daemonset`) is **not deployed** on agent nodes.
- `nvidia.com/gpu` resource requests in K8s Pod specs have no meaning on these nodes.
- GPU allocation is handled entirely by Backend.AI's own scheduler (Sokovan) via etcd.
- Kubernetes has no visibility into which GPU is used by which kernel container.

Attempting to share GPU management between K8s device plugin and Backend.AI Agent would cause dual-allocation conflicts (the same GPU assigned to a K8s Pod and a Backend.AI kernel simultaneously) and would require rewriting Backend.AI's accelerator plugin system to integrate with the K8s device plugin API. This integration is explicitly **out of scope**.

#### 2.4.2 GPU Nodes Are Isolated via Taints

All Backend.AI agent nodes are marked with a dedicated taint:

```bash
kubectl taint nodes <gpu-node> backendai.io/dedicated=agent:NoSchedule
```

This has the following effects:

- Generic K8s workloads cannot schedule onto these nodes (no toleration for the taint).
- Only Backend.AI's DaemonSets (Agent, NFS Mounter) tolerate this taint and can run on these nodes.
- Kernel containers (DooD) are unaffected by taints since they are not K8s resources — they bypass the K8s scheduler entirely.

This isolation guarantees that node resources (CPU, memory, GPU) are reserved exclusively for Backend.AI workloads, preventing noisy-neighbor scenarios with unrelated K8s Pods.

#### 2.4.3 Kernel Containers Operate Outside Kubernetes Control

Kernel containers are created via Docker/containerd API (DooD), not as K8s Pods. Therefore:

- K8s has no knowledge of kernel container lifecycle, resource usage, labels, or networking.
- `kubectl get pods` does not show kernel containers.
- K8s NetworkPolicy, PodSecurityPolicy, LimitRange, and ResourceQuota do not apply to kernel containers.
- Kernel container metrics are collected by Backend.AI's own monitoring (not K8s Prometheus stack by default).

All kernel-level operations — creation, bind mounts, GPU allocation, health monitoring, cleanup — are the responsibility of the Backend.AI Agent.

#### 2.4.4 Dedicated Node Pools

A clear separation between node pools is required:

| Node Pool | Taint | Purpose | Workloads |
|---|---|---|---|
| **Control plane pool** | None | Run K8s-managed Backend.AI services | Manager, PostgreSQL, Redis, etcd, AppProxy, WebServer |
| **Agent pool** | `backendai.io/dedicated=agent:NoSchedule` | Run Backend.AI Agent and kernel containers | Agent DaemonSet, NFS Mounter DaemonSet, kernel containers (via DooD) |

Mixing control plane workloads and agent workloads on the same node is **not supported** and will result in resource contention.

#### 2.4.5 NVIDIA Driver and Container Toolkit Are Host-Level Prerequisites

NVIDIA GPU drivers and the NVIDIA Container Toolkit are treated as **host-level prerequisites**, equivalent to Docker, containerd, and kubelet. They must be installed on each agent node before Backend.AI is deployed, and Kubernetes/Helm does not manage their installation.

**Rationale:**

- NVIDIA drivers are kernel modules, tightly coupled to the host kernel version.
- Drivers must be available immediately on node boot, not after a DaemonSet reconciles.
- Container runtime (Docker/containerd) must have `nvidia-container-runtime` configured at daemon level, which is a host-level configuration.
- Debugging GPU issues is significantly easier with host-level drivers than with containerized driver installers.

**Installation methods** (choose one):

| Environment | Recommended Method |
|---|---|
| Bare-metal / on-premises | Node OS image with drivers pre-baked (Packer, Ansible) |
| Cloud (AWS/GCP/Azure) | GPU-enabled base image (Deep Learning AMI, etc.) or cloud-init |
| Kubernetes distributions | K3s/RKE2 GPU setup, or RHEL/OpenShift GPU node provisioning |

**Required state before Backend.AI deployment:**

1. `nvidia-smi` runs successfully on the host
2. NVIDIA Container Toolkit is installed and configured in Docker/containerd
3. `docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi` works on the host

Backend.AI Agent will fail to enumerate GPUs if any of these are missing.

**Note on NVIDIA GPU Operator**: The Operator's driver installation feature (containerized driver DaemonSet) is **not recommended** as the primary installation method. See Section 4.7.2 for details on optional Operator usage limited to GPU Feature Discovery and DCGM metrics.

#### 2.4.6 Management Domain Boundary

The assumptions above establish a clear boundary between what Kubernetes manages and what Backend.AI manages:

| Domain | Managed by | Scope |
|---|---|---|
| Control plane lifecycle | Kubernetes | Manager/DB/Redis/etcd/AppProxy Pod scheduling, health, rolling updates |
| Agent DaemonSet lifecycle | Kubernetes | Agent Pod scheduling, health, rolling updates |
| GPU device allocation | **Backend.AI** | Physical GPU to kernel container assignment, fractional sharing, MIG partitioning |
| Kernel container lifecycle | **Backend.AI** | Container creation, bind mounts, REPL communication, service port mapping |
| Kernel networking | **Backend.AI + Docker/containerd** | Bridge/overlay networks, inter-kernel communication |
| Storage mount orchestration | **Backend.AI + host/CSI** | vfolder paths, scratch space |

This separation is intentional and preserves the full feature set of Backend.AI's existing accelerator plugin system (fractional GPU via CUDA hook libraries, multi-GPU allocation, MIG support, etc.) without requiring re-architecture. Sections 4.7 (GPU and Accelerator Passthrough) and later sections assume these prerequisites are in place.

---

## 3. Current Architecture Overview

### 3.1 Component Topology

```
┌─────────────────────── Deployment Topology ───────────────────────┐
│                                                                    │
│  ┌─── Manager Node(s) ───────────────────────────────────────┐    │
│  │  ┌──────────┐  ┌──────────┐  ┌───────┐  ┌─────────────┐  │    │
│  │  │ Manager  │  │PostgreSQL│  │ Redis │  │    etcd     │  │    │
│  │  │ (Python) │  │          │  │       │  │             │  │    │
│  │  └────┬─────┘  └──────────┘  └───────┘  └─────────────┘  │    │
│  │       │ ZeroMQ/Callosum RPC                                │    │
│  └───────┼────────────────────────────────────────────────────┘    │
│          │                                                         │
│  ┌───────▼─── Agent Node (per GPU host) ─────────────────────┐    │
│  │  ┌──────────┐     ┌──────────────┐                        │    │
│  │  │  Agent   │────▶│ Docker Daemon│                        │    │
│  │  │ (Python) │     │              │                        │    │
│  │  └──────────┘     └──────┬───────┘                        │    │
│  │                          │                                 │    │
│  │          ┌───────────────┼───────────────┐                 │    │
│  │          │               │               │                 │    │
│  │   ┌──────▼───┐   ┌──────▼───┐   ┌──────▼───┐             │    │
│  │   │ Kernel 1 │   │ Kernel 2 │   │ Kernel 3 │             │    │
│  │   │(Session) │   │(Session) │   │(Session) │             │    │
│  │   └──────────┘   └──────────┘   └──────────┘             │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent-Kernel Relationship

The Backend.AI Agent (`DockerAgent` at `src/ai/backend/agent/docker/agent.py`) manages kernel containers via the Docker API (`aiodocker` library):

- **Container creation**: Agent creates Docker containers with specific resource limits, GPU device mappings, network configuration, and volume mounts.
- **Lifecycle management**: Start, stop, restart, and destroy operations go through the agent's state machine (`agent/stage/`).
- **Resource allocation**: GPU allocation (whole, fractional via CUDA hook libraries), CPU pinning, and memory limits are set via Docker container create parameters.
- **Storage**: vfolders are bind-mounted from host paths into kernel containers.
- **Networking**: Docker overlay networks (Swarm mode) provide multi-node session connectivity.

### 3.3 Infrastructure Dependencies

| Component | Role | Connection Method |
|---|---|---|
| PostgreSQL | Persistent state (sessions, users, resource policies) | TCP (asyncpg) |
| Redis/Valkey | Pub/sub, caching, live session state | TCP (redis-py async) |
| etcd | Configuration store, service discovery, distributed locks | gRPC (etcetra) |
| Docker Daemon | Kernel container lifecycle | Unix socket (`/var/run/docker.sock`) |
| Manager | Orchestration, scheduling, API gateway | ZeroMQ/Callosum RPC |

---

## 4. Proposed Architecture: K8s Control Plane + DooD Agent

### 4.1 Architecture Overview

```
┌───────────────────── Kubernetes Cluster ─────────────────────────────┐
│                                                                       │
│  ┌─── Control Plane Namespace (backendai-system) ────────────────┐   │
│  │                                                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  ┌──────────┐ │   │
│  │  │  Manager    │  │ PostgreSQL  │  │  Redis  │  │   etcd   │ │   │
│  │  │ Deployment  │  │ StatefulSet │  │ Deploy/ │  │ Stateful │ │   │
│  │  │ (replicas:  │  │ (replicas:  │  │ Stateful│  │ Set      │ │   │
│  │  │  2-3, HA)  │  │  1-3, HA)  │  │ Set     │  │ (3 nodes)│ │   │
│  │  └──────┬──────┘  └─────────────┘  └─────────┘  └──────────┘ │   │
│  │         │ K8s Service (ClusterIP)                              │   │
│  └─────────┼──────────────────────────────────────────────────────┘   │
│            │ ZeroMQ RPC (K8s Service endpoint)                        │
│            │                                                          │
│  ┌─────────▼─── Agent DaemonSet (GPU node pool) ─────────────────┐   │
│  │                                                                │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  Agent Pod (per node)                                    │  │   │
│  │  │  ┌────────────┐     ┌──────────────────────────────┐     │  │   │
│  │  │  │   Agent    │────▶│ Host Container Runtime       │     │  │   │
│  │  │  │ Container  │     │ (Docker/containerd via       │     │  │   │
│  │  │  │            │     │  mounted socket - DooD)      │     │  │   │
│  │  │  └────────────┘     └──────────────┬───────────────┘     │  │   │
│  │  └────────────────────────────────────┼─────────────────────┘  │   │
│  │                                       │                        │   │
│  │     ┌─────────────────────────────────┼──────────────────┐     │   │
│  │     │              Host               │                  │     │   │
│  │     │  ┌───────────┐  ┌───────────┐  ┌───────────┐      │     │   │
│  │     │  │ Kernel 1  │  │ Kernel 2  │  │ Kernel 3  │      │     │   │
│  │     │  │ Container │  │ Container │  │ Container │      │     │   │
│  │     │  │ [GPU 0,1] │  │ [GPU 2]   │  │ [CPU only]│      │     │   │
│  │     │  └───────────┘  └───────────┘  └───────────┘      │     │   │
│  │     └────────────────────────────────────────────────────┘     │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 4.2 Control Plane Components

Each control plane component runs as a standard K8s workload:

| Component | K8s Workload Type | Replicas | Persistence | Notes |
|---|---|---|---|---|
| Manager | Deployment | 2-3 (HA) | None (stateless) | Exposed via K8s Service (ClusterIP for internal, LoadBalancer/Ingress for API) |
| PostgreSQL | StatefulSet | 1 (single) or 3 (HA with Patroni/CloudNativePG) | PVC (PersistentVolumeClaim) | Use CloudNativePG operator or external managed DB |
| Redis/Valkey | Deployment or StatefulSet | 1 (single) or 3 (Sentinel/Cluster) | PVC (optional, AOF) | Consider managed Redis (ElastiCache, Memorystore) for production |
| etcd | StatefulSet | 3 (quorum) | PVC per member | Use etcd operator or Bitnami Helm chart |
| Storage Proxy | Deployment | 1-2 | None | Needs access to storage backends |
| AppProxy Coordinator | Deployment | 1-2 | None (stateless) | Needs DB + etcd + Redis; manages app routing rules |
| AppProxy Worker | Deployment | 2-3 | None (stateless) | Needs Redis + etcd; handles actual traffic proxying |
| Web Server | Deployment | 2-3 | None | Ingress for external access |

**Key design decisions:**

- **Namespace isolation**: Control plane in `backendai-system` namespace; kernels run directly on host (outside K8s) or optionally in a separate namespace.
- **Service mesh optional**: Internal control plane communication can use K8s Services directly; Istio/Linkerd optional for mTLS and observability.
- **ConfigMaps and Secrets**: Manager configuration, database credentials, etcd TLS certificates managed via K8s-native primitives.

### 4.3 Agent Pod with DooD

The Agent runs as a **DaemonSet** pod scheduled on every node in the GPU node pool. It accesses the host's container runtime via a mounted socket:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: backendai-agent
  namespace: backendai-system
spec:
  selector:
    matchLabels:
      app: backendai-agent
  template:
    metadata:
      labels:
        app: backendai-agent
    spec:
      hostNetwork: true          # Agent needs host networking for kernel communication
      hostPID: false
      nodeSelector:
        backendai.io/role: agent  # Schedule only on agent-designated nodes
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      serviceAccountName: backendai-agent
      containers:
        - name: agent
          image: lablup/backend.ai-agent:latest
          securityContext:
            privileged: true                    # Required for GPU device access and runtime socket
            readOnlyRootFilesystem: true
            seccompProfile:
              type: RuntimeDefault
          volumeMounts:
            # DooD: mount host container runtime socket
            - name: container-runtime-socket
              mountPath: /var/run/docker.sock   # or /run/containerd/containerd.sock
            # Host paths for kernel data
            - name: scratch-space
              mountPath: /var/cache/scratches
            - name: vfolder-storage
              mountPath: /vfolder
            # Host metrics visibility: Pod-internal /proc and /sys reflect the
            # Pod's cgroup, not the host. The agent needs host-level /proc and
            # /sys mounted read-only for accurate resource detection and metrics
            # collection (CPU topology, memory capacity, disk I/O counters, etc.).
            - name: host-proc
              mountPath: /host/proc
              readOnly: true
            - name: host-sys
              mountPath: /host/sys
              readOnly: true
            # NVIDIA device files
            - name: nvidia-devices
              mountPath: /dev/nvidia0
              # ... (dynamically mapped based on node GPU count)
          env:
            - name: BACKEND_AGENT_BACKEND
              value: "docker"       # Uses existing DockerAgent with DooD
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
      volumes:
        - name: container-runtime-socket
          hostPath:
            path: /var/run/docker.sock  # or /run/containerd/containerd.sock
            type: Socket
        - name: scratch-space
          hostPath:
            path: /var/cache/backendai/scratches
            type: DirectoryOrCreate
        - name: vfolder-storage
          hostPath:
            path: /mnt/vfolder
            type: Directory
        - name: host-proc
          hostPath:
            path: /proc
            type: Directory
        - name: host-sys
          hostPath:
            path: /sys
            type: Directory
```

**Critical host mounts for DooD agent:**

| Host Path | Purpose | Mount Type |
|---|---|---|
| `/var/run/docker.sock` or `/run/containerd/containerd.sock` | Container runtime API access | Socket |
| `/var/cache/backendai/scratches` | Kernel scratch space (working directories) | DirectoryOrCreate |
| `/mnt/vfolder` (or configured storage path) | vfolder storage backend mount point | Directory |
| `/dev/nvidia*` | GPU device files | Device (via NVIDIA device plugin) |
| `/usr/local/nvidia` or `/usr/lib/x86_64-linux-gnu` | NVIDIA driver libraries | Directory (read-only) |
| `/proc` | Host process/CPU/memory information | Directory (read-only, mounted at `/host/proc`) |
| `/sys` | Host sysfs for device and metrics information | Directory (read-only, mounted at `/host/sys`) |

**Security hardening note**: `privileged: true` is required for direct GPU device access and container runtime socket interaction, but should be combined with `readOnlyRootFilesystem: true` and a seccomp profile (`RuntimeDefault`) to limit the attack surface. It is recommended to create dedicated GPU node pools with taints (e.g., `backendai.io/role=agent:NoSchedule`) to isolate these privileged agent pods from other workloads.

### 4.4 Kernel Container Lifecycle

In the DooD model, kernel containers are created **on the host** via the mounted runtime socket. They are siblings of the agent pod, not children:

```
┌──────────────── K8s Node ────────────────────────────────────┐
│                                                               │
│  ┌── kubelet-managed ──────────────────────────────────────┐  │
│  │  Agent Pod (DaemonSet)                                  │  │
│  │  - Talks to host container runtime via mounted socket   │  │
│  └──────────────────────────┬──────────────────────────────┘  │
│                             │                                  │
│                    API calls via socket                         │
│                             │                                  │
│  ┌── Host Container Runtime ▼──────────────────────────────┐  │
│  │  docker daemon / containerd                              │  │
│  │                                                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │  Kernel A  │  │  Kernel B  │  │  Kernel C  │         │  │
│  │  │  (not      │  │  (not      │  │  (not      │         │  │
│  │  │  K8s-     │  │  K8s-     │  │  K8s-     │         │  │
│  │  │  managed)  │  │  managed)  │  │  managed)  │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Important characteristics:**

- Kernel containers are **not visible to Kubernetes**. They are managed entirely by the Backend.AI agent via the Docker/containerd API.
- This means K8s resource accounting does not include kernel containers. Node resource allocation must be coordinated through Backend.AI's own resource management (etcd-based slot allocation).
- Kernel containers have direct access to host GPUs, host network interfaces, and host storage — no virtualization layer overhead.

### 4.5 Networking Architecture

#### 4.5.1 Agent-to-Manager Communication

| Path | Protocol | K8s Mechanism |
|---|---|---|
| Agent → Manager RPC | ZeroMQ/Callosum | K8s Service (ClusterIP) + hostNetwork on agent |
| Agent → etcd | gRPC | K8s Service (ClusterIP) |
| Agent → Redis | TCP | K8s Service (ClusterIP) |
| Manager → Agent events | ZeroMQ pub/sub | Agent hostNetwork IP |

> **RPC Security**: Since the agent uses `hostNetwork: true`, sidecar-based service mesh (Istio/Linkerd) cannot intercept agent traffic for mTLS. Instead, Backend.AI's built-in ZeroMQ CURVE encryption should be enabled for Manager↔Agent RPC. Configure `manager-public-key` and agent keypair in the agent configuration to encrypt all RPC traffic without depending on a service mesh.

The agent pod uses `hostNetwork: true` so that:
1. The manager can reach the agent at the node's real IP address (required for the existing ZeroMQ-based RPC model).
2. Kernel containers (which run on the host network or Docker overlay) can communicate with the agent on `localhost` or the host IP.

#### 4.5.2 Kernel Networking

Kernel containers use Docker/containerd networking directly (not K8s CNI):

- **Single-node sessions**: Docker bridge network (`backendai_network`), same as current deployment.
- **Multi-node sessions (cluster mode)**: Docker Swarm overlay network for cross-node kernel communication (SSH, MPI, NCCL).
- **Service ports**: Exposed via Docker port mapping on the host, accessible through K8s NodePort or external load balancer.

**Note**: Docker Swarm overlay is independent of K8s CNI. The two networking stacks coexist on the same node. This is a common DooD pattern, but Swarm overlay and K8s CNI coexistence behavior varies by CNI implementation (iptables-based vs eBPF-based). The interaction must be validated per-environment — see EXP-8 in the Required Experiments section.

**Network performance note**: Docker Swarm overlay is the same networking mechanism used in Backend.AI's current bare-metal production deployments for multi-node sessions. Migrating the agent to a K8s DaemonSet (DooD) does not change the kernel container networking path — the Swarm overlay continues to operate identically. Therefore, there is **no network performance regression** compared to the current deployment model.

#### 4.5.3 Kernel Communication Model

Kernel containers are **infrastructure-agnostic** — they have no knowledge of etcd, Redis, PostgreSQL, or the Manager. The kernel codebase (`src/ai/backend/kernel/`, `src/ai/backend/runner/`) contains zero references to any infrastructure service. All external communication is mediated by the Agent.

**Communication channels:**

```
┌─── Node A ──────────────────────────────┐    ┌─── Node B ──────────────────────────────┐
│                                          │    │                                          │
│  ┌── Agent A (hostNetwork) ───────────┐  │    │  ┌── Agent B (hostNetwork) ───────────┐  │
│  │  ZeroMQ      ZeroMQ                │  │    │  │  ZeroMQ      ZeroMQ                │  │
│  │  ▲              ▲                   │  │    │  │  ▲              ▲                   │  │
│  └──┼──────────────┼──────────────────┘  │    │  └──┼──────────────┼──────────────────┘  │
│     │              │                      │    │     │              │                      │
│     ▼              ▼                      │    │     ▼              ▼                      │
│  ┌────────┐  ┌────────┐                  │    │  ┌────────┐  ┌────────┐                  │
│  │Kernel 1│  │Kernel 2│                  │    │  │Kernel 3│  │Kernel 4│                  │
│  └───┬────┘  └───┬────┘                  │    │  └───┬────┘  └───┬────┘                  │
│      └─────┬─────┘                        │    │      └─────┬─────┘                        │
│            │ Docker Swarm Overlay          │    │            │ Docker Swarm Overlay          │
└────────────┼──────────────────────────────┘    └────────────┼──────────────────────────────┘
             └──────────── Swarm Overlay ─────────────────────┘
                  (inter-kernel: SSH, MPI, NCCL)
```

Each kernel container has exactly two communication paths:

| Path | Protocol | Network | Purpose |
|---|---|---|---|
| Kernel → **local Agent** | ZeroMQ TCP (`127.0.0.1:{mapped_port}`) | Host loopback via Docker port mapping | Code execution (REPL in/out on ports 2000/2001), autocomplete, interrupt |
| Kernel ↔ **other kernels** (multi-node) | SSH, MPI, NCCL | Docker Swarm Overlay | Distributed training, cluster session inter-process communication |

**What kernels do NOT communicate with:**

| Component | Direct communication? | How it's handled |
|---|---|---|
| etcd | No | Agent reads/writes etcd on behalf of kernels |
| Redis | No | Agent publishes events and metrics to Redis |
| PostgreSQL | No | Manager handles all DB operations |
| Manager | No | Agent relays session state, events, and lifecycle operations |

**Why this matters for DooD**: Since kernels only need (1) host loopback for Agent REPL communication and (2) Docker Swarm overlay for inter-kernel communication, they require no access to K8s Service DNS, K8s CNI, or any cluster-internal networking. The kernel container images are completely unchanged when migrating from bare-metal to K8s DooD deployment.

**ZeroMQ REPL detail**: The Agent creates a `DockerCodeRunner` that connects to the kernel via ZeroMQ TCP:
- `repl_in` (container port 2000): Agent sends code to kernel
- `repl_out` (container port 2001): Kernel sends execution results to Agent

These ports are mapped to `127.0.0.1:{host_port}` by Docker. Because the Agent pod uses `hostNetwork: true`, it shares the host's loopback interface and can reach these mapped ports directly — identical to bare-metal behavior.

### 4.6 Storage Architecture

#### 4.6.1 vfolder Mount Path

```
┌── K8s Node ──────────────────────────────────────────────────┐
│                                                               │
│  Distributed Storage (CephFS/NFS/WekaFS)                     │
│  mounted at: /mnt/vfolder                                     │
│        │                                                      │
│        ├──────────────────────────────────┐                   │
│        │                                  │                   │
│  ┌─────▼──────┐                    ┌──────▼──────┐            │
│  │ Agent Pod  │                    │  Kernel     │            │
│  │ (reads     │                    │  Container  │            │
│  │  vfolder   │                    │  (bind mount│            │
│  │  metadata) │                    │   from host)│            │
│  └────────────┘                    └─────────────┘            │
└───────────────────────────────────────────────────────────────┘
```

- The distributed storage filesystem is mounted on the **host** node (via fstab, systemd mount, or CSI driver).
- The agent pod mounts this path via `hostPath` to read vfolder metadata and determine mount points.
- Kernel containers receive bind mounts from the same host path directly via Docker/containerd API.
- **No virtualization overhead** — bind mounts are native Linux filesystem operations, identical to the current bare-metal deployment.

#### 4.6.2 Scratch Space

Kernel scratch directories (`/home/work` inside kernels) are backed by host-local storage (SSD/NVMe). The agent pod and kernel containers both access `/var/cache/backendai/scratches` on the host.

#### 4.6.3 NFS Mount Considerations in DooD

In the current bare-metal deployment, NFS storage is mounted at the host OS level (via `fstab` or `systemd`). The Agent process simply reads the pre-mounted path (`mount-path` in `agent.toml`) and passes it as a Docker bind mount parameter to kernel containers. The Agent does **not** mount or unmount NFS — it is purely a consumer of an already-mounted path.

In a K8s DooD deployment, this creates a control gap: the Helm chart manages all Backend.AI components, but the host-level NFS mount is outside K8s control. Requiring infrastructure teams to pre-configure NFS mounts on each node defeats the self-contained deployment goal.

**Option A: Host Pre-Mount (simple, but external dependency)**

NFS is mounted on each node before Backend.AI is deployed, identical to bare-metal:

| Aspect | Description |
|---|---|
| Mount method | `fstab`, `systemd`, `cloud-init`, or node image |
| Controlled by | Infrastructure team (outside Helm) |
| Agent restart impact | None — mount is OS-level |
| Node scaling | Manual mount setup required on new nodes |
| `helm install` self-contained? | No |

**Option B: NFS Mounter DaemonSet (recommended for K8s-native deployment)**

A dedicated DaemonSet handles NFS mounting on each agent node, fully managed by the Helm chart:

```
┌─── Helm chart deploys both ───────────────────────────────────┐
│                                                                │
│  ┌── nfs-mounter DaemonSet ────────────────────────────────┐  │
│  │  - Mounts NFS on each node via mountPropagation         │  │
│  │  - Independent lifecycle from Agent                      │  │
│  │  - Health check: periodic mountpoint verification        │  │
│  │  - Auto-remount on failure                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌── Agent DaemonSet ──────────────────────────────────────┐  │
│  │  - init container waits for NFS mount                    │  │
│  │  - Accesses /mnt/vfolder via hostPath (already mounted)  │  │
│  │  - Restart does NOT affect NFS mount                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌── Kernel containers (DooD) ─────────────────────────────┐  │
│  │  - Docker bind mount from host /mnt/vfolder/...          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

The NFS Mounter DaemonSet:

```yaml
# templates/daemonset-nfs-mounter.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: {{ .Release.Name }}-nfs-mounter
spec:
  selector:
    matchLabels:
      app: backendai-nfs-mounter
  template:
    spec:
      nodeSelector:
        backendai.io/role: agent
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      priorityClassName: backendai-nfs-mounter-critical
      containers:
        - name: nfs-mounter
          image: busybox:1.36
          securityContext:
            privileged: true
          command: ['sh', '-c', |
            if ! mountpoint -q /mnt/vfolder; then
              echo "Mounting NFS..."
              mount -t nfs -o {{ .Values.global.storage.nfs.mountOptions }} \
                {{ .Values.global.storage.nfs.server }}:{{ .Values.global.storage.nfs.export }} \
                /mnt/vfolder
            fi
            # Stay alive and periodically verify mount
            while true; do
              if ! mountpoint -q /mnt/vfolder; then
                echo "NFS mount lost, remounting..."
                mount -t nfs -o {{ .Values.global.storage.nfs.mountOptions }} \
                  {{ .Values.global.storage.nfs.server }}:{{ .Values.global.storage.nfs.export }} \
                  /mnt/vfolder
              fi
              sleep 30
            done
          ]
          volumeMounts:
            - name: vfolder-mount
              mountPath: /mnt/vfolder
              mountPropagation: Bidirectional
          livenessProbe:
            exec:
              command: ['mountpoint', '-q', '/mnt/vfolder']
            periodSeconds: 30
            failureThreshold: 3
      volumes:
        - name: vfolder-mount
          hostPath:
            path: /mnt/vfolder
            type: DirectoryOrCreate
```

The Agent DaemonSet adds an init container to wait for the NFS mount:

```yaml
# Added to Agent DaemonSet init containers
- name: wait-for-nfs
  image: busybox:1.36
  command: ['sh', '-c',
    'until mountpoint -q /mnt/vfolder; do echo "waiting for NFS mount..."; sleep 3; done']
  volumeMounts:
    - name: vfolder-storage
      mountPath: /mnt/vfolder
```

**How `mountPropagation: Bidirectional` works**: The NFS Mounter Pod mounts NFS at `/mnt/vfolder` inside its mount namespace. With `Bidirectional` propagation, this mount is propagated back to the host's mount namespace. The Agent Pod and Docker daemon then see the NFS content at the host's `/mnt/vfolder`. When the NFS Mounter Pod restarts, it re-mounts and re-propagates.

Helm values for storage configuration:

```yaml
global:
  storage:
    nfsMounter:
      enabled: true           # false = host pre-mount (Option A)
    nfs:
      server: "nfs-server.internal"
      export: "/export/vfolder"
      mountPath: "/mnt/vfolder"
      mountOptions: "vers=4.1,hard,timeo=600,retrans=2,noresvport"
```

**Option comparison:**

| Aspect | Option A (host pre-mount) | Option B (NFS Mounter DaemonSet) |
|---|---|---|
| Controlled by | Infrastructure team | Helm chart |
| Node scaling | Manual NFS setup on new nodes | Automatic (DaemonSet deploys to new nodes) |
| Configuration change | SSH to each node | `helm upgrade` |
| Mount monitoring | Separate setup needed | Built-in livenessProbe + auto-remount |
| Agent restart impact | None (OS-level mount) | None (separate DaemonSet) |
| `helm install` self-contained? | No | **Yes** |
| NFS Mounter Pod restart | N/A | Remounts and propagates; kernel I/O briefly blocks if `hard` mount option is used (auto-recovers) |

### 4.7 GPU and Accelerator Passthrough

This section describes how GPU and accelerator passthrough works in a K8s DooD deployment, building on the assumptions established in Section 2.4 — Kubernetes does not manage GPU resources, and GPU nodes are isolated via taints.

#### 4.7.1 Two-Layer GPU Management

GPU management is split between two layers with clearly defined responsibilities:

```
┌─── K8s Layer (GPU-unaware) ───────────────────────────────────┐
│                                                                │
│  ❌ NVIDIA device plugin         — not deployed                │
│  ❌ nvidia.com/gpu resource      — meaningless on agent nodes  │
│  ✅ GPU Feature Discovery (GFD)  — node labeling only          │
│  ✅ NVIDIA driver installation   — via Operator (optional)     │
│  ✅ DCGM Exporter                — Prometheus metrics          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
         │
         │ nodeSelector: backendai.io/role=agent
         │ toleration: backendai.io/dedicated=agent:NoSchedule
         ▼
┌─── Backend.AI Layer (full GPU control) ──────────────────────┐
│                                                                │
│  Agent DaemonSet                                               │
│    ├── GPU device discovery (reads /dev/nvidia* directly)      │
│    ├── Driver library mount (/usr/lib/.../nvidia/*)            │
│    ├── GPU slot calculation → etcd registration                │
│    ├── Kernel container creation with GPU allocation           │
│    ├── CUDA hook library injection (fractional GPU)            │
│    └── GPU health monitoring (nvidia-smi, XID errors)          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

K8s is responsible for infrastructure prerequisites (driver install, node labeling, metrics export), but **never touches GPU allocation logic**. All GPU-related decisions are made by the Backend.AI Agent.

#### 4.7.2 NVIDIA Driver and Container Toolkit (Host-Level Prerequisite)

As established in Section 2.4.5, NVIDIA drivers and NVIDIA Container Toolkit are host-level prerequisites — not managed by K8s or Helm. This section clarifies the installation approach and explains the limited role of the NVIDIA GPU Operator.

##### 4.7.2.1 Host-Level Installation (Primary Approach)

Install NVIDIA drivers and Container Toolkit directly on each agent node before deploying Backend.AI:

```bash
# Ubuntu example
apt install nvidia-driver-535
apt install nvidia-container-toolkit
systemctl restart docker    # or containerd

# Verification
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

This approach has the following advantages over the GPU Operator's containerized driver installer:

| Aspect | Host installation | GPU Operator driver DaemonSet |
|---|---|---|
| Installation location | `/usr/lib/x86_64-linux-gnu/` (persistent disk) | `/run/nvidia/driver/` (tmpfs, memory) |
| After reboot | Immediately available | Reinstalled by DaemonSet (5-10 min delay) |
| Memory overhead | None | 500MB-1GB tmpfs per node |
| Debugging | Standard Linux tools | Requires inspecting DaemonSet Pod logs |
| Linux distro support | Any | Only officially supported distros |
| Secure Boot | Standard MOK enrollment | Additional operator configuration |
| Driver version control | Infrastructure team owns | Helm values + Operator reconciliation |
| Coupling to K8s | None | K8s Pod lifecycle affects driver state |

**Recommended deployment workflows:**

| Environment | Method | Artifacts |
|---|---|---|
| Bare-metal / on-premises | Packer + Ansible to build node images with drivers pre-installed | Custom OS image |
| AWS | AWS Deep Learning AMI (has drivers + toolkit pre-installed) | Amazon Linux 2 or Ubuntu DLAMI |
| GCP | GCP Deep Learning VM image or NVIDIA GPU-optimized COS | COS with pre-installed drivers |
| Azure | Azure N-series with NVIDIA drivers | N-series Ubuntu image |
| K3s/RKE2 | Use distribution's GPU-enabled installer | Native integration |

##### 4.7.2.2 NVIDIA GPU Operator (Optional Supplementary Tool)

NVIDIA GPU Operator can still be useful in a Backend.AI K8s deployment, but **only for supplementary components** — not for driver or toolkit installation. Use the Operator with most components disabled:

```yaml
# values.yaml (NVIDIA GPU Operator)
gpu-operator:
  driver:
    enabled: false          # ❌ Use host-level installation instead
  toolkit:
    enabled: false          # ❌ Use host-level installation instead
  devicePlugin:
    enabled: false          # ❌ Conflicts with Section 2.4.1 (Backend.AI manages GPUs)
  migManager:
    enabled: false          # ❌ Backend.AI handles MIG if needed
  gfd:
    enabled: true           # ✅ GPU Feature Discovery — auto-labels nodes with GPU info
  dcgmExporter:
    enabled: true           # ✅ Prometheus metrics for observability
  nodeStatusExporter:
    enabled: true           # ✅ Node health reporting
```

In this configuration, the Operator provides:

| Component | Purpose | Benefit |
|---|---|---|
| GPU Feature Discovery (GFD) | Labels nodes with `nvidia.com/gpu.product`, `nvidia.com/gpu.count`, `nvidia.com/gpu.memory` | Agent DaemonSet can use nodeSelector based on GPU model |
| DCGM Exporter | Exposes GPU metrics to Prometheus (utilization, temperature, memory, ECC errors) | Cluster-wide observability dashboards |
| Node Status Exporter | Reports GPU-related node conditions | Integration with K8s monitoring stack |

The Operator is **not required**. If GFD and DCGM metrics are not needed, the Operator can be skipped entirely — Backend.AI functions normally with only host-level drivers and toolkit.

##### 4.7.2.3 Why Not Use GPU Operator for Drivers?

The GPU Operator's driver installation is a clever but complex approach: it runs a privileged DaemonSet that compiles kernel modules inside a container and installs them to a host tmpfs path. While this works, it has significant operational drawbacks for production Backend.AI deployments:

1. **Reboot recovery is slow**: After a node reboot, the driver DaemonSet must reschedule, pull the driver image, compile modules, and install them. This takes 5-10 minutes, during which the node has no GPU access.
2. **Memory overhead**: Driver files stored in `/run/nvidia/driver` (tmpfs) consume 500MB-1GB of RAM per node permanently.
3. **Fragile dependency on kernel**: Any kernel upgrade requires the driver container to recompile. If the container's kernel source package is unavailable or incompatible, drivers fail to install.
4. **Unusual debugging path**: GPU issues must be diagnosed via `kubectl logs` on the driver Pod rather than standard host tools.
5. **Limited distro support**: Officially supported only on specific Ubuntu, RHEL, and SLES versions. Other distros (Arch, Debian minor versions, custom kernels) are not supported.
6. **Secure Boot complications**: Additional MOK (Machine Owner Key) management required for signed modules in containerized environments.
7. **Operator lifecycle coupling**: If the GPU Operator deployment is deleted or upgraded, driver state may become inconsistent.

For these reasons, Backend.AI deployments should treat NVIDIA drivers like any other host-level system software (kernel, Docker daemon, kubelet) — installed and managed at the node provisioning layer, not via K8s.

#### 4.7.3 Agent Pod GPU Access

The Backend.AI Agent Pod must access GPU devices and driver libraries for:

1. **GPU discovery at startup** — enumerate GPUs, read model and memory
2. **Health monitoring** — periodic `nvidia-smi` queries
3. **Resource slot calculation** — report GPU slots to etcd
4. **Allocation decisions** — determine which GPU to assign to each kernel container

Agent DaemonSet configuration with GPU access:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        backendai.io/role: agent
        nvidia.com/gpu.present: "true"      # GFD-provided label
      tolerations:
        - key: backendai.io/dedicated
          operator: Equal
          value: agent
          effect: NoSchedule
      containers:
        - name: agent
          securityContext:
            privileged: true
          env:
            - name: LD_LIBRARY_PATH
              value: "/usr/local/nvidia/lib64:/usr/local/nvidia/lib"
            - name: PATH
              value: "/usr/local/nvidia/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
          volumeMounts:
            # GPU device files (privileged grants access to all /dev/nvidia*)
            - name: dev
              mountPath: /dev
            # NVIDIA driver libraries from host
            - name: nvidia-driver
              mountPath: /usr/local/nvidia
              readOnly: true
      volumes:
        - name: dev
          hostPath:
            path: /dev
        - name: nvidia-driver
          hostPath:
            path: /run/nvidia/driver        # GPU Operator mount point
            type: Directory
```

**Alternative: NVIDIA CUDA base image for Agent**. Build the Agent image from `nvidia/cuda:12.x-base` and use NVIDIA Container Runtime. When the Agent Pod is created, the NVIDIA runtime automatically mounts driver libraries and devices into the container. This simplifies the Pod spec but requires the Agent image to match the host driver version at the CUDA level.

> **Tested variant (2026-04-21, see `todo.md` §5.6)**: The first real deployment used `runtimeClassName: nvidia` (K8s RuntimeClass → containerd nvidia runtime → `/usr/bin/nvidia-container-runtime`) on the Agent DaemonSet Pod — **without** switching the Agent base image to `nvidia/cuda`. The nvidia-container-runtime injects `/dev/nvidia*` and `libnvidia-ml.so.*` automatically, but does **not** inject `libcudart.so` into non-CUDA base images (the injection is gated on `ENV CUDA_VERSION` / `LABEL com.nvidia.cuda`). Because the `cuda_open` accelerator plugin needs `libcudart.so` for device discovery, the Tested variant additionally bind-mounts the host's `/usr/local/cuda` read-only and prepends it to `LD_LIBRARY_PATH`. Kernel containers (spawned via DooD) are unaffected — the plugin sets `HostConfig.Runtime=nvidia` on each `docker create` call, so the host's dockerd injects the full CUDA stack into the kernel container.

#### 4.7.4 Kernel Container GPU Allocation

Once the Agent is running with GPU access, kernel container GPU allocation works identically to the current bare-metal model. The Agent uses the Docker/containerd API directly to attach GPU devices, libraries, and environment variables to each kernel container.

| Feature | Mechanism | Compatibility |
|---|---|---|
| Single GPU allocation | `--device /dev/nvidia0` via Docker API | Identical to bare-metal |
| Multi-GPU allocation | Multiple `--device` flags or `--gpus '"device=0,1"'` | Identical to bare-metal |
| Fractional GPU (cuda.shares) | CUDA hook library injected via `generate_hooks()` + `LD_PRELOAD` | Requires hook library on host (see 4.7.5) |
| NVIDIA Container Toolkit | `--gpus all` flag or CDI device spec | Toolkit installed on host |
| MIG (Multi-Instance GPU) | MIG UUID injected as device | Requires host-level MIG partitioning (see 4.7.6) |
| NUMA-aware placement | CPU pinning + GPU affinity hint | Uses NUMA topology from host `/sys` |
| ROCm (AMD) | `/dev/kfd`, `/dev/dri/*` device files | Compute plugin determines devices |
| Habana, IPU, Rebellions, XPU | Plugin-specific device paths | Handled by respective compute plugins |

Because the Agent uses the same Docker/containerd API code path as bare-metal, **no changes are required to the accelerator plugin system**. The DooD architecture preserves the full feature set of Backend.AI's GPU management.

#### 4.7.5 Fractional GPU Hook Library Distribution

Backend.AI's fractional GPU sharing relies on a CUDA hook library (`libbaicuda.so`) injected via `LD_PRELOAD`. The Agent's `generate_hooks()` method returns the host path of this library, which is then bind-mounted into the kernel container.

In a K8s DooD deployment, the hook library must be available at a known path on the **host** filesystem. Three distribution options:

| Option | Description | Complexity | Version Management |
|---|---|---|---|
| **A. Agent image bundled** | Agent image contains the `.so` file; init container copies to hostPath | Low | Automatic with Agent upgrade |
| **B. Dedicated installer DaemonSet** | Separate DaemonSet distributes the library to the host | Medium | Independent of Agent version |
| **C. Node image pre-installed** | Library baked into node OS image | Medium | Requires node reprovisioning |

**Recommended: Option A (Agent image bundled).** The library version is automatically in sync with the Agent version, and Helm upgrades handle distribution:

```yaml
# Agent DaemonSet init container
initContainers:
  - name: install-cuda-hook
    image: "{{ .Values.agent.image.repository }}:{{ .Values.agent.image.tag }}"
    command:
      - sh
      - -c
      - |
        mkdir -p /host/opt/backendai/hooks
        cp /opt/backendai/hooks/libbaicuda.so /host/opt/backendai/hooks/
        chmod 755 /host/opt/backendai/hooks/libbaicuda.so
    volumeMounts:
      - name: host-backendai-hooks
        mountPath: /host/opt/backendai/hooks
volumes:
  - name: host-backendai-hooks
    hostPath:
      path: /opt/backendai/hooks
      type: DirectoryOrCreate
```

The Agent's `generate_hooks()` returns `/opt/backendai/hooks/libbaicuda.so`, which Docker bind-mounts into each kernel container. The kernel's `LD_PRELOAD` environment variable is set to load this library at startup.

#### 4.7.6 MIG Partitioning

Multi-Instance GPU (MIG) partitioning on NVIDIA H100/A100 requires host-level configuration that must happen **before** the Agent enumerates GPUs. Options for managing MIG partitions:

| Option | Description | Trade-off |
|---|---|---|
| **Node provisioning time** | MIG partitions set via cloud-init or Ansible during node bootstrap | Static — requires reprovisioning to change partition layout |
| **NVIDIA GPU Operator MIG Manager** | Operator's MIG Manager component | **Disabled** per Section 4.7.2 — couples with device plugin |
| **Manual nvidia-smi** | Cluster admin runs `nvidia-smi mig -cgi ...` per node | Operational burden |
| **Future: Backend.AI Agent dynamic MIG** | Agent partitions MIG based on allocation requests | Not currently implemented |

**Current recommendation**: Set MIG partitions statically at node provisioning time. The Agent detects MIG instances via `nvidia-smi -L` and registers each MIG UUID as a separate GPU slot in etcd. Kernel containers receive specific MIG UUIDs via the `NVIDIA_VISIBLE_DEVICES` environment variable.

#### 4.7.7 GPU Health Monitoring and Failure Handling

Unlike K8s-managed Pods, kernel container GPU failures are invisible to the K8s scheduler (by design — Section 2.4.1). The Backend.AI Agent is solely responsible for GPU health monitoring and recovery.

**Agent's GPU health loop:**

```
Every N seconds (configurable):
  1. Run `nvidia-smi -q` to query all GPUs
  2. Parse XID error counts, ECC errors, temperature, power state
  3. For each GPU:
     - If XID fatal error → mark slot as unavailable in etcd
     - If ECC uncorrectable error count growing → mark slot as degraded
     - If temperature > threshold → log warning, do not fail
  4. If all GPUs on node are unavailable:
     - Report zero GPU slots to Manager
     - Optionally call K8s API to cordon the node (requires RBAC)
     - Manager stops scheduling new sessions to this node
  5. Publish health events to Redis for Manager notification
```

**Interaction with K8s:**

- **DCGM Exporter** (from GPU Operator) publishes GPU metrics to Prometheus independently of the Agent's own monitoring. Cluster operators can use these metrics for dashboards, but the Agent does not consume them.
- **Node Problem Detector** (optional) can be configured to detect NVIDIA driver crashes and mark the K8s node as NotReady. This would evict the Agent Pod, but not kernel containers (they run via DooD).
- **Cordoning via K8s API** is optional. If the Agent has RBAC permission, it can call `kubectl cordon` equivalent to prevent new Pods (other Backend.AI DaemonSets, if any) from scheduling. This does NOT affect existing kernel containers.

**Recovery**: Manual driver reset (`nvidia-smi --gpu-reset`) or node reboot. The Agent re-enumerates GPUs on restart and rejoins the healthy GPU pool. Kernel containers holding a failed GPU must be terminated and rescheduled by the Manager.

#### 4.7.8 Compute Plugin Image Strategy

Backend.AI's accelerator plugins (`backendai_accelerator_cuda`, `backendai_accelerator_rocm`, `backendai_accelerator_xpu`, `backendai_accelerator_habana`, etc.) are loaded into the Agent process at startup. In a K8s deployment, there are two strategies for distributing these plugins via Agent images:

| Strategy | Description | Pros | Cons |
|---|---|---|---|
| **Single unified image** | One Agent image contains all plugins; runtime detects hardware and activates the appropriate plugin | Single image to manage; simpler Helm values | Larger image size; unused plugins loaded |
| **Per-vendor images** | Separate images: `backendai-agent-cuda`, `backendai-agent-rocm`, `backendai-agent-xpu` | Smaller images; clearer dependencies | Image matrix management overhead; requires node-type-specific DaemonSet selection |

**Recommended: Single unified image**. The size overhead is minimal (plugin code is small compared to CUDA/ROCm libraries), and the simpler deployment model reduces operational complexity. The Agent detects available hardware at startup via:

1. Node labels (`nvidia.com/gpu.product`, `amd.com/gpu.family`) if GFD or similar is deployed
2. Direct hardware probing (`lspci`, `/dev/nvidia*`, `/dev/kfd`)
3. Configuration in `agent.toml` or environment variables

For heterogeneous clusters (e.g., NVIDIA H100 nodes + AMD MI300 nodes), per-vendor DaemonSets with nodeSelectors can be used if strict image separation is required:

```yaml
# values.yaml
agent:
  daemonsets:
    - name: agent-nvidia
      nodeSelector:
        nvidia.com/gpu.present: "true"
      image:
        tag: "25.12.0-cuda"
    - name: agent-amd
      nodeSelector:
        amd.com/gpu.present: "true"
      image:
        tag: "25.12.0-rocm"
```

This approach requires Helm templating to generate multiple DaemonSets from a single values configuration.

#### 4.7.9 VM-Based Isolation Alternatives (External Document)

For environments requiring stronger isolation than DooD containers provide — multi-tenant scenarios with untrusted code, regulatory compliance, confidential computing — VM-based isolation runtimes (Kata Containers, KubeVirt) must be supported alongside the default DooD architecture.

Because VM runtime support involves substantial architectural considerations, GPU constraints, operational strategies, and a 12-layer system-wide change set, it is documented in a **dedicated companion document**:

**📄 [Backend.AI VM Runtime Support: Kata Containers and KubeVirt](./support_vm_kata.md)**

That document covers:

- **Background**: Why VM isolation must be supported alongside DooD (security, compliance, confidential computing)
- **Runtime options**: Kata Containers vs KubeVirt vs DooD comparison
- **GPU + VM constraints**: Why Firecracker cannot be used, why VM pooling fails for GPUs, GPU cold start reality (30 seconds to several minutes)
- **Operational strategies**: Runtime class selection per session, dedicated GPU pools, NVIDIA vGPU/MIG integration, per-GPU driver binding for hybrid nodes
- **Hybrid runtime architecture**: Multi-runtime cluster design with taint-based pool separation
- **System-wide changes**: 55 required changes across 12 architectural layers (Agent core, kernel communication, GPU allocation, storage, networking, image management, scheduler, node infrastructure, monitoring, Helm, API/CLI/UI, test infrastructure)
- **Phased implementation roadmap**: 4-phase approach over 12-18 months
- **Decision gate**: Criteria to evaluate before committing to VM runtime support

**Key takeaways for this document's context:**

| Aspect | Status |
|---|---|
| VM runtime support required | Yes (for security/compliance scenarios) |
| Default runtime | DooD (preserved for general workloads) |
| Implementation impact | 12-18 months, 2-3 engineers, 12-layer changes |
| Compatible with current 4.7.1-4.7.8 design | Yes (DooD remains primary, VM runtimes are opt-in) |

---

## 5. Container Runtime Analysis: Docker vs containerd

### 5.1 DooD with Docker (docker.sock)

In this model, the host runs the Docker daemon (`dockerd`), and the agent pod mounts `/var/run/docker.sock`:

```
Agent Pod ──(docker.sock)──▶ dockerd ──▶ containerd ──▶ runc ──▶ Kernel Container
```

The Backend.AI agent uses the `aiodocker` library, which communicates with the Docker Engine API (REST over Unix socket). This is the current production model.

**Advantages:**
- **Zero agent code changes**: The existing `DockerAgent` implementation works as-is.
- **Docker Compose compatibility**: Development and testing workflows using Docker Compose remain functional.
- **Docker Swarm overlay**: Multi-node session networking via Docker Swarm overlay networks is a proven, production-validated feature.
- **Mature tooling**: `docker exec`, `docker logs`, `docker stats` for debugging and operations.
- **Image management**: `docker pull`, `docker build`, `docker tag` — well-understood lifecycle.
- **NVIDIA Container Toolkit**: Full integration via `nvidia-docker2` or `nvidia-container-toolkit` packages.

**Disadvantages:**
- **Additional daemon**: Docker daemon (`dockerd`) is an additional process on the node, adding memory overhead (50-100MB) and a potential single point of failure.
- **Layered architecture**: Docker → containerd → runc adds latency to container operations.
- **K8s CRI conflict**: Modern K8s (1.24+) uses containerd directly as CRI. Running Docker alongside means two container runtimes on the same node, with potential confusion about which runtime manages which containers.
- **Dockershim removal**: Kubernetes removed dockershim in 1.24. Docker is no longer a first-class K8s runtime, though it can still run as a standalone daemon for DooD purposes.
- **Attack surface**: Docker daemon runs as root with broad capabilities; compromising the socket grants full host access.

### 5.2 DooD with containerd (containerd.sock)

In this model, the agent communicates directly with containerd (which K8s already uses as its CRI runtime):

```
Agent Pod ──(containerd.sock)──▶ containerd ──▶ runc ──▶ Kernel Container
```

The agent would use a containerd client library (e.g., `containerd` Python bindings via gRPC, or the `nerdctl` CLI as a Docker-compatible interface).

**Advantages:**
- **Single runtime**: containerd is already running on every K8s node. No additional daemon needed.
- **Lower overhead**: One less daemon process (no `dockerd`), saving 50-100MB memory per node.
- **Native K8s alignment**: Containers created via containerd can optionally be placed in a separate namespace (e.g., `backendai.io`) to avoid interference with K8s-managed containers.
- **Simpler architecture**: Agent → containerd → runc (one fewer layer).
- **Security**: containerd socket has a smaller attack surface than Docker socket. Fine-grained namespace isolation is possible.
- **CDI (Container Device Interface)**: containerd natively supports CDI for standardized device (GPU) management, which is the future direction for NVIDIA container integration.

**Disadvantages:**
- **Agent code changes required**: The `DockerAgent` uses `aiodocker` (Docker Engine API). Switching to containerd requires either:
  - Rewriting container management to use containerd's gRPC API (significant effort).
  - Using `nerdctl` as a Docker-compatible CLI wrapper around containerd for development and debugging convenience (moderate effort, but adds a CLI dependency). Note that `nerdctl` is a development/debugging convenience, not a production dependency. For production, the agent should use containerd's async gRPC API directly or the CRI gRPC API, avoiding CLI wrapper dependencies.
  - Using CRI (Container Runtime Interface) gRPC API directly (moderate effort).
- **No Swarm overlay**: containerd does not have Docker Swarm's built-in overlay network. Multi-node session networking would require an alternative (e.g., CNI plugins, WireGuard, or a custom overlay solution).
- **Image management differences**: containerd uses namespaced image stores. Image pull/tag operations differ from Docker CLI conventions.
- **NVIDIA Container Toolkit**: Supported via CDI or `nvidia-ctk` runtime configuration, but the integration path differs from the Docker-based model.
- **Debugging UX**: `ctr` and `nerdctl` are less ergonomic than `docker` CLI for debugging.

### 5.3 Feature Parity Matrix

| Feature | Docker (docker.sock) | containerd (containerd.sock) | Gap Assessment |
|---|---|---|---|
| Container create/start/stop/remove | Full (Docker Engine API) | Full (containerd gRPC / CRI) | Parity |
| Container exec | Full (`docker exec`) | Full (`ctr tasks exec` / CRI ExecSync) | Parity |
| Container logs (stdout/stderr) | Full (Docker API stream) | Full (containerd log API) | Parity |
| Container stats (CPU, memory, I/O) | Full (Docker API stream) | Full (containerd metrics API) | Parity |
| Image pull/push/tag | Full (Docker API) | Full (containerd API, different semantics) | Minor difference (namespaces) |
| Image build | Full (`docker build`) | Via BuildKit (standalone) or `nerdctl build` | Equivalent (BuildKit) |
| Bind mounts | Full | Full | Parity |
| GPU device mapping | Full (`--gpus`, `--device`) | Full (CDI, `--device`) | Parity (CDI preferred) |
| CPU/memory limits | Full (cgroup) | Full (cgroup) | Parity |
| Network: bridge | Full (docker0 bridge) | Full (CNI bridge plugin) | Parity |
| Network: overlay (multi-node) | Full (Docker Swarm overlay) | **Not built-in** | **Significant gap** |
| Network: host | Full (`--net=host`) | Full (host namespace) | Parity |
| NVIDIA Container Toolkit | Full (nvidia-docker2) | Full (CDI / nvidia-ctk) | Parity |
| CUDA hook library injection | Full (OCI hooks via Docker) | Full (OCI hooks via containerd) | Parity |
| Container labels/annotations | Full | Full (labels on containerd containers) | Parity |
| Health checks | Full (Docker HEALTHCHECK) | Not built-in (application-level) | Minor gap |
| Docker Compose | Full | Via `nerdctl compose` | Parity (with nerdctl) |
| Container restart policies | Full | Limited (application-level) | Minor gap |
| Python client library | aiodocker (mature, async) | No mature async Python library | **Significant gap** |

### 5.4 Performance Comparison

| Metric | Docker | containerd | Delta |
|---|---|---|---|
| Container create latency | ~200-300ms | ~150-250ms | containerd ~20% faster (no dockerd hop) |
| Container start latency | ~100-200ms | ~80-150ms | containerd ~20% faster |
| Memory overhead (daemon) | ~50-100MB (dockerd) + containerd | containerd only (~30-50MB) | containerd saves ~50-100MB per node |
| Image pull throughput | Equivalent | Equivalent | Parity (both use containerd under the hood for Docker) |
| Container exec latency | ~50ms | ~30ms | containerd ~40% faster |
| I/O performance (bind mounts) | Native | Native | Parity (both use runc) |
| GPU compute performance | Native | Native | Parity (VFIO/CDI passthrough) |

The performance differences are modest. For Backend.AI's use case (long-running AI/ML sessions), the container creation latency difference (50-100ms) is negligible compared to session setup time (image pull, storage mount, GPU initialization).

### 5.5 Security Comparison

| Aspect | Docker | containerd | Assessment |
|---|---|---|---|
| Socket access = root | Yes (docker.sock = full root) | Yes (containerd.sock = full root) | Equivalent risk |
| Namespace isolation | Single namespace | Multi-namespace (K8s, backendai) | containerd better |
| Attack surface | Larger (Docker API + containerd) | Smaller (containerd only) | containerd better |
| Rootless mode | Supported (rootless Docker) | Supported (rootless containerd) | Parity |
| Seccomp profiles | Full | Full | Parity |
| AppArmor/SELinux | Full | Full | Parity |
| Image signing verification | Docker Content Trust | containerd + cosign/notation | Parity |

**Key security consideration**: In both models, the agent pod must have access to the container runtime socket, which effectively grants root-equivalent access to the node. This is an inherent trade-off of the DooD model. Mitigations include:
- Restricting which nodes the agent DaemonSet runs on (nodeSelector, taints/tolerations)
- Using K8s RBAC to limit which ServiceAccounts can create DaemonSets
- Network policies to restrict agent pod communication
- PodSecurityAdmission policies for non-agent workloads

### 5.6 Operational Complexity

| Aspect | Docker | containerd | Assessment |
|---|---|---|---|
| Node setup | Install Docker + configure | Already present (K8s CRI) | containerd simpler |
| Agent deployment | Mount docker.sock | Mount containerd.sock | Parity |
| Debugging | `docker ps`, `docker logs`, `docker exec` | `nerdctl`/`ctr` (less familiar) | Docker easier |
| Monitoring | Docker stats API, cAdvisor | containerd metrics, cAdvisor | Parity |
| Multi-node networking | Docker Swarm (built-in) | Requires separate solution | Docker easier |
| Image registry auth | `~/.docker/config.json` | containerd config.toml | Docker easier |
| Upgrade path | Docker releases independently | containerd upgraded with K8s | containerd simpler |
| Coexistence with K8s | Two runtimes on node | Single runtime | containerd simpler |

### 5.7 Runtime Selection Recommendation

#### Recommendation: **Docker for initial deployment; containerd as long-term target**

**Phase 1 (Immediate): Docker-based DooD**

- **Rationale**: Zero agent code changes. The existing `DockerAgent` + `aiodocker` stack works immediately. Docker Swarm overlay networking for multi-node sessions is production-proven. The GPU integration path (`nvidia-docker2`, `generate_docker_args()`, `generate_hooks()`) is unchanged.
- **Deployment**: Install Docker daemon on K8s worker nodes alongside containerd (K8s uses containerd for its pods; Backend.AI uses Docker for kernel containers).
- **Trade-off**: Two container runtimes on the same node. Acceptable for initial deployment where operational simplicity and speed of delivery are priorities.
- **Network performance**: Docker Swarm overlay is already used in the current bare-metal deployment for multi-node sessions. Moving to K8s with Docker DooD does not change the networking path — kernel containers use the same Swarm overlay as before. There is no network performance regression compared to the current production deployment.

**Phase 2 (Medium-term): containerd Runtime + Isolated CNI Networking**

- **Rationale**: Eliminates dual-runtime complexity by switching container management to containerd, but avoids the risks of sharing K8s CNI with non-Pod containers. Uses a separate CNI configuration with its own IP address range, completely independent of the K8s pod network.
- **Required work**:
  1. Develop a `ContainerdAgent` implementation using containerd's async gRPC API (not nerdctl CLI).
  2. Configure a separate CNI network for Backend.AI kernel containers (`--cni-netconfpath` pointing to a dedicated config directory with its own IPAM/CIDR).
  3. For cross-node kernel communication, use a dedicated VXLAN overlay (e.g., standalone Flannel instance) or route traffic through AppProxy.
  4. Migrate GPU device mapping to CDI (Container Device Interface).
  5. Validate CUDA hook library injection via containerd's OCI hook support.
- **Key advantage**: Zero risk of K8s IPAM conflicts, NetworkPolicy interference, or kubelet GC cleaning up unknown endpoints. The Backend.AI network is fully isolated from K8s networking.
- **Estimated effort**: 3-4 months of engineering work.

**Phase 3 (Long-term): CNI Native Integration**

- **Rationale**: Full integration with the K8s CNI (Calico/Cilium) for DooD kernel containers, providing unified routing, policy enforcement, and observability across K8s pods and Backend.AI kernels.
- **Three possible approaches** (choose based on organizational standards):

  | Approach | Mechanism | Pros | Cons |
  |---|---|---|---|
  | **CNI direct invocation** | Small Go helper daemon invokes CNI ADD/DEL on kernel container netns. Uses a dedicated IP pool/block to avoid IPAM conflicts with K8s pods. | Simplest integration; reuses existing CNI infra | No NetworkPolicy for non-Pod endpoints; requires GC daemon for orphaned endpoints |
  | **Calico/Cilium native** | Register non-Pod endpoints via Calico WorkloadEndpoint CRD or Cilium endpoint API. | Full policy/observability parity with K8s pods | Product/version-dependent; requires CRD/operator integration |
  | **CRI-based PodSandbox** | Agent creates PodSandbox-like entities via CRI API, letting containerd invoke CNI naturally. | Most "K8s-native"; kubelet-compatible lifecycle | Highest implementation complexity; risk of kubelet state conflicts |

- **Operational requirements for all approaches**:
  - **IPAM isolation**: Dedicated CIDR/IP block for Backend.AI kernel containers. Never share the same IP pool with K8s pods.
  - **Endpoint GC**: Agent restart/crash recovery must reconcile network state — clean up orphaned veth pairs, release leaked IPs via CNI DEL.
  - **Observability**: Service exposure should go through AppProxy, not direct NodePort mapping, to maintain consistent routing and visibility.
- **Estimated effort**: 6-12 months depending on approach chosen.

**Decision matrix by deployment scenario:**

| Scenario | Recommended Runtime | Rationale |
|---|---|---|
| Existing Docker-based deployment migrating to K8s | Docker | Zero migration risk; proven stack |
| New greenfield K8s deployment (single-node sessions only) | containerd | Simpler; no Swarm dependency |
| New deployment requiring multi-node sessions | Docker | Swarm overlay is the simplest multi-node solution |
| Edge deployment with minimal resources | containerd | Lower memory overhead |
| Air-gapped / high-security environment | containerd | Smaller attack surface, single runtime |

### 5.8 CNI Integration Strategy for containerd DooD

When transitioning from Docker to containerd, the most critical challenge is not the container runtime itself but **networking**. Docker Swarm provides a built-in overlay network that "just works" for multi-node sessions. containerd has no equivalent — networking must be explicitly designed.

#### 5.8.1 Why Sharing K8s CNI is Risky

Directly invoking the K8s CNI (Calico/Cilium) for non-Pod containers introduces several risks that are not immediately obvious:

| Risk | Description | Severity |
|---|---|---|
| kubelet GC interference | kubelet periodically garbage-collects network resources for containers it does not know about. Non-Pod endpoints may be cleaned up unexpectedly. | High |
| NetworkPolicy gaps | K8s NetworkPolicy is enforced based on Pod labels/selectors. Non-Pod endpoints have no K8s metadata, so policies either don't apply or apply incorrectly (e.g., Cilium classifies them as "world" identity). | Medium |
| IPAM leak on crash | If the agent crashes without calling CNI DEL, the allocated IP is leaked until manual cleanup. kubelet handles this automatically for its own pods. | High |
| State inconsistency | The CNI plugin's internal state (Calico's WorkloadEndpoint, Cilium's eBPF map) may become inconsistent with actual container state after agent restarts. | Medium |

#### 5.8.2 Recommended Phased Approach

```
Phase 2: containerd + Isolated CNI
    ┌──────────────────────────────────────────────────────────┐
    │  K8s CNI (Calico/Cilium)     Backend.AI CNI (separate)  │
    │  ┌──────────────┐            ┌────────────────────┐     │
    │  │ Pod CIDR:    │            │ BAI CIDR:          │     │
    │  │ 10.244.0.0/16│            │ 172.30.0.0/16      │     │
    │  │              │            │                    │     │
    │  │ K8s pods     │            │ Kernel containers  │     │
    │  │ (managed by  │            │ (managed by Agent  │     │
    │  │  kubelet)    │            │  via containerd)   │     │
    │  └──────────────┘            └────────────────────┘     │
    │         ▲                            ▲                   │
    │         │                            │                   │
    │    K8s CNI config              Separate CNI config       │
    │    /etc/cni/net.d/             /etc/cni/backendai.d/     │
    └──────────────────────────────────────────────────────────┘

Phase 3: Unified CNI (Calico/Cilium native integration)
    ┌──────────────────────────────────────────────────────────┐
    │  Unified CNI (Calico/Cilium)                             │
    │  ┌────────────────────────────────────────────────┐      │
    │  │ K8s Pod pool:  10.244.0.0/16                   │      │
    │  │ BAI pool:      10.244.128.0/17 (dedicated)     │      │
    │  │                                                │      │
    │  │ K8s pods + Kernel containers                   │      │
    │  │ (unified routing, policy, observability)       │      │
    │  └────────────────────────────────────────────────┘      │
    │                      ▲                                    │
    │                      │                                    │
    │              Single CNI with                              │
    │              dedicated IP pools                           │
    └──────────────────────────────────────────────────────────┘
```

#### 5.8.3 Implementation Sketch: CNI Direct Invocation Helper

For Phase 3 CNI integration, a dedicated Go helper daemon manages the network lifecycle for kernel containers:

```
Agent ──(gRPC)──▶ CNI Helper Daemon ──(CNI API)──▶ Calico/Cilium
                        │
                        ├── Maintains endpoint registry
                        ├── Handles CNI ADD/DEL
                        ├── Runs periodic GC (reconcile with running containers)
                        └── Exposes IP/route info back to Agent
```

The helper daemon is responsible for:
- Receiving container PID from Agent after container creation
- Creating veth pair and attaching to container netns
- Invoking CNI ADD with dedicated IP pool configuration
- Tracking all managed endpoints in a local state file
- On startup: reconciling state with running containers and cleaning up orphans
- On Agent restart signal: running CNI DEL for terminated containers

---

## 6. Control Plane Installation (Helm)

This section describes the Helm-based installation strategy for the Backend.AI control plane on Kubernetes. The key challenge is **service discovery bootstrapping**: each component needs to know the addresses of its dependencies at startup, and these addresses must remain stable across Pod restarts.

### 6.1 Dependency Chain and Bootstrap Order

Each Backend.AI component has different dependency requirements:

```
┌─── Infrastructure (no Backend.AI dependencies) ───────────────┐
│                                                                │
│  etcd          PostgreSQL          Redis                       │
│  (must start   (must start         (must start                 │
│   first)        first)              first)                     │
│                                                                │
└──────────┬───────────┬───────────────┬─────────────────────────┘
           │           │               │
           ▼           ▼               ▼
┌─── Manager (needs all three) ─────────────────────────────────┐
│                                                                │
│  Reads from:                                                   │
│    - etcd:       BACKEND_ETCD_ADDR  (env var)                  │
│    - PostgreSQL: BACKEND_DB_ADDR    (env var)                  │
│    - Redis:      [redis] addr       (toml / env var)           │
│                                                                │
│  Writes to etcd:                                               │
│    - announce-addr (K8s Service DNS)                           │
│    - announce-internal-addr (K8s Service DNS)                  │
│    - cluster configuration                                     │
│                                                                │
└──────────┬─────────────────────────────────────────────────────┘
           │
           ▼
┌─── Agent (needs only etcd) ───────────────────────────────────┐
│                                                                │
│  Reads from:                                                   │
│    - etcd:       BACKEND_ETCD_ADDR  (env var)                  │
│                                                                │
│  Discovers via etcd:                                           │
│    - Manager announce-addr                                     │
│    - Redis addr                                                │
│    - Cluster configuration                                     │
│                                                                │
│  Writes to etcd:                                               │
│    - advertised-rpc-addr (host node IP)                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Critical insight**: The Manager needs etcd + DB + Redis addresses at startup. The Agent needs only the etcd address — everything else is discovered from etcd at runtime.

### 6.2 Service Discovery Architecture

All inter-component discovery relies on **K8s Service DNS names** as stable endpoints. These DNS names are deterministic based on the Helm release and never change across Pod restarts.

```
┌─── K8s Service DNS (stable, deterministic) ────────────────────────────┐
│                                                                         │
│  backendai-etcd.backendai-system.svc.cluster.local:2379                │
│  backendai-pg-rw.backendai-system.svc.cluster.local:5432               │
│  backendai-redis.backendai-system.svc.cluster.local:6379               │
│  backendai-manager.backendai-system.svc.cluster.local:8080             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─ etcd ─────────┐  ┌─ Manager ──────────┐  ┌─ Agent ───────────────────┐
│                 │  │                     │  │                           │
│ env var:        │  │ env vars:           │  │ env var:                  │
│  etcd addr      │  │  etcd addr          │  │  BACKEND_ETCD_ADDR       │
│  (from Helm     │  │  DB addr            │  │  (from Helm values)      │
│   values)       │  │  Redis addr         │  │                           │
│                 │  │  (from Helm values)  │  │ Registers in etcd:       │
│ Registers:      │  │                     │  │  advertised-rpc-addr     │
│  (self, quorum) │  │ Registers in etcd:  │  │  = NODE_IP:6001          │
│                 │  │  announce-addr      │  │  (via K8s Downward API)  │
│                 │  │  = K8s Service DNS  │  │                           │
└─────────────────┘  └─────────────────────┘  └───────────────────────────┘
```

**Address registration summary:**

| Component | Registered in etcd as | Value in K8s | Who resolves it |
|---|---|---|---|
| Manager `announce-addr` | K8s Service DNS | `backendai-manager.backendai-system.svc:8080` | Agent |
| Manager `announce-internal-addr` | K8s Service DNS | `backendai-manager.backendai-system.svc:18080` | Agent, Storage Proxy |
| Agent `advertised-rpc-addr` | Host node IP | `192.168.1.100:6001` (via Downward API) | Manager |
| Agent `advertised-host` (for kernels) | Host node IP | `192.168.1.100` (via Downward API) | Kernel containers |

### 6.3 Helm Chart Structure

```
backendai/                              # Umbrella chart
├── Chart.yaml
├── values.yaml                         # Global configuration
├── charts/
│   ├── etcd/                           # Subchart (or dependency: bitnami/etcd)
│   ├── postgresql/                     # Subchart (or dependency: cnpg-cluster)
│   ├── redis/                          # Subchart (or dependency: bitnami/redis)
│   ├── manager/                        # Backend.AI Manager
│   │   ├── Chart.yaml
│   │   └── templates/
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       ├── configmap.yaml
│   │       └── _helpers.tpl
│   ├── agent/                          # Backend.AI Agent
│   │   ├── Chart.yaml
│   │   └── templates/
│   │       ├── daemonset.yaml
│   │       └── _helpers.tpl
│   ├── storage-proxy/                  # Backend.AI Storage Proxy
│   │   └── templates/
│   │       └── deployment.yaml
│   ├── app-proxy/                      # Backend.AI App Proxy
│   │   ├── Chart.yaml
│   │   └── templates/
│   │       ├── coordinator-deployment.yaml
│   │       ├── worker-deployment.yaml
│   │       ├── service.yaml
│   │       └── _helpers.tpl
│   └── webserver/                      # Backend.AI Web Server
│       └── templates/
│           ├── deployment.yaml
│           └── ingress.yaml
└── templates/
    ├── namespace.yaml
    ├── secrets.yaml                    # Shared secrets (DB, etcd, Redis credentials)
    └── _helpers.tpl                    # Common DNS name generation helpers
```

**External chart dependencies** (in `Chart.yaml`):

```yaml
# Chart.yaml
apiVersion: v2
name: backendai
version: 1.0.0
dependencies:
  - name: etcd
    version: "10.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: etcd.enabled
  - name: postgresql
    version: "1.x.x"
    repository: "https://cloudnative-pg.github.io/charts"
    condition: postgresql.enabled
    alias: postgresql
  - name: redis
    version: "19.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
```

Setting `etcd.enabled=false`, `postgresql.enabled=false`, or `redis.enabled=false` allows use of externally managed instances (e.g., AWS RDS, ElastiCache, managed etcd).

### 6.4 Global Values Configuration

The `values.yaml` is the single source of truth for all service addresses:

```yaml
# values.yaml
global:
  namespace: backendai-system

  # ── etcd ──────────────────────────────────────────────────
  # This is the bootstrap entry point. Both Manager and Agent
  # need this address. Everything else is discovered via etcd
  # (for Agent) or via additional env vars (for Manager).
  etcd:
    host: "backendai-etcd.backendai-system.svc"
    port: 2379
    namespace: "backend"        # etcd key prefix for Backend.AI
    auth:
      user: "root"
      existingSecret: "backendai-etcd-credentials"
      secretKey: "password"

  # ── PostgreSQL ────────────────────────────────────────────
  # Only Manager needs this directly.
  db:
    host: "backendai-pg-rw.backendai-system.svc"   # CloudNativePG read-write service
    port: 5432
    name: "backend"
    auth:
      user: "backend"
      existingSecret: "backendai-db-credentials"
      secretKey: "password"

  # ── Redis ─────────────────────────────────────────────────
  # Manager reads from config; Agent discovers from etcd.
  redis:
    host: "backendai-redis-master.backendai-system.svc"
    port: 6379
    auth:
      existingSecret: "backendai-redis-credentials"
      secretKey: "password"

  # ── Manager announce addresses ────────────────────────────
  # These are written to etcd so agents can discover the manager.
  # Must be K8s Service DNS names (stable across Pod restarts).
  manager:
    announceAddr:
      host: "backendai-manager.backendai-system.svc"
      port: 8080
    announceInternalAddr:
      host: "backendai-manager.backendai-system.svc"
      port: 18080

  # ── AppProxy announce addresses ──────────────────────────────
  appProxy:
    coordinator:
      announceAddr:
        host: "backendai-appproxy-coordinator.backendai-system.svc"
        port: 8070
    worker:
      announceAddr:
        host: "backendai-appproxy-worker.backendai-system.svc"
        port: 8071

# ── Manager subchart ──────────────────────────────────────────
manager:
  replicas: 2
  image:
    repository: lablup/backend.ai-manager
    tag: "25.12.0"

# ── Agent subchart ────────────────────────────────────────────
agent:
  image:
    repository: lablup/backend.ai-agent
    tag: "25.12.0"
  nodeSelector:
    backendai.io/role: agent
  containerRuntime: docker          # "docker" or "containerd"
  rpcPort: 6001

# ── External chart overrides ──────────────────────────────────
etcd:
  enabled: true
  replicaCount: 3
  persistence:
    size: 10Gi
    storageClass: fast-ssd

postgresql:
  enabled: true
  # CloudNativePG Cluster spec
  instances: 3
  storage:
    size: 50Gi
    storageClass: fast-ssd

redis:
  enabled: true
  architecture: standalone          # or "replication" for HA
  master:
    persistence:
      size: 8Gi
```

### 6.5 Component Environment Variable Injection

#### 6.5.1 Manager Deployment Template

The Manager needs all three infrastructure addresses:

```yaml
# charts/manager/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backendai-manager
spec:
  replicas: {{ .Values.replicas }}
  template:
    spec:
      initContainers:
        - name: wait-for-etcd
          image: bitnami/etcd:3.5
          command: ['sh', '-c',
            'until etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} endpoint health 2>/dev/null; do echo "etcd not healthy yet..."; sleep 3; done']
        - name: wait-for-db
          image: postgres:16-alpine
          command: ['sh', '-c',
            'until pg_isready -h {{ .Values.global.db.host }} -p {{ .Values.global.db.port }} -U {{ .Values.global.db.auth.user }}; do echo "db not ready yet..."; sleep 3; done']
        - name: wait-for-redis
          image: redis:7-alpine
          command: ['sh', '-c',
            'until redis-cli -h {{ .Values.global.redis.host }} -p {{ .Values.global.redis.port }} ping 2>/dev/null | grep -q PONG; do echo "redis not ready yet..."; sleep 3; done']
      containers:
        - name: manager
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          env:
            # ── etcd ──
            - name: BACKEND_ETCD_ADDR
              value: "{{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }}"
            - name: BACKEND_NAMESPACE
              value: "{{ .Values.global.etcd.namespace }}"
            - name: BACKEND_ETCD_USER
              value: "{{ .Values.global.etcd.auth.user }}"
            - name: BACKEND_ETCD_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.etcd.auth.existingSecret }}"
                  key: "{{ .Values.global.etcd.auth.secretKey }}"
            # ── PostgreSQL ──
            - name: BACKEND_DB_ADDR
              value: "{{ .Values.global.db.host }}:{{ .Values.global.db.port }}"
            - name: BACKEND_DB_NAME
              value: "{{ .Values.global.db.name }}"
            - name: BACKEND_DB_USER
              value: "{{ .Values.global.db.auth.user }}"
            - name: BACKEND_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.db.auth.existingSecret }}"
                  key: "{{ .Values.global.db.auth.secretKey }}"
            # ── Manager announce addresses (written to etcd) ──
            - name: BACKEND_MANAGER_ANNOUNCE_ADDR
              value: "{{ .Values.global.manager.announceAddr.host }}:{{ .Values.global.manager.announceAddr.port }}"
            - name: BACKEND_MANAGER_ANNOUNCE_INTERNAL_ADDR
              value: "{{ .Values.global.manager.announceInternalAddr.host }}:{{ .Values.global.manager.announceInternalAddr.port }}"
          volumeMounts:
            - name: manager-config
              mountPath: /etc/backend.ai/manager.toml
              subPath: manager.toml
      volumes:
        - name: manager-config
          configMap:
            name: backendai-manager-config
```

#### 6.5.2 Agent DaemonSet Template

The Agent needs only the etcd address — Manager and Redis addresses are discovered from etcd at runtime:

```yaml
# charts/agent/templates/daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: backendai-agent
spec:
  template:
    spec:
      hostNetwork: true
      nodeSelector:
        {{- toYaml .Values.nodeSelector | nindent 8 }}
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      priorityClassName: backendai-agent-critical
      initContainers:
        - name: wait-for-etcd
          image: bitnami/etcd:3.5
          command: ['sh', '-c',
            'until etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} endpoint health 2>/dev/null; do echo "etcd not healthy yet..."; sleep 3; done']
      containers:
        - name: agent
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          securityContext:
            privileged: true
          env:
            # ── etcd (the only bootstrap dependency) ──
            - name: BACKEND_ETCD_ADDR
              value: "{{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }}"
            - name: BACKEND_NAMESPACE
              value: "{{ .Values.global.etcd.namespace }}"
            - name: BACKEND_ETCD_USER
              value: "{{ .Values.global.etcd.auth.user }}"
            - name: BACKEND_ETCD_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.etcd.auth.existingSecret }}"
                  key: "{{ .Values.global.etcd.auth.secretKey }}"
            # ── Agent host address override (node IP via Downward API) ──
            # The agent with hostNetwork:true binds to 0.0.0.0 by default,
            # which would register the wrong address in etcd. These overrides
            # ensure the agent advertises the node's actual host IP.
            - name: BACKEND_AGENT_HOST_OVERRIDE
              valueFrom:
                fieldRef:
                  fieldPath: status.hostIP
            - name: BACKEND_BIND_HOST_OVERRIDE
              valueFrom:
                fieldRef:
                  fieldPath: status.hostIP
            # ── Container runtime backend ──
            - name: BACKEND_AGENT_BACKEND
              value: "docker"
          volumeMounts:
            {{- if eq .Values.containerRuntime "docker" }}
            - name: container-runtime-socket
              mountPath: /var/run/docker.sock
            {{- else }}
            - name: container-runtime-socket
              mountPath: /run/containerd/containerd.sock
            {{- end }}
            - name: scratch-space
              mountPath: /var/cache/scratches
            - name: vfolder-storage
              mountPath: /vfolder
      volumes:
        - name: container-runtime-socket
          hostPath:
            {{- if eq .Values.containerRuntime "docker" }}
            path: /var/run/docker.sock
            {{- else }}
            path: /run/containerd/containerd.sock
            {{- end }}
            type: Socket
        - name: scratch-space
          hostPath:
            path: /var/cache/backendai/scratches
            type: DirectoryOrCreate
        - name: vfolder-storage
          hostPath:
            path: /mnt/vfolder
            type: Directory
```

**Note on PriorityClass**: The `system-node-critical` priority class is reserved for core Kubernetes components (kubelet, kube-proxy). A custom PriorityClass should be created for the Backend.AI agent:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: backendai-agent-critical
value: 1000000
globalDefault: false
description: "Priority class for Backend.AI agent DaemonSet pods"
```

### 6.6 Boot Sequence and Init Containers

Helm does not guarantee deployment order within a single release. All resources are applied simultaneously. The boot sequence is enforced at the Pod level via **init containers**:

```
┌─ Helm install (all resources applied at once) ─────────────────────┐
│                                                                     │
│  etcd StatefulSet    ──▶ Pods start, form quorum                   │
│  PostgreSQL          ──▶ Pods start, become ready                  │
│  Redis               ──▶ Pods start, become ready                  │
│                                                                     │
│  Manager Deployment  ──▶ init containers wait for etcd/DB/Redis    │
│                          ──▶ main container starts after all ready  │
│                                                                     │
│  Agent DaemonSet     ──▶ init container waits for etcd             │
│                          ──▶ main container starts                  │
│                          ──▶ reads manager addr from etcd          │
│                              (retries until manager has registered) │
└─────────────────────────────────────────────────────────────────────┘
```

**Why init containers are sufficient:**

1. **etcd, PostgreSQL, Redis**: These are infrastructure services with no Backend.AI dependencies. They start immediately and become ready within seconds.
2. **Manager**: Init containers block until all three infrastructure services are reachable. The Manager then starts and registers its `announce-addr` in etcd.
3. **Agent**: Init container blocks until etcd is reachable. The Agent starts and reads Manager address from etcd. If the Manager has not yet registered, the Agent's existing retry logic handles this (it periodically re-reads the Manager endpoint from etcd).

**Why native client health checks instead of `nc -z` port checks:**

Simple TCP port checks (`nc -z`) can pass even when the service is not truly ready. Each init container uses a native client that validates actual service readiness:

| Service | Check Tool | What it validates | Why `nc -z` is insufficient |
|---|---|---|---|
| etcd | `etcdctl endpoint health` | Quorum formed, read/write capable | etcd listens on port before quorum — writes fail until quorum is established |
| PostgreSQL | `pg_isready` | Connection accepting, recovery complete | PostgreSQL opens the TCP port during startup recovery — queries fail until recovery finishes |
| Redis | `redis-cli ping` → `PONG` | Command processing, memory loaded | Redis binds the port before loading AOF/RDB — commands timeout until data is loaded |

> **Alternative approach — application-level retries with probes**: Instead of init containers with infinite wait loops, an alternative is to rely on Kubernetes `startupProbe` and `readinessProbe` combined with application-level retry logic. The Manager and Agent already implement connection retry for etcd and Redis. The init container approach is simpler to reason about and ensures clean startup ordering, but in production environments where init container image pull adds latency, the probe-based approach may be preferred. Both approaches are valid; choose based on operational preference.

### 6.7 Installation Commands

#### 6.7.1 Prerequisites

```bash
# Create namespace
kubectl create namespace backendai-system

# Create secrets (before Helm install)
kubectl create secret generic backendai-etcd-credentials \
  --from-literal=password='<ETCD_PASSWORD>' \
  -n backendai-system

kubectl create secret generic backendai-db-credentials \
  --from-literal=password='<DB_PASSWORD>' \
  -n backendai-system

kubectl create secret generic backendai-redis-credentials \
  --from-literal=password='<REDIS_PASSWORD>' \
  -n backendai-system
```

#### 6.7.1a vFolder Storage Path Initialization

vfolder storage mount paths and etcd volume configuration keys must be initialized before the first agent startup. This can be done via a Helm post-install hook or a manual `etcdctl put` step:

```bash
# Initialize vfolder storage mount configuration in etcd
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl put /backend/volumes/_mount /mnt/vfolder
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl put /backend/volumes/_fsprefix ""
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl put /backend/volumes/_default_host "local:volume1"
```

#### 6.7.2 Install

```bash
# Install everything with a single Helm command
helm install backendai ./backendai \
  -n backendai-system \
  --create-namespace \
  -f values.yaml

# Or with external infrastructure (e.g., managed DB)
helm install backendai ./backendai \
  -n backendai-system \
  --set postgresql.enabled=false \
  --set global.db.host=my-rds-instance.region.rds.amazonaws.com \
  --set global.db.port=5432
```

#### 6.7.3 Verify

```bash
# Check all Pods are running
kubectl get pods -n backendai-system

# Expected output:
# NAME                                  READY   STATUS    RESTARTS
# backendai-etcd-0                      1/1     Running   0
# backendai-etcd-1                      1/1     Running   0
# backendai-etcd-2                      1/1     Running   0
# backendai-pg-1                        1/1     Running   0
# backendai-pg-2                        1/1     Running   0
# backendai-pg-3                        1/1     Running   0
# backendai-redis-master-0              1/1     Running   0
# backendai-manager-xxxx-yyy            1/1     Running   0
# backendai-manager-xxxx-zzz            1/1     Running   0
# backendai-agent-node1                 1/1     Running   0
# backendai-agent-node2                 1/1     Running   0

# Verify Manager registered in etcd
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl get /backend/manager --prefix

# Verify Agent registered in etcd
kubectl exec -n backendai-system backendai-etcd-0 -- \
  etcdctl get /backend/agents --prefix
```

#### 6.7.4 Upgrade

```bash
# Rolling upgrade (e.g., new Manager image)
helm upgrade backendai ./backendai \
  -n backendai-system \
  --set manager.image.tag="25.13.0"

# Agent rolling update is handled by DaemonSet update strategy
# Kernel containers are NOT affected (DooD — they run on the host)
```

### 6.8 Container Image Management

In the DooD architecture, there are **two independent image pull paths** that must be configured separately:

```
┌─── Image Registry (e.g., Harbor) ────────────────────────────┐
│                                                               │
│  backendai/manager:25.12.0        ← kubelet pulls            │
│  backendai/agent:25.12.0          ← kubelet pulls            │
│  backendai/webserver:25.12.0      ← kubelet pulls            │
│  backendai/kernel-python:3.11     ← Agent pulls (Docker API) │
│  backendai/kernel-pytorch:2.1     ← Agent pulls (Docker API) │
│                                                               │
└───────────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │                                    │
   K8s imagePullSecrets              etcd registry config
   (Helm values)                    (Manager API / etcd)
```

#### 6.8.1 Dual Image Pull Architecture

| Aspect | Control Plane Images | Kernel Images |
|---|---|---|
| **Examples** | `manager`, `agent`, `webserver`, `app-proxy` | `kernel-python:3.11`, `kernel-pytorch:2.1` |
| **Pull agent** | kubelet | Backend.AI Agent (via Docker/containerd API) |
| **Authentication** | K8s `imagePullSecrets` | etcd `registry_conf` (username/password) |
| **Configuration** | Helm `values.yaml` | Backend.AI Manager API or etcd |
| **Lifecycle** | Updated via `helm upgrade` | Updated via Backend.AI image management |

The Agent pull implementation (`src/ai/backend/agent/docker/agent.py`) reads registry credentials from etcd and passes them directly to the Docker API:

```python
reg_user = registry_conf.get("username")
reg_passwd = registry_conf.get("password")
auth_config = {"auth": base64.b64encode(f"{reg_user}:{reg_passwd}".encode()).decode("ascii")}
await docker.images.pull(image_ref.canonical, auth=auth_config)
```

This means K8s `imagePullSecrets` have **no effect** on kernel image pulls — the Agent bypasses kubelet entirely.

#### 6.8.2 Registry Credential Synchronization

When using a private registry (e.g., Harbor) for both control plane and kernel images, credentials must be configured in **two places**:

1. **K8s Secret** (for kubelet): `imagePullSecrets` in Helm values
2. **etcd** (for Agent): Registry username/password via Manager API

To avoid managing credentials in two places, use a **Helm post-install/post-upgrade hook** to synchronize K8s Secret credentials into etcd automatically:

```yaml
# templates/jobs/sync-registry-creds.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-sync-registry-creds
  annotations:
    helm.sh/hook: post-install,post-upgrade
    helm.sh/hook-weight: "-5"
    helm.sh/hook-delete-policy: hook-succeeded
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: sync
          image: bitnami/etcd:3.5
          command: ['sh', '-c', |
            etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} \
              put /{{ .Values.global.etcd.namespace }}/config/docker/registry/{{ .Values.global.imageRegistry.host }}/username "$REG_USER"
            etcdctl --endpoints={{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }} \
              put /{{ .Values.global.etcd.namespace }}/config/docker/registry/{{ .Values.global.imageRegistry.host }}/password "$REG_PASS"
          ]
          env:
            - name: REG_USER
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.global.imageRegistry.existingSecret }}
                  key: username
            - name: REG_PASS
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.global.imageRegistry.existingSecret }}
                  key: password
```

Add the corresponding values to `values.yaml`:

```yaml
global:
  imageRegistry:
    host: "harbor.internal"
    existingSecret: "harbor-credentials"   # K8s Secret with username/password keys
  imagePullSecrets:
    - harbor-credentials                   # For kubelet (control plane images)
```

This way, registry credentials are managed in a **single K8s Secret**, and the Helm hook synchronizes them to etcd for the Agent on every install/upgrade.

#### 6.8.3 Air-Gapped Deployment

In air-gapped environments without external registry access:

| Image Type | Pre-loading Strategy |
|---|---|
| Control Plane | `docker load` or `ctr image import` on each node, set `imagePullPolicy: IfNotPresent` |
| Kernel | `docker load` on each agent node (loaded into host Docker daemon for DooD access) |

For kernel images in air-gapped mode, set `auto_pull` to `NONE` in Backend.AI configuration to prevent the Agent from attempting to pull images from an unreachable registry. All kernel images must be pre-loaded on each agent node's Docker daemon.

#### 6.8.4 Credential Rotation Procedure

When registry credentials change:

1. Update the K8s Secret:
   ```bash
   kubectl create secret docker-registry harbor-credentials \
     --docker-server=harbor.internal \
     --docker-username=NEW_USER \
     --docker-password=NEW_PASS \
     -n backendai-system --dry-run=client -o yaml | kubectl apply -f -
   ```
2. Run Helm upgrade to trigger the sync hook:
   ```bash
   helm upgrade backendai ./backendai -n backendai-system
   ```
3. Verify etcd has updated credentials:
   ```bash
   kubectl exec -n backendai-system backendai-etcd-0 -- \
     etcdctl get /backend/config/docker/registry/harbor.internal/username
   ```

---

### 6.9 Database Migration Strategy (Alembic)

Backend.AI uses Alembic for database schema migrations. In a K8s deployment where image updates trigger Pod recreation, migrations must run **before** the new Manager Pod starts. Otherwise, the new code references columns or tables that don't exist yet, causing immediate startup failure.

#### 6.9.1 The Problem

```
helm upgrade (manager image 25.12.0 → 25.13.0)
    │
    ├── New Manager Pod created (25.13.0 code)
    │     → DB schema is still at 25.12.0
    │     → New code references missing columns/tables
    │     → CRASH
    │
    └── Migration must run BEFORE new Pod starts
```

#### 6.9.2 Solution: Helm Pre-Upgrade Hook

A Kubernetes Job runs the Alembic migration using the **new** Manager image before the Manager Deployment is updated:

```yaml
# templates/jobs/db-migrate.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migrate
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
    helm.sh/hook-weight: "0"
    helm.sh/hook-delete-policy: before-hook-creation
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      initContainers:
        - name: wait-for-db
          image: postgres:16-alpine
          command: ['sh', '-c',
            'until pg_isready -h {{ .Values.global.db.host }} -p {{ .Values.global.db.port }} -U {{ .Values.global.db.auth.user }}; do echo "db not ready..."; sleep 3; done']
      containers:
        - name: migrate
          image: "{{ .Values.manager.image.repository }}:{{ .Values.manager.image.tag }}"
          command: ["python", "-m", "ai.backend.manager.cli", "schema", "oneshot"]
          env:
            - name: BACKEND_DB_ADDR
              value: "{{ .Values.global.db.host }}:{{ .Values.global.db.port }}"
            - name: BACKEND_DB_NAME
              value: "{{ .Values.global.db.name }}"
            - name: BACKEND_DB_USER
              value: "{{ .Values.global.db.auth.user }}"
            - name: BACKEND_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.db.auth.existingSecret }}"
                  key: "{{ .Values.global.db.auth.secretKey }}"
            - name: BACKEND_ETCD_ADDR
              value: "{{ .Values.global.etcd.host }}:{{ .Values.global.etcd.port }}"
```

AppProxy Coordinator also has its own database and Alembic migrations:

```yaml
# templates/jobs/db-migrate-appproxy.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migrate-appproxy
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
    helm.sh/hook-weight: "1"
    helm.sh/hook-delete-policy: before-hook-creation
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      initContainers:
        - name: wait-for-db
          image: postgres:16-alpine
          command: ['sh', '-c',
            'until pg_isready -h {{ .Values.global.db.host }} -p {{ .Values.global.db.port }} -U {{ .Values.global.db.auth.user }}; do echo "db not ready..."; sleep 3; done']
      containers:
        - name: migrate
          image: "{{ .Values.appProxy.coordinator.image.repository }}:{{ .Values.appProxy.coordinator.image.tag }}"
          command: ["python", "-m", "ai.backend.app_proxy.coordinator.cli", "schema", "oneshot"]
          env:
            - name: BACKEND_DB_ADDR
              value: "{{ .Values.global.db.host }}:{{ .Values.global.db.port }}"
            - name: BACKEND_DB_NAME
              value: "appproxy"
            - name: BACKEND_DB_USER
              value: "{{ .Values.global.db.auth.user }}"
            - name: BACKEND_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: "{{ .Values.global.db.auth.existingSecret }}"
                  key: "{{ .Values.global.db.auth.secretKey }}"
```

#### 6.9.3 Helm Hook Execution Order

All Helm hooks execute in `hook-weight` order before the main resources are updated:

```
helm install/upgrade
    │
    │  hook-weight: -5
    ├── sync-registry-creds Job       (K8s Secret → etcd sync)
    │
    │  hook-weight: 0
    ├── db-migrate Job                (Manager DB: alembic upgrade head)
    │
    │  hook-weight: 1
    ├── db-migrate-appproxy Job       (AppProxy DB: alembic upgrade head)
    │
    │  hook-weight: 5
    ├── init-etcd-volumes Job         (etcd vfolder config initialization)
    │
    │  (all hooks completed successfully)
    ├── Manager Deployment updated    (new image, schema already current)
    ├── AppProxy Deployment updated
    ├── Agent DaemonSet updated
    └── Other components updated
```

If any hook Job fails (e.g., migration error), Helm aborts the upgrade and no Deployments are updated. This prevents deploying new code against an incompatible schema.

#### 6.9.4 Rollback Considerations

```
helm rollback backendai 1
    │
    ├── Manager image rolls back: 25.13.0 → 25.12.0
    │
    └── DB schema remains at 25.13.0 (Helm rollback does NOT run migrations)
```

Alembic migrations in Backend.AI are **forward-only** by default. Rollback behavior depends on the migration type:

| Migration Type | Rollback Safety | Action Required |
|---|---|---|
| Column additions | **Safe** — old code ignores unknown columns | No action needed |
| New tables | **Safe** — old code doesn't reference them | No action needed |
| Column renames | **Unsafe** — old code references old column name | Manual `alembic downgrade` required |
| Column deletions | **Unsafe** — old code references deleted column | Manual `alembic downgrade` required |
| Data transformations | **Unsafe** — data format may be incompatible | Manual assessment + downgrade required |

**Rollback procedure for unsafe migrations:**

```bash
# 1. Identify the target Alembic revision for the old version
kubectl exec -n backendai-system deploy/backendai-manager -- \
  python -m ai.backend.manager.cli schema show-revision

# 2. Run manual downgrade (use the OLD image)
kubectl run db-downgrade --rm -it \
  --image=backendai/manager:25.12.0 \
  -n backendai-system -- \
  python -m ai.backend.manager.cli schema downgrade <target-revision>

# 3. Then perform Helm rollback
helm rollback backendai 1 -n backendai-system
```

> **Best practice**: Before any upgrade, record the current Alembic revision. This enables targeted downgrade if rollback is needed. Consider adding a pre-upgrade hook that saves the current revision to a ConfigMap for reference.

### 6.10 Redis High Availability

Backend.AI already supports Redis Sentinel for high availability. The K8s deployment must provide a Redis HA setup that is compatible with the existing Sentinel-based client code.

#### 6.10.1 Options Comparison

| Option | Pod Count | Failover | Backend.AI Compatible | Operational Complexity | Best For |
|---|---|---|---|---|---|
| **Bitnami Helm (Sentinel)** | **3** (master+replica+sentinel in each Pod) | Sentinel auto-failover | Full (existing Sentinel support) | Low | On-premises, single cluster |
| **Redis Operator (Spotahome)** | **7** (1 operator + 3 Redis + 3 Sentinel) | Operator + Sentinel | Full | Medium | Multi-cluster, platform teams |
| **Managed Redis** | 0 (cloud-managed) | Cloud provider managed | Full (single endpoint or Sentinel) | Lowest | Cloud deployments (AWS, GCP, Azure) |
| **Redis Cluster** | 6+ (3 masters + 3 replicas) | Built-in cluster failover | **Not supported** (requires client changes) | High | Not recommended |

#### 6.10.2 Recommended: Bitnami Helm Chart (Sentinel Mode)

The simplest option with full Backend.AI compatibility. Sentinel runs as a sidecar in each Redis Pod, requiring only **3 Pods** total:

```
┌─── Redis StatefulSet (Bitnami Helm) ──────────────────────┐
│                                                            │
│  backendai-redis-node-0  (master + sentinel sidecar)       │
│  backendai-redis-node-1  (replica + sentinel sidecar)      │
│  backendai-redis-node-2  (replica + sentinel sidecar)      │
│                                                            │
│  K8s Services:                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ backendai-redis.svc:6379       → master (read-write) │  │
│  │ backendai-redis-headless.svc   → all nodes           │  │
│  │ backendai-redis.svc:26379      → sentinel port       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

Helm values:

```yaml
redis:
  enabled: true
  architecture: replication

  sentinel:
    enabled: true
    quorum: 2

  master:
    persistence:
      size: 8Gi
      storageClass: fast-ssd

  replica:
    replicaCount: 2

  auth:
    existingSecret: backendai-redis-credentials
    existingSecretPasswordKey: password
```

#### 6.10.3 Alternative: Redis Operator (Spotahome)

For organizations that prefer operator-managed infrastructure. The operator watches a `RedisFailover` CRD and automatically manages Redis topology, rolling upgrades, and recovery:

```
┌─── Redis Operator Deployment ─────────────────────────────┐
│                                                            │
│  Operator Pod (1)          ← watches RedisFailover CRD     │
│                                                            │
│  Redis Pods:                                               │
│    redis-0 (master)                                        │
│    redis-1 (replica)                                       │
│    redis-2 (replica)                                       │
│                                                            │
│  Sentinel Pods:                                            │
│    sentinel-0                                              │
│    sentinel-1                                              │
│    sentinel-2                                              │
│                                                            │
│  Total: 7 Pods                                             │
└────────────────────────────────────────────────────────────┘
```

```yaml
apiVersion: databases.spotahome.com/v1
kind: RedisFailover
metadata:
  name: backendai-redis
  namespace: backendai-system
spec:
  sentinel:
    replicas: 3
  redis:
    replicas: 3
    storage:
      persistentVolumeClaim:
        metadata:
          name: redis-data
        spec:
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 8Gi
```

**Operator advantages over Bitnami Helm:**

| Scenario | Bitnami Helm | Redis Operator |
|---|---|---|
| Pod deleted by K8s | Sentinel handles failover; manual topology check may be needed | Operator automatically reconciles to desired state |
| Redis version upgrade | `helm upgrade` with manual validation | Operator manages rolling update |
| Persistent storage issue | Manual intervention | Operator detects and recreates |
| Configuration drift | Possible after manual changes | Operator continuously reconciles |

#### 6.10.4 Alternative: Managed Redis (Cloud)

For cloud deployments, managed Redis eliminates all operational overhead:

| Cloud Provider | Service | Sentinel Compatible | Configuration |
|---|---|---|---|
| AWS | ElastiCache for Redis | Yes (cluster mode disabled) | Single primary endpoint |
| GCP | Memorystore for Redis | Yes (Standard tier) | Single endpoint with auto-failover |
| Azure | Azure Cache for Redis | Yes (Premium tier) | Single endpoint with auto-failover |

With managed Redis, set `redis.enabled=false` in Helm values and configure the external endpoint:

```yaml
redis:
  enabled: false

global:
  redis:
    host: "my-redis.xxxx.cache.amazonaws.com"
    port: 6379
    # No sentinel config needed — managed Redis handles failover internally
```

#### 6.10.5 Backend.AI Sentinel Configuration

Regardless of the Redis HA option chosen (Bitnami or Operator), the Backend.AI Manager and Agent need Sentinel connection details. Since Sentinel requires multiple host entries (`[[redis.sentinel]]` TOML array), this is best provided via a ConfigMap rather than environment variables:

```yaml
# ConfigMap for Manager
apiVersion: v1
kind: ConfigMap
metadata:
  name: backendai-manager-redis-config
data:
  redis.toml: |
    [redis]
    service-name = "mymaster"

    [[redis.sentinel]]
    host = "backendai-redis-node-0.backendai-redis-headless.backendai-system.svc"
    port = 26379

    [[redis.sentinel]]
    host = "backendai-redis-node-1.backendai-redis-headless.backendai-system.svc"
    port = 26379

    [[redis.sentinel]]
    host = "backendai-redis-node-2.backendai-redis-headless.backendai-system.svc"
    port = 26379
```

**Failover behavior:**

```
Normal:
  Client → Sentinel (query master addr) → connect to master

Master failure:
  1. Sentinels detect master down (quorum: 2/3 agree)
  2. One replica promoted to new master
  3. Other replicas follow new master
  4. Client re-queries Sentinel → connects to new master

  → Backend.AI redis_helper already supports Sentinel protocol
    — automatic master discovery and reconnection on failover
```

---

## 7. Detailed Component Design

### 7.1 Control Plane Pod Specifications

#### 7.1.1 Manager Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backendai-manager
  namespace: backendai-system
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    spec:
      containers:
        - name: manager
          image: lablup/backend.ai-manager:latest
          ports:
            - containerPort: 8080    # API
              name: api
            - containerPort: 8090    # RPC (agent communication)
              name: rpc
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          envFrom:
            - configMapRef:
                name: backendai-manager-config
            - secretRef:
                name: backendai-manager-secrets
          livenessProbe:
            httpGet:
              path: /func/health
              port: api
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /func/health
              port: api
            initialDelaySeconds: 10
            periodSeconds: 5
```

#### 7.1.2 PostgreSQL StatefulSet

Recommended approach: Use **CloudNativePG operator** for production-grade PostgreSQL on K8s.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: backendai-pg
  namespace: backendai-system
spec:
  instances: 3
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "512MB"
  storage:
    size: 50Gi
    storageClass: fast-ssd
  backup:
    barmanObjectStore:
      destinationPath: "s3://backendai-backup/pg"
```

#### 7.1.3 etcd StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: backendai-etcd
  namespace: backendai-system
spec:
  serviceName: backendai-etcd
  replicas: 3
  template:
    spec:
      containers:
        - name: etcd
          image: quay.io/coreos/etcd:v3.5
          ports:
            - containerPort: 2379
              name: client
            - containerPort: 2380
              name: peer
          volumeMounts:
            - name: data
              mountPath: /var/run/etcd
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 10Gi
```

### 7.2 Agent DaemonSet Design

#### 7.2.1 Resource Reservation

The agent DaemonSet must reserve resources on each node to ensure the agent pod always has sufficient CPU and memory, even under heavy kernel workload:

```yaml
resources:
  requests:
    cpu: "500m"       # Reserved for agent process
    memory: "1Gi"     # Reserved for agent process
  limits:
    cpu: "2"          # Agent can burst during scheduling operations
    memory: "4Gi"     # Agent caches image metadata, kernel state
```

K8s will not schedule other K8s pods into the agent's reserved resources. However, kernel containers (managed outside K8s) compete for the node's remaining resources. The Backend.AI agent must account for its own reserved resources when calculating `available_slots`.

#### 7.2.2 Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 6009
  initialDelaySeconds: 60
  periodSeconds: 30
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /health
    port: 6009
  initialDelaySeconds: 15
  periodSeconds: 10
```

#### 7.2.3 Agent Shutdown and Kernel Orphan Management

When the agent pod is restarted (rolling update, node drain, OOM kill), kernel containers continue running on the host since they are not managed by K8s:

- **Graceful shutdown**: Agent receives SIGTERM, performs `pre_stop` cleanup, persists kernel registry state to etcd.
- **Recovery on restart**: New agent pod reads kernel registry from etcd, reconnects to existing kernel containers (`DockerKernelRegistryRecovery`).
- **Orphan detection**: On startup, agent scans running containers with `ai.backend.` labels and reconciles with its persisted state.

This is identical to the current bare-metal recovery behavior — the DooD model does not change kernel recovery semantics.

### 7.3 Kernel Container Management

#### 7.3.1 Container Labels

All kernel containers must be labeled for identification and management:

```json
{
  "ai.backend.kernel-id": "<kernel-uuid>",
  "ai.backend.session-id": "<session-uuid>",
  "ai.backend.agent-id": "<agent-id>",
  "ai.backend.managed-by": "backendai-agent",
  "ai.backend.cluster": "<k8s-cluster-name>"
}
```

#### 7.3.2 Resource Isolation

Kernel containers use Linux cgroups (via Docker/containerd) for resource isolation:

- **CPU**: `--cpus`, `--cpuset-cpus` for pinning
- **Memory**: `--memory`, `--memory-swap`
- **GPU**: `--gpus`, `--device /dev/nvidia*`, or CDI device spec
- **I/O**: Block I/O limits via cgroup blkio controller

### 7.4 Service Discovery and Communication

| Communication Path | Mechanism |
|---|---|
| Manager → Agent | ZeroMQ over K8s Service (agent `hostNetwork` IP) |
| Agent → Manager | ZeroMQ to K8s Service (ClusterIP) for manager |
| Agent → etcd | gRPC to K8s Service (ClusterIP) for etcd |
| Agent → Redis | TCP to K8s Service (ClusterIP) for Redis |
| Agent → PostgreSQL | TCP to K8s Service (ClusterIP) for PostgreSQL |
| Agent → Kernel | Docker/containerd API via socket + kernel TCP ports |
| Kernel → Agent | TCP to host IP (agent `hostNetwork`) |
| Kernel → Kernel (same node) | Docker bridge network |
| Kernel → Kernel (cross-node) | Docker Swarm overlay / alternative overlay |

---

## 8. Migration Path from Current Architecture

### 8.1 Agent Code Changes Required

| Change | Effort | Description |
|---|---|---|
| Configuration source | Low | Read config from K8s ConfigMap/Secret (env vars) instead of toml file. The agent already supports env var configuration. |
| Manager address resolution | Low | Use K8s Service DNS name instead of static IP. |
| Node resource detection | Low | Agent detects host resources (not pod resources). Ensure `/proc`, `/sys` from host are accessible or use `hostPID` for resource detection. |
| Scratch space paths | Low | Ensure scratch paths are consistent between agent pod mounts and kernel container bind mounts. |
| Network plugin | Medium | Docker overlay network setup may need adaptation for K8s-managed nodes. |
| Kernel recovery | None | Existing `DockerKernelRegistryRecovery` works as-is. |
| GPU detection | Low | Ensure NVIDIA device plugin labels are used for node selection; agent's own GPU detection uses host `/dev/nvidia*`. |

**Total estimated effort for Docker-based DooD: 2-4 weeks**

### 8.2 Manager Code Changes Required

| Change | Effort | Description |
|---|---|---|
| Agent discovery | Medium | Currently agents register via etcd heartbeat. This works unchanged in K8s. Optionally, enhance with K8s-native service discovery. |
| Health monitoring | Low | Agent health checks work unchanged over ZeroMQ. |
| Resource scheduling | Low | No changes — Sokovan scheduler uses agent-reported slots. |
| API server | None | Manager API is unchanged; K8s Ingress handles external routing. |

**Total estimated effort: 1-2 weeks**

### 8.3 Configuration Changes

| Current Config | K8s Equivalent |
|---|---|
| `agent.toml` | ConfigMap + Secret |
| `manager.toml` | ConfigMap + Secret |
| etcd connection string | K8s Service DNS |
| PostgreSQL connection string | K8s Service DNS + Secret |
| Redis connection string | K8s Service DNS |
| Docker daemon address | hostPath socket mount |
| Storage mount paths | hostPath volume mounts |

---

## 9. Risk Analysis

### 9.1 Technical Risks

| Risk | Probability | Impact | Description |
|---|---|---|---|
| K8s resource accounting mismatch | High | Medium | K8s does not know about kernel containers. Node may be over-committed from K8s perspective. |
| Docker Swarm + K8s coexistence | Medium | Medium | Docker Swarm and K8s CNI on the same node may have IP range conflicts. |
| Agent pod eviction | Medium | High | If K8s evicts the agent pod (resource pressure), kernel containers become orphaned until agent restarts. |
| Host path permissions | Medium | Low | Agent pod needs correct UID/GID mapping to access host paths. |
| GPU device plugin conflict | Medium | Medium | K8s NVIDIA device plugin allocates GPUs to K8s pods. Agent allocates GPUs to kernel containers. Potential double-allocation. |
| Network port conflicts | Low | Medium | Kernel container port mappings may conflict with K8s NodePort range (30000-32767). |

### 9.2 Operational Risks

| Risk | Probability | Impact | Description |
|---|---|---|---|
| Debugging complexity | High | Low | Two layers of container management (K8s for agent, Docker for kernels) increases debugging complexity. |
| Log aggregation | Medium | Low | Kernel container logs are in Docker/containerd, not in K8s logging pipeline. Requires separate log collection. |
| Monitoring gaps | Medium | Medium | K8s monitoring (Prometheus, metrics-server) does not see kernel containers. Backend.AI's own monitoring fills the gap. |
| Node drain behavior | Medium | High | `kubectl drain` evicts the agent pod but not kernel containers. Custom drain procedure required. |

### 9.3 Mitigation Strategies

**K8s resource accounting mismatch:**
- Reserve a fixed portion of node resources for K8s system pods (kubelet, kube-proxy, agent, monitoring).
- Configure the agent to report `total_slots - k8s_reserved` as available slots.
- Use K8s `allocatable` minus DaemonSet requests as the base for Backend.AI slot calculation.

**GPU device plugin conflict:**
- **Option A**: Do not deploy the NVIDIA K8s device plugin on agent nodes. Let Backend.AI manage all GPU allocation.
- **Option B**: Deploy device plugin but taint agent nodes to prevent K8s GPU workloads. Backend.AI agent ignores the device plugin and manages GPUs directly.
- **Recommended**: Option A — do not deploy NVIDIA device plugin on Backend.AI agent nodes.

**Agent pod eviction:**
- Set `PriorityClass` to `backendai-agent-critical` for the agent DaemonSet (see Section 6.5.2 for the custom PriorityClass definition).
- Configure appropriate resource requests to prevent eviction under memory pressure.

**Node drain procedure:**
- Create a custom drain script:
  1. Cordon the node (prevent new sessions).
  2. Wait for all Backend.AI sessions to complete or migrate.
  3. `kubectl drain` to evict agent and system pods.

---

## 10. Alternative Approaches

### 10.1 Pure K8s-native (Kernels as Pods)

Instead of DooD, run each kernel session as a K8s Pod:

| Aspect | Assessment |
|---|---|
| GPU allocation | Limited to K8s device plugin model (whole GPU only, no fractional via CUDA hooks) |
| Multi-GPU | Supported via K8s resource requests |
| Fractional GPU | **Not supported** natively; requires NVIDIA MPS/MIG at K8s level |
| Networking | K8s CNI; no Docker Swarm overlay for multi-node sessions |
| Storage | K8s PV/PVC; lose direct bind mount flexibility |
| Agent code impact | Requires full rewrite of kernel lifecycle management |
| K8s visibility | Full — kernel pods visible in K8s, proper resource accounting |

**Verdict**: Significant feature regressions (fractional GPU, overlay networking) and massive engineering effort. Not recommended for near-term.

### 10.2 Hybrid: Agent on Host + Control Plane on K8s

Run only the control plane on K8s; agents remain on bare-metal/VM hosts:

| Aspect | Assessment |
|---|---|
| Agent management | Manual (Ansible, systemd) — no change from current |
| Control plane | K8s-managed — operational benefits |
| Kernel lifecycle | Unchanged (Docker on host) |
| Code changes | Minimal (manager config for K8s Service discovery) |

**Verdict**: Lowest risk, lowest effort, but does not gain K8s agent lifecycle management benefits. Good intermediate step.

### 10.3 K8s Operator Pattern

Build a Backend.AI K8s Operator that manages Custom Resources (BackendAISession, BackendAIAgent):

| Aspect | Assessment |
|---|---|
| K8s integration | Deepest — fully K8s-native |
| GPU allocation | Depends on implementation (can use device plugin + MIG, or DooD within operator pods) |
| Engineering effort | Very high (6-12 months for production-grade operator) |
| Operational model | K8s-native CRUD via kubectl / K8s API |

**Verdict**: Best long-term architecture but requires significant investment. Consider as a future evolution.

---

## 11. Required Experiments

This section defines experiments that must be conducted to validate key architectural assumptions before committing to the proposed design. Each experiment targets a specific risk or unverified claim.

### 11.1 EXP-1: CNI Direct Invocation for DooD Containers

| Field | Value |
|---|---|
| **Objective** | Verify that a non-K8s container created via containerd/Docker DooD can be assigned a Pod-network IP by directly invoking the host's CNI plugin binary |
| **Priority** | Critical |
| **Blocking** | containerd DooD feasibility for multi-node sessions |

**Hypothesis**: CNI plugins (Calico, Cilium) are standalone binaries conforming to the CNI spec. They can be invoked by any process — not just kubelet — to configure networking for a container's network namespace.

**Procedure**:

1. Set up a 2-node K8s cluster with Calico (or Cilium) as CNI.
2. On Node A, create a container via `nerdctl` (containerd) or `docker run` with `--net=none` (no automatic networking).
3. Obtain the container's PID and network namespace path (`/proc/<pid>/ns/net`).
4. Invoke the CNI plugin binary directly:
   ```bash
   export CNI_COMMAND=ADD
   export CNI_CONTAINERID=test-kernel-001
   export CNI_NETNS=/proc/<pid>/ns/net
   export CNI_IFNAME=eth0
   export CNI_PATH=/opt/cni/bin
   cat /etc/cni/net.d/10-calico.conflist | /opt/cni/bin/calico
   ```
5. Verify: container receives an IP from the pod CIDR, `ip route` on host shows a route to the container, `ping` from another K8s pod on the same node succeeds.
6. Clean up: invoke `CNI_COMMAND=DEL` and verify IP is returned to IPAM pool.

**Success Criteria**:
- Container gets a valid IP from the CNI IPAM pool
- Container is reachable from K8s pods on the same node
- IP is properly released on `CNI_COMMAND=DEL`
- No errors in calico-node / cilium-agent logs

**Critical precaution**: Use a **dedicated IP pool/CIDR** for DooD containers, separate from the K8s pod IP range. For Calico, create a dedicated `IPPool` resource. For Cilium, configure a separate `--cluster-pool-ipv4-cidr` range. Never share the same IPAM pool between kubelet-managed pods and agent-managed kernel containers.

**Failure Implications**: If CNI direct invocation does not work, the containerd DooD path requires a custom networking solution (WireGuard, manual VXLAN) for multi-node sessions.

---

### 11.2 EXP-2: CNI IPAM Coexistence with K8s Pods

| Field | Value |
|---|---|
| **Objective** | Verify that CNI-assigned IPs for DooD containers do not conflict with IPs assigned to K8s-managed pods |
| **Priority** | Critical |
| **Blocking** | Safe coexistence of DooD kernel containers and K8s pods on the same node |

**Hypothesis**: CNI IPAM (Calico IPAM, Cilium IPAM) manages IP allocation centrally via etcd or K8s CRDs. All callers — whether kubelet or a direct CNI invocation — go through the same IPAM backend, preventing double-allocation, provided that dedicated IP pools are used for DooD containers to avoid interference with kubelet's garbage collection of unknown endpoints.

**Procedure**:

1. Prerequisite: EXP-1 completed successfully.
2. On Node A, create 10 K8s pods (via Deployment).
3. On Node A, create 10 DooD containers with CNI direct invocation (from EXP-1).
4. Verify: all 20 containers/pods have unique IPs.
5. Inspect IPAM state:
   - Calico: `calicoctl ipam show --show-blocks`
   - Cilium: `cilium-dbg bpf ipcache list`
6. Delete 5 K8s pods and 5 DooD containers. Create 10 new ones (mixed). Verify no IP reuse conflicts.
7. Stress test: rapidly create and delete 50 DooD containers while K8s is scaling pods up and down.

**Success Criteria**:
- Zero IP conflicts across all iterations
- IPAM state correctly reflects both K8s pods and DooD containers
- No IPAM pool exhaustion beyond expected capacity

---

### 11.3 EXP-3: Cross-Node Connectivity via Host CNI

| Field | Value |
|---|---|
| **Objective** | Verify that a DooD container on Node A (with CNI-assigned IP) can communicate with a DooD container on Node B over the existing CNI overlay/routing |
| **Priority** | Critical |
| **Blocking** | Multi-node session feasibility with containerd DooD |

**Hypothesis**: CNI overlay infrastructure (VXLAN tunnels for Calico, eBPF for Cilium, etc.) is established at the node level, not per-pod. Any container with a CNI-assigned IP on the node should be routable through the existing overlay, regardless of whether it is a K8s pod.

**Procedure**:

1. Prerequisite: EXP-1 completed on both Node A and Node B.
2. Create DooD container `kernel-A` on Node A with CNI-assigned IP (e.g., 10.244.1.50).
3. Create DooD container `kernel-B` on Node B with CNI-assigned IP (e.g., 10.244.2.30).
4. From `kernel-A`, run:
   ```bash
   ping 10.244.2.30          # ICMP connectivity
   nc -zv 10.244.2.30 22     # TCP connectivity (SSH port)
   iperf3 -c 10.244.2.30     # Throughput test
   ```
5. From a K8s pod on Node A, ping `kernel-B` on Node B (cross-type connectivity).
6. Measure latency and throughput compared to K8s pod-to-pod communication on the same nodes.

**Success Criteria**:
- Bidirectional ICMP and TCP connectivity between DooD containers on different nodes
- Cross-type connectivity (K8s pod ↔ DooD container) works
- Throughput within 10% of K8s pod-to-pod baseline
- No packet drops under sustained load

**Failure Implications**: If cross-node routing does not work for DooD containers, the CNI overlay only routes traffic for endpoints it knows about via K8s API, and a custom overlay solution is required.

---

### 11.4 EXP-4: GPU Device Access from DooD Kernel Containers

| Field | Value |
|---|---|
| **Objective** | Verify that kernel containers created via DooD can access host GPUs without the NVIDIA K8s device plugin |
| **Priority** | High |
| **Blocking** | GPU workload support in DooD architecture |

**Procedure**:

1. Set up a K8s node with NVIDIA GPUs. Do **not** install the NVIDIA K8s device plugin on this node.
2. Deploy the agent DaemonSet pod with `privileged: true` and host device mounts.
3. From the agent pod, create a kernel container via DooD with GPU access:
   ```bash
   # Docker DooD
   docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

   # containerd DooD (nerdctl)
   nerdctl run --rm --device /dev/nvidia0 --device /dev/nvidiactl \
     --device /dev/nvidia-uvm nvidia/cuda:12.0-base nvidia-smi
   ```
4. Test multi-GPU:
   ```bash
   docker run --rm --gpus '"device=0,1"' nvidia/cuda:12.0-base nvidia-smi
   ```
5. Test fractional GPU (CUDA hook library injection):
   ```bash
   docker run --rm --gpus all \
     -v /path/to/cuda-hook:/usr/local/cuda-hook \
     -e LD_PRELOAD=/usr/local/cuda-hook/libcuda_hook.so \
     -e CUDA_SHARES=0.5 \
     nvidia/cuda:12.0-base python -c "import torch; print(torch.cuda.memory_allocated())"
   ```
6. Verify no conflict with K8s resource accounting (K8s should not see GPU usage by DooD containers).

**Success Criteria**:
- Single GPU, multi-GPU, and fractional GPU all work from DooD containers
- `nvidia-smi` inside kernel container shows correct GPU(s)
- No interference with K8s scheduler's GPU resource tracking (because device plugin is not installed)
- CUDA hook library injection works identically to bare-metal deployment

---

### 11.5 EXP-5: Agent Pod Restart and Kernel Recovery

| Field | Value |
|---|---|
| **Objective** | Verify that kernel containers survive agent pod restart and are properly recovered by the new agent instance |
| **Priority** | High |
| **Blocking** | Rolling update and fault recovery viability |

**Procedure**:

1. Deploy agent DaemonSet. Create 5 kernel sessions via Backend.AI API.
2. Verify all 5 kernels are running and responsive.
3. Kill the agent pod: `kubectl delete pod <agent-pod> --grace-period=30`
4. Wait for DaemonSet to reschedule a new agent pod.
5. Verify:
   - All 5 kernel containers are still running on the host (`docker ps` / `nerdctl ps`).
   - New agent pod discovers and reconnects to existing kernels via `DockerKernelRegistryRecovery`.
   - Sessions are reported as RUNNING in Backend.AI manager.
   - `docker exec` / interactive session access works through the new agent.
6. Repeat with `kubectl drain <node>` (which evicts the agent pod but not DooD containers).
7. Uncordon the node, verify agent pod returns and recovers.
8. Verify network state cleanup: after agent pod restart, check that no orphaned veth pairs or leaked IPs remain on the host. Run `ip link show | grep veth` and compare with running kernel containers. Verify CNI IPAM state matches actual container count.

**Success Criteria**:
- Zero kernel container loss during agent pod restart
- Recovery time < 30 seconds after new agent pod is ready
- All sessions return to RUNNING state without user intervention
- No data loss in kernel scratch space or vfolder mounts
- No orphaned veth pairs or leaked IPs after agent recovery

---

### 11.6 EXP-6: containerd DooD Basic Lifecycle

| Field | Value |
|---|---|
| **Objective** | Verify that a pod running on K8s can create, manage, and destroy containers on the host's containerd via socket mount |
| **Priority** | Medium |
| **Blocking** | containerd-based DooD path (Phase 3) |

**Procedure**:

1. Deploy a test pod with `/run/containerd/containerd.sock` mounted from host.
2. Inside the pod, use `nerdctl` or `ctr` to:
   ```bash
   # Pull an image into the backendai namespace
   nerdctl --namespace backendai pull python:3.11-slim

   # Create and start a container
   nerdctl --namespace backendai run -d --name test-kernel python:3.11-slim sleep 3600

   # Exec into the container
   nerdctl --namespace backendai exec test-kernel python -c "print('hello')"

   # Get logs
   nerdctl --namespace backendai logs test-kernel

   # Get stats
   nerdctl --namespace backendai stats test-kernel --no-stream

   # Stop and remove
   nerdctl --namespace backendai rm -f test-kernel
   ```
3. Verify all operations succeed.
4. Verify that containers in the `backendai` namespace do not appear in `kubectl get pods` (K8s namespace isolation).
5. Test bind mount from host path:
   ```bash
   nerdctl --namespace backendai run -d --name test-mount \
     -v /mnt/vfolder/user1/folder1:/home/work/folder1:rw \
     python:3.11-slim sleep 3600
   ```

**Success Criteria**:
- Full container lifecycle (create, exec, logs, stats, remove) works from within a K8s pod
- containerd namespace isolation prevents interference with K8s-managed containers
- Host path bind mounts work correctly
- Resource limits (CPU, memory) are properly applied via cgroups

---

### 11.7 EXP-7: vfolder Bind Mount Path Consistency

| Field | Value |
|---|---|
| **Objective** | Verify that host paths mounted into the agent pod are resolvable and consistent when the agent creates kernel containers via DooD |
| **Priority** | High |
| **Blocking** | vfolder mount correctness |

**Background**: In DooD, the agent pod sees the host filesystem via `hostPath` mounts. When the agent creates a kernel container and specifies a bind mount (e.g., `-v /mnt/vfolder/user1/data:/home/work/data`), this path refers to the **host** filesystem, not the agent pod's filesystem. The paths must be consistent.

**Procedure**:

1. Host has CephFS mounted at `/mnt/vfolder`.
2. Agent pod mounts `/mnt/vfolder` as `hostPath`.
3. Agent creates a kernel container with bind mount: `-v /mnt/vfolder/user1/testdata:/home/work/testdata`.
4. Inside the kernel container:
   ```bash
   ls /home/work/testdata     # Verify files are visible
   echo "test" > /home/work/testdata/output.txt  # Verify write works
   ```
5. From the host: verify `/mnt/vfolder/user1/testdata/output.txt` exists.
6. From the agent pod: verify the same file is visible at its mount.
7. Test with read-only mount: `-v /mnt/vfolder/user1/testdata:/home/work/testdata:ro`.
8. Test scratch space: agent writes to `/var/cache/backendai/scratches/<kernel-id>/`, kernel sees it at `/home/work/`.

**Success Criteria**:
- Bidirectional file visibility between host, agent pod, and kernel container
- Read-only mounts enforced correctly
- Scratch space paths are consistent across all three contexts
- No permission (UID/GID) issues with shared files

---

### 11.8 EXP-8: Docker Swarm Overlay Coexistence with K8s CNI

| Field | Value |
|---|---|
| **Objective** | Verify that Docker Swarm overlay networks can coexist with K8s CNI (Calico/Cilium) on the same node without IP range or routing conflicts |
| **Priority** | High (for Docker DooD Phase 2) |
| **Blocking** | Multi-node session networking in Docker DooD deployment |

**Procedure**:

1. Set up a 2-node K8s cluster with Calico CNI (pod CIDR: `10.244.0.0/16`).
2. Initialize Docker Swarm on the same nodes (default overlay subnet: `10.0.0.0/8` — **must be reconfigured to avoid overlap**).
3. Create a Docker Swarm overlay network with a non-conflicting CIDR:
   ```bash
   docker network create -d overlay --subnet=172.30.0.0/16 backendai-overlay
   ```
4. Deploy K8s pods and DooD kernel containers simultaneously:
   - K8s pods: 10 nginx pods (Calico-networked)
   - DooD kernels: 10 containers on Swarm overlay
5. Verify:
   - K8s pods can reach each other across nodes (Calico overlay).
   - DooD kernels can reach each other across nodes (Swarm overlay).
   - No cross-contamination: K8s pods cannot accidentally route to Swarm IPs and vice versa.
   - `ip route` on host shows distinct routing tables for both overlays.
6. Stress test: scale both to 50 pods/containers and verify stability.

**Success Criteria**:
- Both overlays function independently on the same nodes
- No IP range conflicts (requires explicit CIDR planning)
- No routing table corruption or packet misrouting
- Stable under concurrent scaling

**Failure Implications**: If Swarm and K8s CNI conflict, Docker DooD Phase 2 requires either: (a) not using Swarm overlay (fall back to host networking + manual port allocation), or (b) using CNI direct invocation (EXP-1/EXP-3) even in the Docker DooD phase.

---

### 11.9 Experiment Execution Priority

| Order | Experiment | Phase Dependency | Estimated Effort |
|---|---|---|---|
| 1 | EXP-7: vfolder bind mount paths | Phase 2 (Docker DooD) | 0.5 day |
| 2 | EXP-4: GPU device access | Phase 2 (Docker DooD) | 0.5 day |
| 3 | EXP-8: Swarm + K8s CNI coexistence | Phase 2 (Docker DooD) | 1 day |
| 4 | EXP-5: Agent restart recovery | Phase 2 (Docker DooD) | 1 day |
| 5 | EXP-1: CNI direct invocation | Phase 3 (containerd) | 0.5 day |
| 6 | EXP-2: IPAM coexistence | Phase 3 (containerd) | 0.5 day |
| 7 | EXP-3: Cross-node CNI connectivity | Phase 3 (containerd) | 1 day |
| 8 | EXP-6: containerd DooD lifecycle | Phase 3 (containerd) | 1 day |

EXP-1 through EXP-3 (CNI direct invocation) are the most architecturally significant experiments. Their results determine whether containerd DooD can use the host CNI for multi-node sessions, or whether a custom overlay solution is needed.

---

## 12. Conclusions and Recommendations

### 12.1 Summary of Findings

The DooD-based architecture (Agent as K8s DaemonSet + host container runtime for kernels) provides the best balance between K8s operational benefits and Backend.AI feature preservation:

1. **Full GPU feature parity**: Multi-GPU, fractional GPU, CUDA hook libraries, all compute plugins work unchanged.
2. **Full storage feature parity**: vfolder bind mounts, scratch space, distributed filesystem mounts work unchanged.
3. **Minimal code changes**: The existing `DockerAgent` works with DooD. Configuration and service discovery are the primary changes.
4. **K8s operational benefits**: Rolling updates, self-healing, declarative configuration, Helm-based deployment for the control plane and agent lifecycle.
5. **Known trade-off**: Kernel containers are invisible to K8s, requiring Backend.AI's own resource management to prevent over-commitment.

### 12.2 Recommended Approach

**Phase 1 (1-2 months): Hybrid — Control Plane on K8s, Agent on Host**
- Deploy Manager, PostgreSQL, Redis, etcd as K8s workloads.
- Keep agents on bare-metal/VM hosts, connecting to K8s-hosted control plane.
- Validates control plane K8s deployment with zero agent risk.

**Phase 2 (2-3 months): DooD Agent DaemonSet with Docker**
- Deploy agent as K8s DaemonSet with Docker socket mount (DooD).
- Docker daemon remains on host for kernel container management.
- Docker Swarm overlay for multi-node sessions.
- Resolve GPU device plugin conflict (disable K8s device plugin on agent nodes).

**Phase 3 (6-12 months): containerd Migration (Optional)**
- Develop containerd-native agent backend, eliminating Docker daemon dependency.
- Implement alternative multi-node session networking (CNI-based or WireGuard).
- Migrate GPU management to CDI.

### 12.3 Container Runtime Recommendation

| Deployment Scenario | Runtime | Confidence |
|---|---|---|
| Initial K8s migration | **Docker** | High |
| Single-node-only sessions (no multi-node) | **containerd** (viable now with moderate effort) | Medium |
| Long-term target | **containerd** | High |
| Multi-node sessions (Swarm overlay required) | **Docker** (until alternative overlay is built) | High |

---

## 13. References

### Backend.AI Internal
1. Backend.AI Agent Docker Implementation. `src/ai/backend/agent/docker/agent.py`
2. Backend.AI Agent Kubernetes Implementation. `src/ai/backend/agent/kubernetes/agent.py`
3. Backend.AI Agent Types and Backends. `src/ai/backend/agent/types.py`
4. Kata Containers Feature Parity Analysis. `docs/reports/kata-containers-feature-parity-analysis.md`

### Kubernetes
5. Kubernetes DaemonSet Documentation. https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/
6. Kubernetes Container Runtime Interface (CRI). https://kubernetes.io/docs/concepts/architecture/cri/
7. CloudNativePG Operator. https://cloudnative-pg.io/
8. NVIDIA GPU Operator for Kubernetes. https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/

### Container Runtimes
9. containerd Architecture. https://github.com/containerd/containerd/blob/main/docs/getting-started.md
10. nerdctl: Docker-compatible CLI for containerd. https://github.com/containerd/nerdctl
11. Container Device Interface (CDI) Specification. https://github.com/cncf-tags/container-device-interface
12. Docker Engine API Reference. https://docs.docker.com/engine/api/

### DooD Pattern
13. Docker-out-of-Docker Pattern. https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/
14. DooD Security Considerations. https://docs.docker.com/engine/security/
