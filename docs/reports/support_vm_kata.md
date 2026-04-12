# Backend.AI VM Runtime Support: Kata Containers and KubeVirt

| Field | Value |
|---|---|
| **Document ID** | TR-2026-003 |
| **Date** | 2026-04-08 |
| **Author** | Backend.AI Architecture Team |
| **Status** | Draft |
| **Classification** | Internal Technical Reference |
| **Related Documents** | `k8s-control-plane-dood-agent-architecture.md`, `kata-containers-feature-parity-analysis.md` |
| **Scope** | Considerations and required changes to support VM-based isolation runtimes (Kata Containers, KubeVirt) as alternatives to the default DooD architecture |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Background and Motivation](#2-background-and-motivation)
   - 2.1 [Why DooD is the Default](#21-why-dood-is-the-default)
   - 2.2 [Why VM Isolation Must Be Supported](#22-why-vm-isolation-must-be-supported)
3. [VM Runtime Options](#3-vm-runtime-options)
   - 3.1 [Kata Containers](#31-kata-containers)
   - 3.2 [KubeVirt](#32-kubevirt)
   - 3.3 [Comparison with DooD](#33-comparison-with-dood)
4. [GPU + VM Constraints](#4-gpu--vm-constraints)
   - 4.1 [Firecracker Cannot Be Used for GPU Workloads](#41-firecracker-cannot-be-used-for-gpu-workloads)
   - 4.2 [GPU Static Binding to VMs](#42-gpu-static-binding-to-vms)
   - 4.3 [Why VM Pooling Does Not Work for GPUs](#43-why-vm-pooling-does-not-work-for-gpus)
   - 4.4 [GPU VM Cold Start Reality](#44-gpu-vm-cold-start-reality)
5. [Operational Strategies](#5-operational-strategies)
   - 5.1 [Runtime Class Selection per Session](#51-runtime-class-selection-per-session)
   - 5.2 [Dedicated GPU Pool (Pre-committed VMs)](#52-dedicated-gpu-pool-pre-committed-vms)
   - 5.3 [NVIDIA vGPU and MIG Integration](#53-nvidia-vgpu-and-mig-integration)
   - 5.4 [Per-GPU Driver Binding for Mixed Nodes](#54-per-gpu-driver-binding-for-mixed-nodes)
6. [When to Choose VM-Based Isolation](#6-when-to-choose-vm-based-isolation)
7. [Hybrid Runtime Architecture Design](#7-hybrid-runtime-architecture-design)
8. [System-Wide Changes Required](#8-system-wide-changes-required)
   - 8.1 [Agent Core Architecture](#81-agent-core-architecture)
   - 8.2 [Kernel Communication](#82-kernel-communication)
   - 8.3 [GPU Allocation](#83-gpu-allocation)
   - 8.4 [Storage](#84-storage)
   - 8.5 [Networking](#85-networking)
   - 8.6 [Image Management](#86-image-management)
   - 8.7 [Manager and Scheduler](#87-manager-and-scheduler)
   - 8.8 [Node Infrastructure](#88-node-infrastructure)
   - 8.9 [Monitoring and Observability](#89-monitoring-and-observability)
   - 8.10 [Helm Chart and Deployment](#810-helm-chart-and-deployment)
   - 8.11 [API / CLI / UI](#811-api--cli--ui)
   - 8.12 [Test Infrastructure](#812-test-infrastructure)
9. [Reusable vs Rewrite Summary](#9-reusable-vs-rewrite-summary)
10. [Critical Architectural Decisions](#10-critical-architectural-decisions)
11. [Phased Implementation Roadmap](#11-phased-implementation-roadmap)
12. [Effort Estimate](#12-effort-estimate)
13. [Conclusions and Recommendations](#13-conclusions-and-recommendations)
14. [References](#14-references)

---

## 1. Executive Summary

This document analyzes the requirements and trade-offs for supporting VM-based isolation runtimes — Kata Containers and KubeVirt — alongside the default Docker-out-of-Docker (DooD) architecture established in `k8s-control-plane-dood-agent-architecture.md`.

**Key findings:**

- **VM-based isolation must be supported as an option** for environments with strict security, multi-tenancy, or regulatory requirements where shared-kernel containers are inadequate.
- **GPU workloads break most VM optimization techniques**: Firecracker cannot do GPU passthrough, VM pooling wastes GPUs, and Cold Start times are 30 seconds to several minutes due to GPU initialization overhead. However, multi-GPU is supported via `pcie_root_port` configuration (when bypassing the NVIDIA GPU Operator).
- **Per-GPU driver binding** allows hybrid nodes (some GPUs DooD, others VM) but requires per-GPU scheduler tracking.
- **Fractional GPU does not work in VMs** — Backend.AI's CUDA hook library mechanism cannot cross the VM boundary. NVIDIA vGPU (Enterprise license) or MIG are the only alternatives.
- **System-wide changes** span 12 architectural layers and require an estimated 12-18 months of engineering effort with 2-3 full-time engineers.
- **Phased adoption** is recommended: Foundation → Kata → KubeVirt → Fractional GPU in VM.

---

## 2. Background and Motivation

### 2.1 Why DooD is the Default

The primary architecture (described in `k8s-control-plane-dood-agent-architecture.md`) uses Docker-out-of-Docker (DooD) for kernel container management. This choice provides:

- **Full GPU feature support**: multi-GPU, fractional GPU via CUDA hook library, MIG, NUMA awareness
- **Identical to bare-metal performance**: no VM overhead
- **Minimal Backend.AI code changes**: existing `DockerAgent` works unchanged
- **Fast startup**: ~1-3 seconds for kernel container creation
- **Native bind mounts**: zero overhead for vfolder access

For the vast majority of Backend.AI workloads (single-tenant or trusted-tenant AI/ML training and inference), DooD provides the best balance of features, performance, and operational simplicity.

### 2.2 Why VM Isolation Must Be Supported

Despite DooD's advantages, VM-based isolation is **not optional** for many real-world deployments:

| Driver | Description |
|---|---|
| **Multi-tenancy with untrusted code** | Users may run arbitrary code; container escape via kernel CVE is unacceptable |
| **Regulatory compliance** | PCI-DSS, HIPAA, FedRAMP, ISO 27001 may require hardware-enforced isolation |
| **Confidential computing** | Data-in-use protection via Intel TDX, AMD SEV-SNP requires VM-based execution |
| **Security research** | Malware analysis, vulnerability research, untrusted experimentation |
| **Government/defense** | Classified workloads with strict isolation mandates |
| **Customer requirements** | Enterprise customers may explicitly require VM isolation in contracts |

For these scenarios, "DooD is faster" is not a valid argument — VM isolation is a prerequisite, and the system must accommodate it. The question is not *whether* to support VM runtimes, but *how* to integrate them with minimum disruption to DooD users.

---

## 3. VM Runtime Options

### 3.1 Kata Containers

Kata Containers provides pod-level hardware isolation by running each Kubernetes pod inside a lightweight VM. Existing OCI container images run unchanged, but each pod gets its own guest kernel and hypervisor boundary.

**Architecture:**

```
┌─── K8s Node ────────────────────────────────────────────┐
│                                                          │
│  Host OS                                                 │
│    ├── containerd + kata-runtime                        │
│    └── kata-shim manages VM lifecycle                   │
│                                                          │
│  ┌── Kernel Container (via Kata) ─────────────────────┐ │
│  │  Lightweight VM (Cloud Hypervisor / QEMU)          │ │
│  │  ┌─── Guest Kernel (minimal) ──────────────────┐   │ │
│  │  │  kata-agent                                  │   │ │
│  │  │  Container runtime                           │   │ │
│  │  │    └── Kernel workload                       │   │ │
│  │  │         └── GPU via VFIO                     │   │ │
│  │  └──────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**GPU support limitations** (see `kata-containers-feature-parity-analysis.md` for full analysis):

- **Single GPU supported** via VFIO passthrough
- **Multi-GPU supported** — multiple VFIO devices can be passed to a single VM via `pcie_root_port` configuration. Note: the NVIDIA GPU Operator path only supports single GPU; multi-GPU requires direct VFIO management (as Backend.AI already does). QEMU is more stable than Cloud Hypervisor for this
- **No fractional GPU** — VFIO passes the entire device; CUDA hook libraries do not work across the VM boundary
- **No NVIDIA Container Toolkit integration** — host-side device mapping does not cross the VM boundary
- Partial MIG support depending on hypervisor
- Confidential computing support (TDX, SEV-SNP) for privacy-sensitive workloads

**Integration with Backend.AI DooD model**: Kata is not directly compatible with the DooD architecture because kernel containers are not K8s pods. Adopting Kata would require either:

- Switching to a K8s-native kernel model (kernels as pods), abandoning DooD
- Or selective use: DooD for most workloads, Kata for specific opt-in sessions requiring strong isolation

### 3.2 KubeVirt

KubeVirt extends Kubernetes with a `VirtualMachine` custom resource, running full VMs alongside regular pods on the same nodes. Unlike Kata (which masquerades a VM as a pod), KubeVirt VMs are first-class K8s resources with full lifecycle management.

**GPU support:**

- **VFIO PCI passthrough** for dedicated GPUs (like bare-metal VM passthrough)
- **Multi-GPU per VM** — multiple PCI devices can be passed through to a single VM
- **NVIDIA vGPU (Enterprise)** — hypervisor-level time-slicing and memory partitioning via NVIDIA vGPU Manager
- **SR-IOV** for network/FPGA devices
- **No CUDA hook libraries** — Backend.AI's userspace fractional GPU mechanism does not work in a VM context

**Integration with Backend.AI**: A full KubeVirt integration would require significant architectural changes:

- Each session becomes a VM instead of a container
- Agent must create/manage `VirtualMachine` resources instead of Docker containers
- Kernel runner must be pre-installed in VM images (cloud-init or baked-in)
- Storage via CDI (Containerized Data Importer) or PVC-backed disks
- Networking via Multus CNI with multiple network attachments
- Different metrics/monitoring path (libvirt metrics instead of container cgroups)

### 3.3 Comparison with DooD

| Feature | DooD (default) | Kata Containers | KubeVirt |
|---|---|---|---|
| Isolation boundary | cgroup/namespace (soft) | Hardware VM (hard, per-pod) | Hardware VM (hard, per-VM) |
| GPU allocation mechanism | Docker device passthrough | VFIO passthrough | VFIO passthrough |
| Single GPU | Full | Yes | Yes |
| Multi-GPU per instance | Full | Yes (multiple VFIO, requires `pcie_root_port` config, bypassing GPU Operator) | Yes (multiple VFIO) |
| Fractional GPU (cuda.shares) | Full (CUDA hook library) | **Not supported** | NVIDIA vGPU (Enterprise license) |
| MIG support | Full | Limited | Yes |
| NVIDIA Container Toolkit | Full | Not applicable | Not applicable |
| Existing container images | Unchanged | Unchanged | Requires VM image conversion |
| Agent code changes | None | Moderate (K8s-native kernels) | Major (VM lifecycle management) |
| Startup latency | ~1-3 seconds | ~30 seconds (with GPU) | 1-2 minutes (with GPU) |
| Memory overhead | ~5-20MB | ~50-150MB per pod | ~500MB-1GB per VM |
| Blast radius of CVE | Container boundary | Pod boundary | VM boundary |
| Confidential computing (TDX, SEV) | No | Yes (CoCo) | Yes |

---

## 4. GPU + VM Constraints

VM-based isolation has well-known optimization techniques (Firecracker, VM pools, templating, snapshot/resume). **Almost none of these work for GPU workloads**, fundamentally changing the cost/benefit analysis compared to CPU-only VM scenarios.

### 4.1 Firecracker Cannot Be Used for GPU Workloads

Firecracker — AWS's minimal VMM with ~125ms boot time — is the fastest hypervisor option for Kata. However:

- Firecracker **explicitly excludes VFIO support** by design
- It is built for CPU-only serverless workloads (AWS Lambda, Fargate)
- VFIO would significantly expand the attack surface, contradicting Firecracker's minimalism goal
- **Result**: Firecracker is not an option for Backend.AI GPU workloads

This eliminates Kata's fastest VMM option. For GPU workloads, the realistic Kata choices are Cloud Hypervisor or QEMU, both with notably slower startup.

### 4.2 GPU Static Binding to VMs

VFIO passthrough works as follows:

```
At VM creation:
  ├── Host unbinds GPU from nvidia driver
  ├── Host binds GPU to vfio-pci driver
  ├── IOMMU group setup
  ├── VM is given the PCI device
  └── VM boots and initializes the PCI device

While VM is running:
  ├── GPU is "owned" by the VM
  ├── Host cannot see this GPU
  └── Cannot be assigned to other VMs simultaneously
```

**PCI hot-plug?** Theoretically possible but in practice:

- NVIDIA driver does not handle runtime PCI topology changes well
- CUDA contexts cannot survive device re-initialization
- Guest kernels frequently panic on device removal
- Effectively unusable in production

**Conclusion**: To reassign a GPU to a different VM requires terminating the current VM, unbinding the GPU, creating a new VM, and binding the GPU. VM restart is mandatory.

### 4.3 Why VM Pooling Does Not Work for GPUs

For CPU-only workloads, the standard optimization is to maintain a "warm pool" of pre-booted VMs:

```
General CPU-only workload (pooling works):
┌──── Warm Pool ────┐
│  VM 1 (idle) ☉   │  ← request arrives
│  VM 2 (idle) ☉   │    just assign
│  VM 3 (idle) ☉   │
└────────────────────┘

GPU workload (pooling broken):
┌──── "Warm Pool"? ─────────────┐
│  VM 1 (idle, holds GPU 0) ⚠️  │  ← GPU is committed to this VM
│  VM 2 (idle, holds GPU 1) ⚠️  │    even while idle
│  VM 3 (idle, holds GPU 2) ⚠️  │
└──────────────────────────────┘
     → Idle VMs lock GPUs that cannot be used elsewhere
     → Extremely wasteful for $20K-30K H100s
     → "Pre-warmed" only in the sense of "pre-allocated"
```

GPUs are too expensive to leave attached to idle VMs. A pool of 8 H100s reserved for VM use means $200K of hardware sitting idle waiting for requests. This is rarely justifiable.

### 4.4 GPU VM Cold Start Reality

VM cold start latency for GPU workloads is fundamentally limited by **GPU hardware initialization**, not by the VMM choice:

```
CPU-only VM boot:
  Kernel boot ──▶ init ──▶ ready (a few seconds)

GPU VM boot:
  Kernel boot ──▶ init ──▶ NVIDIA driver load ──▶ 
  GPU initialization (PCI scan, VBIOS, ECC init) ──▶ ready
  (30 seconds to several minutes depending on GPU type and count)
```

H100 GPUs in particular take tens of seconds just for ECC memory initialization. **The GPU itself is the bottleneck**, not the VMM. Switching from QEMU to Cloud Hypervisor saves only a few hundred milliseconds — irrelevant compared to the GPU init cost.

**Total comparison:**

| Scenario | Cold Start Time |
|---|---|
| DooD container with cached image | 1-3 seconds |
| Kata + Cloud Hypervisor + GPU | 30-60 seconds |
| Kata + QEMU + GPU | 45-90 seconds |
| KubeVirt full VM + GPU | 1-3 minutes |

---

## 5. Operational Strategies

Despite the cold start cost, VM isolation can be made practical with the right operational strategies. Backend.AI's typical workload patterns (long-lived sessions) absorb startup latency, and several techniques further mitigate it.

### 5.1 Runtime Class Selection per Session

Expose runtime selection as a first-class API parameter, allowing users to opt into stronger isolation when needed:

```
POST /sessions
{
  "image": "python:3.11",
  "runtime_class": "secure",  // "standard" | "secure" | "confidential"
  "resources": {"cuda.device": 1}
}
```

| runtime_class | Backend | Cold Start | Isolation | Use Case |
|---|---|---|---|---|
| `standard` | DooD | ~1 sec | cgroup/namespace | General training/inference |
| `secure` | Kata + CHV | ~30 sec | Hardware VM | Multi-tenancy, untrusted code |
| `confidential` | Kata + CoCo (TDX/SEV) | ~60 sec | TEE-encrypted memory | Sensitive data, regulatory |

When users explicitly choose isolation level, UX expectations adjust accordingly. A 30-second wait is acceptable when users understand they are getting hardware isolation.

### 5.2 Dedicated GPU Pool (Pre-committed VMs)

For environments willing to absorb the cost, a dedicated GPU pool with pre-committed VMs eliminates user-visible cold start:

```
┌─── Secure GPU Pool (dedicated nodes) ─────────────────────┐
│                                                             │
│  Cold VM Pool (pre-created, GPU committed)                 │
│    ├── Kata VM 1 + GPU 0  (idle, awaiting user)            │
│    ├── Kata VM 2 + GPU 1  (idle)                           │
│    └── Kata VM 3 + GPU 2  (idle)                           │
│                                                             │
│  On request:                                                │
│    1. User requests session with secure runtime_class      │
│    2. Agent picks one from pool → instant assignment       │
│    3. Session initialization (Jupyter, etc.) takes seconds │
│                                                             │
│  On session end:                                            │
│    1. Destroy VM completely (clear memory + GPU state)     │
│    2. Create new VM and rebind GPU → return to pool        │
│    3. (30s-1min, but user already working)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- **Cost**: Pool size GPUs are committed but idle when not in use
- **Benefit**: User-perceived cold start = 0
- **Best for**: Finance, healthcare, government — high security demands and willingness to pay GPU opportunity cost

### 5.3 NVIDIA vGPU and MIG Integration

To work around the "VFIO whole-GPU" constraint, two NVIDIA technologies enable GPU sharing across VMs:

**NVIDIA vGPU (Enterprise license)**:

```
H100 ──split──▶ vGPU instances 4
                ├── VM 1 (vGPU 1)
                ├── VM 2 (vGPU 2)
                ├── VM 3 (vGPU 3)
                └── VM 4 (vGPU 4)
                
  → Multiple VMs share one GPU (time-slicing + memory partitioning)
  → Fractional GPU works in VM environments
```

**NVIDIA MIG (hardware partitioning)**:

```
H100 ──hardware split──▶ 7 MIG instances
                          ├── VM 1 (MIG slice 1)
                          ├── VM 2 (MIG slice 2)
                          └── ... (each VM gets dedicated MIG)
                          
  → Hardware isolation + VM isolation = double security
  → Cold start unchanged but GPUs are shared
```

vGPU has significant license costs but is the **only way to enable fractional GPU in VM environments**. For security-critical deployments where this is required, the cost is generally justifiable.

### 5.4 Per-GPU Driver Binding for Mixed Nodes

A common misconception is that an entire node must be either nvidia-driver-bound or vfio-pci-bound. In reality, the binding is **per-GPU**:

```
┌─── 8-GPU node (e.g., H100 8x) ────────────────────────────┐
│                                                            │
│  Static binding at boot via udev/modprobe:                │
│                                                            │
│  GPU 0-5 ──▶ nvidia driver                                │
│      └── Used by DooD containers (6 GPUs)                 │
│                                                            │
│  GPU 6-7 ──▶ vfio-pci driver                              │
│      └── Used by Kata/KubeVirt VMs (2 GPUs)               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Configuration:**

```bash
# /etc/modprobe.d/vfio.conf
# Bind specific PCI slots to vfio-pci instead of nvidia

# /etc/default/grub
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"

# /etc/udev/rules.d/10-vfio.rules
ACTION=="add", KERNEL=="0000:81:00.0", DRIVERS=="vfio-pci"
ACTION=="add", KERNEL=="0000:82:00.0", DRIVERS=="vfio-pci"
```

**Constraints:**

- Binding is **static**, set at boot time
- IOMMU groups must allow the split (each GPU in its own group)
- NVLink-connected GPUs typically must all be in the same camp
- Backend.AI scheduler must track runtime capability **per GPU**, not per node
- Fractional GPU is still impossible on VFIO-bound GPUs (unless using vGPU)

**When this is useful:**

- Cost optimization: avoid dedicating entire H100 nodes to either DooD or VM workloads
- Small clusters where dedicated VM nodes would waste GPU capacity
- Gradual migration: introduce VM support without restructuring all GPU nodes

---

## 6. When to Choose VM-Based Isolation

| Scenario | Recommended Approach |
|---|---|
| General AI/ML training/inference | **DooD** (default) |
| Multi-tenant with trusted users | **DooD** |
| Multi-tenant with untrusted code | Kata (opt-in) |
| Compliance requiring hardware isolation (PCI-DSS, HIPAA) | Kata or KubeVirt |
| Confidential computing (TEE) | Kata (with CoCo) |
| Security research / malware analysis | KubeVirt (strongest isolation) |
| Legacy workloads requiring full VM | KubeVirt |
| Cost-sensitive small clusters | DooD (avoid VM overhead) |
| GPU-intensive distributed training | DooD preferred (performance), Kata also supports multi-GPU |
| Single-GPU inference at scale | Kata acceptable, DooD preferred |

---

## 7. Hybrid Runtime Architecture Design

Backend.AI can support multiple runtime classes within a single cluster by using:

```
┌─── Control Plane ───────────────────────────────────────────┐
│                                                              │
│  Manager ── Sokovan scheduler                                │
│    ├── Session requests runtime_class: "dood"  → Agent Pool A│
│    ├── Session requests runtime_class: "kata"  → Agent Pool B│
│    └── Session requests runtime_class: "kvm"   → Agent Pool C│
│                                                              │
└──────────────┬───────────┬───────────┬──────────────────────┘
               │           │           │
               ▼           ▼           ▼
    ┌─── Pool A ───┐ ┌─── Pool B ───┐ ┌─── Pool C ───┐
    │ DooD agents  │ │ Kata agents  │ │ KubeVirt     │
    │ (full GPU    │ │ (VFIO single │ │ (VM with     │
    │  features)   │ │  GPU only)   │ │  vGPU)       │
    └──────────────┘ └──────────────┘ └──────────────┘
```

Implementation prerequisites:

1. **Taint-based pool separation**: Each runtime class has its own dedicated node pool with unique taints (`backendai.io/runtime=dood`, `backendai.io/runtime=kata`, `backendai.io/runtime=kvm`)
2. **Manager session routing**: Sokovan scheduler selects agent pool based on `runtime_class` session attribute
3. **Feature capability flags**: Accelerator plugin exposes runtime-class-specific capabilities (e.g., disable fractional GPU when `runtime_class != "dood"`)
4. **Per-runtime agent implementation**: Separate agent backends (`DockerAgent`, `KataAgent`, `KubeVirtAgent`) with shared abstract interface
5. **Image management**: Container images for DooD/Kata, VM images (qcow2) for KubeVirt — separate registries and pull strategies

---

## 8. System-Wide Changes Required

Supporting VM-based isolation alongside DooD as a first-class option requires changes across nearly every layer of Backend.AI. The 12 layers below enumerate required changes with difficulty estimates.

### 8.1 Agent Core Architecture

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 1 | Agent backend abstraction | `DockerAgent`, `KubernetesAgent`, `DummyAgent` | Add `KataAgent`, `KubeVirtAgent`. Generalize `AbstractAgent` interface | Medium |
| 2 | Kernel creation path | `docker.containers.create()` | Runtime-specific branching: Docker API / K8s Pod with runtimeClass / K8s VirtualMachine CR | High |
| 3 | Kernel ≠ container abstraction | "Kernel = Docker container" assumption embedded throughout | Kernel = runtime-independent entity. Decouple "container" terminology across the codebase | High |
| 4 | Kernel lifecycle state machine | Container states (`created`, `running`, `exited`) | Include VM states (`provisioning`, `booting`, `initializing`) with longer transition times | Medium |
| 5 | Kernel recovery | `DockerKernelRegistryRecovery` | Per-runtime recovery logic. State restoration on VM restart | Medium |

### 8.2 Kernel Communication

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 6 | Communication transport | TCP via Docker port mapping (127.0.0.1) | Kata: vsock or virtio-serial / KubeVirt: via guest network | High |
| 7 | `kernel_host` calculation | Host loopback | VM IP or vsock CID | Medium |
| 8 | Port pool management | Host port pool | VM environments have different port mapping semantics | Medium |

### 8.3 GPU Allocation

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 9 | GPU device mapping | `--device /dev/nvidia0` | VFIO binding (Kata/KubeVirt), vGPU mapping, MIG UUID | High |
| 10 | Fractional GPU (cuda.shares) | CUDA hook library via `LD_PRELOAD` | Cannot cross VM boundary. Replace with NVIDIA vGPU or MIG | Very High |
| 11 | Multi-GPU allocation | Multiple `--device` flags | VFIO multiple passthrough, IOMMU group considerations | High |
| 12 | NUMA placement | CPU pinning + GPU affinity | VM vCPU pinning + VFIO NUMA topology | Medium |
| 13 | GPU driver binding | All GPUs use NVIDIA driver | **Per-GPU binding** (not per-node): nvidia vs vfio-pci. See Section 5.4 | High |
| 14 | Accelerator plugin API | `generate_docker_args()`, `generate_hooks()` | Per-runtime methods: `generate_kata_annotations()`, `generate_kubevirt_devices()` | Medium |

### 8.4 Storage

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 15 | vfolder mount | Docker bind mount (host → container) | Kata: virtio-fs / KubeVirt: PVC or virtio-fs | Medium |
| 16 | Scratch space | hostPath on node | VM uses guest disk or virtio-fs | Medium |
| 17 | VFolderMount abstraction | Host path → container path | Runtime-independent abstraction with per-runtime translation layer | Medium |
| 18 | Performance difference UX | Native I/O | virtio-fs is 3-10x slower → user warning or scheduling consideration | Low |

### 8.5 Networking

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 19 | Single-node session network | Docker bridge | Kata: K8s pod network (CNI) / KubeVirt: guest network | Medium |
| 20 | Multi-node session network | Docker Swarm overlay | CNI-based (Multus) or Kata network plugin | High |
| 21 | Service port exposure | Docker port mapping → AppProxy | K8s Service → AppProxy (unified across runtimes) | Medium |
| 22 | Cluster SSH (MPI/NCCL) | Swarm overlay L3 connectivity | Equivalent inter-node L3 connectivity for Kata/KubeVirt | High |

### 8.6 Image Management

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 23 | Kernel image | OCI container image | Same for DooD/Kata. KubeVirt requires qcow2 VM image | Medium |
| 24 | Image build pipeline | Dockerfile | VM image build for KubeVirt (packer, virt-builder) | Medium |
| 25 | Image distribution | Docker registry (Harbor) | KubeVirt uses CDI (Containerized Data Importer) or different registry | Medium |
| 26 | Image metadata | OCI labels in Image table | Add VM image compatibility metadata | Low |

### 8.7 Manager and Scheduler

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 27 | Session API | `resources`, `image` | Add `runtime_class` parameter | Low |
| 28 | Sokovan scheduler | Resource-based matching | Runtime-capability awareness. Per-runtime node pool routing. Per-GPU runtime tracking | Medium |
| 29 | Resource accounting | GPU/CPU/memory slots | Include VM overhead (kernel ~150MB, CPU overhead) | Medium |
| 30 | Cold start prediction | None | Estimate VM session startup time, expose to user | Low |
| 31 | Session migration | Not supported | KubeVirt supports live migration — potential new feature | High |
| 32 | Agent registration schema | `slots`, `capabilities` | Add `runtime_classes: ["dood", "kata"]` | Low |

### 8.8 Node Infrastructure

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 33 | Node pool separation | Single agent node type | Per-runtime dedicated node pools (separated by taints) — OR mixed nodes with per-GPU split binding | Medium |
| 34 | GPU driver binding | All GPUs on nvidia driver | Per-GPU static binding at boot. Node may have mixed bindings | High |
| 35 | Kernel boot parameters | Default | VM-capable nodes need `intel_iommu=on` or `amd_iommu=on` | Low |
| 36 | IOMMU groups | N/A | VFIO isolation by IOMMU group. Multiple GPUs in same group cause issues | Medium |
| 37 | Kata runtime install | Not present | containerd + kata-runtime, kata-agent, etc. | Medium |
| 38 | KubeVirt install | Not present | kubevirt-operator, virt-handler DaemonSet, libvirt | Medium |
| 39 | NVIDIA vGPU driver | Not present | Enterprise license, vGPU Manager install (for fractional GPU in VM) | High |

### 8.9 Monitoring and Observability

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 40 | Container metrics | cgroup via Docker stats | Kata: kata-agent or guest cgroup / KubeVirt: libvirt metrics | Medium |
| 41 | GPU metrics | Host nvidia-smi / DCGM | VFIO-bound GPUs invisible to host nvidia-smi. Guest-internal collection needed | High |
| 42 | Log collection | Docker logs | Kata: via kata-agent / KubeVirt: guest console + qemu logs | Medium |
| 43 | Kernel health check | Docker inspect | Per-runtime health probe (Kata API, VirtualMachineInstance status) | Medium |
| 44 | Event pipeline | Redis pub/sub | Same, but event sources differ per runtime | Low |

### 8.10 Helm Chart and Deployment

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 45 | Multiple Agent DaemonSets | Single Agent DaemonSet | Per-runtime DaemonSets (`agent-dood`, `agent-kata`, `agent-kubevirt`) | Medium |
| 46 | Runtime install Helm dependency | None | Kata operator chart, KubeVirt chart as subcharts | Low |
| 47 | values.yaml structure | Simple | `runtimeClasses: { dood: {}, kata: {}, kubevirt: {} }` structure | Low |
| 48 | Feature flags | None | Per-runtime enable/disable (initially only DooD enabled) | Low |

### 8.11 API / CLI / UI

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 49 | Session creation CLI | `./bai session create` | Add `--runtime-class=kata` option | Low |
| 50 | Capability discovery | None | `./bai runtime list` shows available runtime classes | Low |
| 51 | Web UI session creation | No runtime selection | Runtime selector dropdown, expected startup time per option | Low |
| 52 | Admin UI | Session list | runtime_class column, per-runtime resource dashboard | Low |

### 8.12 Test Infrastructure

| # | Change | Current | Required | Difficulty |
|---|---|---|---|---|
| 53 | CI environment | Docker-based | Nodes capable of running Kata/KubeVirt (nested virtualization or bare metal) | High |
| 54 | Agent backend tests | DockerAgent integration tests | Per-backend integration tests (VM tests take minutes) | Medium |
| 55 | End-to-end scenarios | Basic session create/exec | Per-runtime: session boot, GPU allocation, multi-node training | Medium |

---

## 9. Reusable vs Rewrite Summary

```
┌─── Reusable (no or minimal changes) ──────────────────────┐
│                                                            │
│  - Manager API base structure                              │
│  - User/permission/project model                           │
│  - vfolder metadata management                             │
│  - Web UI core                                             │
│  - Event system (Redis pub/sub)                            │
│  - etcd service discovery                                  │
│  - AppProxy (service port exposure)                        │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌─── Moderate changes (add abstraction layer) ──────────────┐
│                                                            │
│  - Sokovan scheduler (runtime-aware routing)               │
│  - Session creation API (runtime_class parameter)          │
│  - Helm chart (multiple DaemonSets)                        │
│  - Kernel lifecycle state machine                          │
│  - Monitoring pipeline                                     │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌─── Major rewrite / new implementation ────────────────────┐
│                                                            │
│  - Agent backend (KataAgent, KubeVirtAgent new)            │
│  - Kernel creation path (runtime-agnostic)                 │
│  - GPU allocation logic (per-runtime branching)            │
│  - Fractional GPU strategy (CUDA hook → vGPU/MIG)          │
│  - Kernel communication transport (TCP → vsock/virtio)     │
│  - Network plugin (Swarm → CNI-based)                      │
│  - Storage mount (bind → virtio-fs/PVC)                    │
│  - Image build pipeline (OCI + qcow2)                      │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌─── Infrastructure-level changes ──────────────────────────┐
│                                                            │
│  - Node pool separation (taint per runtime class)          │
│  - GPU driver binding (nvidia vs vfio-pci, per GPU)        │
│  - IOMMU activation, kernel boot params                    │
│  - Kata/KubeVirt runtime install                           │
│  - NVIDIA vGPU license adoption (optional)                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 10. Critical Architectural Decisions

Several fundamental decisions span the entire change set:

1. **Agent backend model**: Separate backends per runtime (`KataAgent`, `KubeVirtAgent`) or strategy pattern injection into a single agent? Former gives clean separation but code duplication; latter gives reuse but complex conditionals.

2. **Kernel concept redefinition**: Remove the implicit "kernel = container" assumption from the entire codebase. `AbstractKernel` exists but actual implementations have container assumptions baked in.

3. **Fate of fractional GPU**: Backend.AI's signature feature (CUDA hook based fractional GPU) does not work in a VM environment. Alternatives:
   - NVIDIA vGPU (Enterprise license cost)
   - MIG (only on hardware-supported GPUs, fixed partition sizes)
   - No fractional support in VM environments (whole GPU only)

4. **Node sharing strategy**: Per-GPU binding allows mixing DooD and VM workloads on the same node. The scheduler must track runtime capability per GPU (not per node). Trade-offs: more flexible resource utilization, more complex scheduling logic.

5. **Multi-node session networking integration**: 
   - DooD uses Swarm overlay
   - Kata/KubeVirt use CNI-based networking
   - Mixing creates inter-node networking complications
   - → Multi-node sessions can only span same runtime class

---

## 11. Phased Implementation Roadmap

A complete rewrite is impractical. Recommended phased approach:

**Phase 1 (3-6 months): Foundation**
- Agent backend abstraction refactoring
- `runtime_class` concept in API/CLI
- Node pool separation infrastructure
- Per-GPU runtime capability tracking in scheduler

**Phase 2 (6-12 months): Kata Support**
- `KataAgent` implementation (leverages K8s runtimeClass)
- VFIO-based single/multi GPU
- virtio-fs storage
- Fractional GPU **not supported** in VM initially

**Phase 3 (12-18 months): KubeVirt Support**
- `KubeVirtAgent` implementation
- VM image build/distribution pipeline
- vGPU integration (for organizations with license)
- Live migration and other advanced features

**Phase 4 (Long-term): Fractional GPU in VM**
- NVIDIA vGPU or MIG-based alternative
- Per-runtime capability matrix completed

---

## 12. Effort Estimate

| Layer | Estimated Effort |
|---|---|
| Agent abstraction + Kata basic | 3-4 months (2-3 engineers) |
| KubeVirt basic | 4-6 months |
| GPU allocation logic integration | 3-4 months |
| Networking integration | 2-3 months |
| Storage integration | 2 months |
| Image pipeline | 2-3 months |
| Scheduler / Manager | 2-3 months |
| Helm / infrastructure | 1-2 months |
| Tests / CI | 2 months (continuous) |
| **Total** | **~12-18 months (2-3 full-time engineers)** |

This estimate assumes parallel work streams and existing K8s/Kata/KubeVirt expertise on the team. Without prior expertise, add 30-50% for learning curve.

---

## 13. Conclusions and Recommendations

### Summary

VM-based isolation (Kata Containers, KubeVirt) is a **required capability** for Backend.AI in security-sensitive deployments — multi-tenant environments with untrusted code, regulatory compliance scenarios, and confidential computing workloads. However, GPU workloads fundamentally constrain the available optimization techniques: Firecracker is unusable, VM pooling wastes GPUs, and Cold Start times are dominated by GPU hardware initialization (30 seconds to several minutes).

### Recommendations

1. **Default to DooD**: For the vast majority of Backend.AI workloads (single-tenant, trusted multi-tenant, performance-critical training), DooD remains the right choice. Do not migrate existing workloads to VM-based runtimes.

2. **Add VM support as opt-in**: Implement VM-based runtimes (starting with Kata) as opt-in alternatives, selected per-session via a `runtime_class` parameter. Users explicitly choose isolation vs performance.

3. **Set realistic UX expectations**: VM-based sessions have 30+ second cold start. This is fundamental, not a bug. Communicate this clearly in CLI/UI.

4. **Per-GPU binding for flexibility**: On nodes with multiple GPUs, support per-GPU driver binding to enable hybrid configurations. The scheduler must track runtime capability per GPU.

5. **Phased rollout**: Foundation → Kata → KubeVirt → Fractional GPU in VM. Do not attempt to deliver everything at once.

6. **Reserve fractional GPU as a DooD-only feature** initially. NVIDIA vGPU adoption depends on customer demand and license budget.

7. **Plan for 12-18 months** of focused engineering effort with 2-3 dedicated engineers. This is a significant investment, justifiable only by concrete customer requirements.

### Decision Gate

Before committing to VM runtime support, confirm:

- [ ] Specific customer or regulatory requirement exists
- [ ] Customer accepts cold start UX trade-offs
- [ ] Customer accepts initial lack of fractional GPU
- [ ] Engineering team has K8s + Kata/KubeVirt expertise (or budget to acquire)
- [ ] Support team can handle dual-runtime operational complexity

If any of these are not met, defer VM runtime support until they are.

---

## 14. References

### Backend.AI Internal
1. K8s Control Plane + DooD Agent Architecture. `docs/reports/k8s-control-plane-dood-agent-architecture.md`
2. Kata Containers Feature Parity Analysis. `docs/reports/kata-containers-feature-parity-analysis.md`
3. Backend.AI Agent Docker Implementation. `src/ai/backend/agent/docker/agent.py`

### Kata Containers
4. Kata Containers Architecture. https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/README.md
5. Kata Containers Hypervisor Comparison. https://github.com/kata-containers/kata-containers/blob/main/docs/hypervisors.md
6. Confidential Containers Project. https://confidentialcontainers.org/

### KubeVirt
7. KubeVirt Documentation. https://kubevirt.io/user-guide/
8. KubeVirt GPU Passthrough. https://kubevirt.io/user-guide/virtual_machines/host-devices/

### NVIDIA Virtualization
9. NVIDIA vGPU Documentation. https://docs.nvidia.com/grid/
10. NVIDIA MIG User Guide. https://docs.nvidia.com/datacenter/tesla/mig-user-guide/
11. NVIDIA Container Toolkit. https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/

### Linux Virtualization
12. VFIO Documentation. https://docs.kernel.org/driver-api/vfio.html
13. Firecracker (no VFIO). https://github.com/firecracker-microvm/firecracker/blob/main/docs/device-api.md
14. Cloud Hypervisor. https://www.cloudhypervisor.org/
