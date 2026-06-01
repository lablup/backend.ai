# Kata Containers Feature Parity Analysis with Native Container Runtimes

| Field | Value |
|---|---|
| **Document ID** | TR-2026-001 |
| **Date** | 2026-02-27 |
| **Author** | Backend.AI Architecture Team |
| **Status** | Final |
| **Classification** | Internal Technical Reference |
| **Scope** | Kata Containers 3.x architecture, feature parity with Docker/containerd/runc, and feasibility assessment for Backend.AI integration |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Introduction and Motivation](#2-introduction-and-motivation)
3. [Kata Containers Architecture](#3-kata-containers-architecture)
   - 3.1 [Three-Environment Model](#31-three-environment-model)
   - 3.2 [Runtime Components](#32-runtime-components)
   - 3.3 [Container Creation Flow](#33-container-creation-flow)
   - 3.4 [Kata 3.x Architectural Evolution](#34-kata-3x-architectural-evolution)
4. [Hypervisor Landscape](#4-hypervisor-landscape)
   - 4.1 [Supported Hypervisors](#41-supported-hypervisors)
   - 4.2 [Feature Comparison Matrix](#42-feature-comparison-matrix)
   - 4.3 [Selection Guidelines](#43-selection-guidelines)
5. [Feature Parity Analysis](#5-feature-parity-analysis)
   - 5.1 [Networking](#51-networking)
   - 5.2 [Storage and Volumes](#52-storage-and-volumes)
   - 5.3 [GPU and Device Passthrough](#53-gpu-and-device-passthrough)
   - 5.4 [Resource Management](#54-resource-management)
   - 5.5 [Container Image Handling](#55-container-image-handling)
   - 5.6 [Multi-Container Pods](#56-multi-container-pods)
   - 5.7 [Security Model](#57-security-model)
6. [Performance Analysis](#6-performance-analysis)
   - 6.1 [Startup Latency](#61-startup-latency)
   - 6.2 [Memory Overhead](#62-memory-overhead)
   - 6.3 [CPU Performance](#63-cpu-performance)
   - 6.4 [I/O Performance](#64-io-performance)
   - 6.5 [Network Performance](#65-network-performance)
7. [Advanced Capabilities](#7-advanced-capabilities)
   - 7.1 [Confidential Containers (CoCo)](#71-confidential-containers-coco)
   - 7.2 [Peer Pods / Remote Hypervisor](#72-peer-pods--remote-hypervisor)
   - 7.3 [Nydus Image Acceleration](#73-nydus-image-acceleration)
   - 7.4 [Monitoring and Observability](#74-monitoring-and-observability)
8. [Known Limitations and Unsupported Features](#8-known-limitations-and-unsupported-features)
9. [Production Adoption](#9-production-adoption)
10. [Implications for Backend.AI](#10-implications-for-backendai)
11. [Conclusions and Recommendations](#11-conclusions-and-recommendations)
12. [References](#12-references)

---

## 1. Executive Summary

Kata Containers is an open-source project under the OpenInfra Foundation that provides hardware-isolated container workloads by running each Kubernetes pod inside a lightweight virtual machine (VM). It delivers the security guarantees of VMs while maintaining OCI runtime specification compliance and seamless Kubernetes integration via the RuntimeClass mechanism.

This report provides a comprehensive analysis of Kata Containers 3.x architecture, evaluates feature parity against native container runtimes (Docker, containerd with runc), and assesses implications for Backend.AI's container orchestration stack. The analysis covers networking, storage, GPU passthrough, resource management, security, performance, and advanced features including Confidential Containers.

**Key findings:**

- Kata provides strong hardware-enforced isolation with full OCI compliance, making it suitable for multi-tenant environments where untrusted workloads must be sandboxed.
- Significant feature gaps exist for Backend.AI's core use cases: multi-GPU passthrough is not supported (single GPU only via VFIO), storage I/O adds measurable overhead through the virtualization layer, and checkpoint/restore is not implemented.
- Kata 3.x's Rust rewrite and built-in Dragonball VMM deliver substantial performance improvements, with Alibaba demonstrating 3,000 secure containers launched in 6 seconds on a single host.
- Cold start overhead (125-500ms depending on hypervisor) and per-pod memory overhead (15-150MB) impact density and interactive session responsiveness compared to native containers.
- Confidential Containers (CoCo) integration with Intel TDX and AMD SEV-SNP represents a compelling future capability for privacy-sensitive AI/ML workloads.

---

## 2. Introduction and Motivation

### 2.1 Background

Traditional Linux containers (runc, Docker) share the host kernel and rely on namespaces and cgroups for isolation. While efficient, this model exposes a large kernel attack surface — a kernel vulnerability in any container can potentially compromise the entire host and all co-located workloads. This is a significant concern in multi-tenant environments where untrusted code executes alongside sensitive workloads.

Kata Containers addresses this by interposing a hypervisor boundary between the host and the containerized workload. Each pod receives its own guest kernel, eliminating cross-pod kernel attack surface. The project originated from the merger of Intel Clear Containers and Hyper runV in December 2017, combining Intel's hardware virtualization expertise with Hyper's container-optimized VM technology.

### 2.2 Scope of Analysis

This report evaluates Kata Containers from the perspective of a container orchestration platform (Backend.AI) that:

- Schedules and orchestrates containerized AI/ML workloads across distributed agent nodes
- Provides fractional and multi-GPU allocation to containers
- Mounts distributed storage (CephFS, NetApp, etc.) to containers via bind mounts
- Manages multi-node overlay networks for distributed training
- Requires low-latency interactive session startup for notebook environments

The analysis focuses on Kata 3.x (current mainline) with references to the upcoming 4.0 release where relevant.

### 2.3 Methodology

This report synthesizes information from the following sources:

- Official Kata Containers architecture documentation and design documents (GitHub repository)
- Community blog posts and project updates (2024-2025)
- Conference presentations (KubeCon, OpenInfra Summit)
- Third-party benchmarks and production case studies (StackHPC, Red Hat, Northflank)
- Cloud provider documentation (AWS, Azure, GCP)
- Academic papers on container runtime performance analysis

---

## 3. Kata Containers Architecture

### 3.1 Three-Environment Model

Kata Containers defines three distinct execution contexts that are fundamental to understanding its behavior:

**Host**: The physical machine running the container manager (containerd or CRI-O), the Kata runtime shim process, and the hypervisor process. The host is considered **untrusted** in confidential computing scenarios.

**Guest VM**: A lightweight virtual machine with its own Linux kernel, root filesystem, and the kata-agent daemon. The VM provides hardware-enforced isolation using KVM. The guest kernel is a standard Linux LTS kernel stripped down for container workloads — minimal drivers, fast boot, and small memory footprint.

**Container**: An isolated process environment *within* the guest VM, created using standard Linux namespaces and cgroups. From the workload's perspective, it appears identical to a native container. From the host's perspective, it is doubly isolated — first by the VM boundary, then by namespace/cgroup isolation within the guest.

The mapping model is **one VM per Kubernetes pod**. All containers within a single pod share the same VM. This preserves the Kubernetes pod semantics (shared network namespace, IPC, optional PID namespace sharing) while adding a hardware isolation boundary at the pod level.

```
┌─────────────────────── HOST ───────────────────────┐
│                                                     │
│  ┌──────────────────┐     ┌──────────────────────┐ │
│  │  containerd /    │     │  Other pods           │ │
│  │  CRI-O           │     │  (runc or kata)       │ │
│  └────────┬─────────┘     └──────────────────────┘ │
│           │ shimv2 API                              │
│  ┌────────▼─────────┐                              │
│  │  containerd-shim- │                              │
│  │  kata-v2          │                              │
│  │  (1 per pod)      │                              │
│  └────────┬─────────┘                              │
│           │ fork + manage                           │
│  ┌────────▼─────────┐     ┌──────────────────────┐ │
│  │  Hypervisor       │     │ virtiofsd            │ │
│  │  (QEMU/CLH/      │     │ (filesystem sharing) │ │
│  │   Dragonball)     │     └──────────────────────┘ │
│  └────────┬─────────┘                              │
│           │ VM boundary (KVM)                       │
│  ╔════════╧═══════════════════════════════════════╗ │
│  ║              GUEST VM                          ║ │
│  ║  ┌─────────────────────────────────────────┐   ║ │
│  ║  │  Guest Kernel (Linux LTS, minimal)      │   ║ │
│  ║  └─────────────────────────────────────────┘   ║ │
│  ║  ┌─────────────────────────────────────────┐   ║ │
│  ║  │  kata-agent (Rust, ttRPC over VSOCK)    │   ║ │
│  ║  └──────────┬──────────────────────────────┘   ║ │
│  ║             │                                   ║ │
│  ║  ┌──────────▼────┐  ┌───────────────────┐      ║ │
│  ║  │  Container A  │  │  Container B      │      ║ │
│  ║  │  (namespaces  │  │  (namespaces      │      ║ │
│  ║  │   + cgroups)  │  │   + cgroups)      │      ║ │
│  ║  └───────────────┘  └───────────────────┘      ║ │
│  ╚════════════════════════════════════════════════╝ │
└─────────────────────────────────────────────────────┘
```

### 3.2 Runtime Components

#### 3.2.1 containerd-shim-kata-v2 (The Runtime Shim)

The shim is the single entry point for Kata Containers on the host side. It implements the containerd Runtime V2 (shimv2) API, which replaced the earlier model requiring 2N+1 separate processes (kata-runtime, kata-shim, kata-proxy, and reaper) per pod.

Key characteristics:

- **One shim process per pod**: A single long-running daemon handles all containers within a pod.
- **Unix domain socket communication**: containerd creates a socket and passes it to the shim at startup. All subsequent lifecycle commands flow over this socket as gRPC calls.
- **Configuration**: Reads from `configuration.toml` (default at `/usr/share/defaults/kata-containers/`), which specifies hypervisor type, guest kernel/image paths, resource defaults, and feature toggles.
- **virtcontainers library**: Internally uses the virtcontainers abstraction layer, providing a runtime-spec-agnostic, hardware-virtualized containers API.

#### 3.2.2 Hypervisor

The hypervisor is spawned by the shim (or, in Dragonball's case, runs in-process) to create and manage the VM. It:

- Creates the VM with configured CPU/memory resources
- Sets up virtio devices (vsock for host-guest communication, block/fs for storage, net for networking)
- DAX-maps the guest image into VM memory for zero-copy access (on supported hypervisors)
- Supports hotplugging of CPU, memory, and block devices (hypervisor-dependent)

#### 3.2.3 kata-agent

The agent is a Rust daemon running inside the guest VM. It serves as the supervisor for all container operations within the VM:

- **Deployment modes**: In rootfs image deployments, systemd is PID 1 and kata-agent runs as a systemd service. In initrd deployments, kata-agent runs directly as PID 1 (no init system).
- **Communication**: Runs a ttRPC server (a lightweight gRPC alternative optimized for low-overhead communication) listening on a VSOCK socket.
- **API surface**: `CreateSandbox`, `CreateContainer`, `StartContainer`, `ExecProcess`, `WaitProcess`, `DestroySandbox`, and related operations.
- **Responsibilities**: Creates and manages namespaces, cgroups, and mounts within the guest for each container. Carries stdio streams (stdout, stderr, stdin) between containers and the host runtime.

#### 3.2.4 Communication Protocol: ttRPC over VSOCK

Host-guest communication uses ttRPC (Tiny TTRPC — a simplified, more efficient alternative to gRPC) over VSOCK (virtual socket, available since Linux kernel 4.8). VSOCK provides a direct host-guest socket without requiring network configuration. The protocol:

- Uses Protocol Buffers for serialization
- Supports multiplexed streams for concurrent container I/O
- Eliminates the need for the separate kata-proxy process that was required in pre-shimv2 architectures when using virtio-serial

### 3.3 Container Creation Flow

The step-by-step process from a pod creation request to a running container:

1. Kubernetes kubelet or Docker sends a container creation request to the CRI runtime (containerd or CRI-O).
2. CRI runtime identifies the RuntimeClass as `kata` and invokes the `containerd-shim-kata-v2` binary.
3. containerd creates a Unix domain socket and passes it to the shim, which starts as a long-running daemon.
4. The shim reads `configuration.toml` and launches the configured hypervisor (QEMU, Cloud Hypervisor, or Dragonball in-process).
5. The hypervisor boots the VM with the guest kernel and guest image. The guest image is DAX-mapped into VM memory for zero-copy access (on x86_64 with QEMU).
6. The kata-agent starts inside the VM (either as PID 1 for initrd or via systemd for rootfs images).
7. The shim establishes a ttRPC connection to the agent over VSOCK.
8. The shim calls `CreateSandbox` on the agent, establishing the pod-level environment.
9. For each container in the pod, the shim calls `CreateContainer`, and the agent creates the appropriate namespaces, cgroups, rootfs mounts, and environment within the guest.
10. The agent spawns the workload process and returns success.
11. The shim reports container running status to containerd.

**Shutdown**: The agent detects workload exit, captures the exit status, and returns it via `WaitProcess`. For forced shutdown, `DestroySandbox` terminates the VM via the hypervisor.

### 3.4 Kata 3.x Architectural Evolution

Kata 3.x represents a fundamental architectural shift from the Go-based runtime of version 2.x:

| Component | Kata 1.x | Kata 2.x | Kata 3.x |
|---|---|---|---|
| kata-agent | Go | Rust | Rust |
| kata-runtime | Go | Go | **Rust** (runtime-rs) |
| Shim model | 2N+1 processes | shimv2 (single process, Go) | shimv2 (single process, Rust) |
| VMM integration | External process | External process | **Built-in** (Dragonball) or external |
| Policy engine | N/A | Go-based OPA | Rust-based regorus |
| Async runtime | goroutines | goroutines | **Tokio** (configurable worker threads) |

#### 3.4.1 Rationale for the Rust Rewrite

- **Performance**: Eliminates Go garbage collection pauses and reduces memory consumption. The runtime is a long-lived system daemon where GC pauses can impact container lifecycle latency.
- **Memory safety**: Rust's ownership model prevents null pointer dereferences, use-after-free, and data races at compile time — critical for system-level software managing VM lifecycle.
- **Async runtime**: Tokio provides Go-like concurrency with configurable worker threads (`TOKIO_RUNTIME_WORKER_THREADS`, default: 2), enabling high concurrency with predictable resource consumption.

#### 3.4.2 Dragonball: Built-in VMM

The most significant architectural change in 3.x is the built-in Dragonball VMM. Instead of forking a separate hypervisor process and communicating over IPC, Dragonball is linked as a Rust library directly into the runtime process:

**Kata 2.x (separated VMM)**:
```
runtime process ──(fork + RPC)──> VMM process (QEMU, CLH)
```

**Kata 3.x (built-in VMM)**:
```
single process: runtime-rs + Dragonball VMM (shared address space)
```

Benefits:
- **Zero IPC overhead** between runtime and VMM
- **Unified lifecycle management** — no orphaned VMM processes on crashes
- **Simplified resource cleanup and exception handling**
- **Out-of-the-box experience** — no external VMM installation or version matching required

Dragonball is built on the rust-vmm crate ecosystem (shared building blocks with Firecracker and Cloud Hypervisor) and is specifically optimized for container workloads.

#### 3.4.3 Production Validation

Alibaba Cloud has validated the Rust runtime + Dragonball in production:
- Launch 3,000 secure containers in 6 seconds on a single host
- Run 4,000+ secure containers simultaneously on a single host
- Support approximately 12 billion calls per day for Function Compute services

---

## 4. Hypervisor Landscape

### 4.1 Supported Hypervisors

Kata Containers supports five hypervisors, all KVM-based (Type 2):

**QEMU** — The most feature-complete option. Written in C with approximately 2 million lines of code. Supports all CPU architectures (x86_64, ARM, ppc64le, s390x), all device types (40+ emulated devices including legacy), full CPU/memory/disk hotplug, VFIO device passthrough, virtio-fs, and 9pfs. The trade-off is a larger attack surface, higher memory overhead, and slower boot times compared to newer Rust-based VMMs. QEMU is the default hypervisor for the Go runtime.

**Cloud Hypervisor (CLH)** — A Rust-based VMM with approximately 50,000 lines of code. Supports x86_64 and aarch64, CPU/memory hotplug, virtio-fs, VFIO passthrough, and approximately 16 modern virtio devices. Boots in approximately 200ms. Provides a good balance between feature completeness and security (small Rust codebase, minimal attack surface).

**Firecracker** — AWS's minimal VMM, also Rust-based. Extremely fast boot (approximately 125ms) and tiny footprint, but deliberately omits filesystem sharing (no virtio-fs or 9pfs), device hotplug, and VFIO passthrough. All resources must be pre-allocated at VM boot. Designed for serverless/FaaS workloads where density and startup latency are critical.

**Dragonball** — Alibaba's built-in VMM for the Rust runtime. Runs in-process (not as a separate process), eliminating IPC overhead. Built on the rust-vmm crate ecosystem. Supports CPU/memory/disk hotplug, VFIO, and virtio-fs. Optimized for high-density container deployments. Default for runtime-rs.

**StratoVirt** — Huawei's VMM supporting both MicroVM (lightweight) and StandardVM modes. Currently supports MicroVM mode in Kata with limited features. The community has discussed potentially deprecating StratoVirt support due to maintenance concerns (April 2025 PTG).

### 4.2 Feature Comparison Matrix

| Feature | QEMU | Cloud Hypervisor | Firecracker | Dragonball | StratoVirt |
|---|---|---|---|---|---|
| Language | C (~2M LOC) | Rust (~50K LOC) | Rust | Rust | Rust |
| Architectures | x86_64, ARM, ppc64le, s390x | x86_64, aarch64 | x86_64, aarch64 | x86_64, aarch64 | x86_64, aarch64 |
| Typical boot time | ~500ms | ~200ms | ~125ms | ~200ms | ~200ms |
| Memory footprint | 50-150 MB | 20-50 MB | 15-30 MB | 20-50 MB | 20-50 MB |
| CPU hotplug | Yes | Yes | No | Yes | No |
| Memory hotplug | Yes | Yes | No | Yes | No |
| Disk hotplug | Yes | Yes | No | Yes | Yes |
| VFIO passthrough | Yes | Yes | No | Yes | No |
| virtio-fs | Yes | Yes | No | Yes | Yes |
| 9pfs | Yes | No | No | No | No |
| Device emulation scope | 40+ (incl. legacy) | ~16 modern | Minimal (3) | Container-optimized | MicroVM-focused |
| Execution model | Separate process | Separate process | Separate process | In-process (library) | Separate process |
| Default for | Go runtime | — | — | Rust runtime | — |
| Confidential computing | TDX, SEV-SNP | TDX, SEV-SNP | No | Planned | No |

### 4.3 Selection Guidelines

| Use Case | Recommended VMM | Rationale |
|---|---|---|
| General-purpose, maximum compatibility | QEMU | Broadest architecture and feature support |
| Cloud-native production (balanced) | Cloud Hypervisor | Good feature set with small Rust attack surface |
| Serverless / FaaS (density + speed) | Firecracker | Minimal boot time, smallest footprint |
| High-density containers (Rust runtime) | Dragonball | In-process VMM, zero IPC, optimized for containers |
| Confidential computing | QEMU | Most mature TDX/SEV-SNP support |
| Legacy hardware / non-x86 architectures | QEMU | Only option for ppc64le, s390x |

---

## 5. Feature Parity Analysis

This section provides a detailed comparison of Kata Containers capabilities against native container runtimes (runc via Docker or containerd). Each subsection identifies feature gaps, behavioral differences, and performance implications.

### 5.1 Networking

#### 5.1.1 Native Container Networking

Native containers use Linux network namespaces with veth (virtual Ethernet) pairs connecting containers to a bridge (e.g., `docker0` or `cni0`). The packet path is straightforward:

```
Container process → veth (container end) → veth (host end) → bridge → host routing
```

Overlay networks (VXLAN, Geneve) for multi-host communication add encapsulation/decapsulation at the host level. CNI plugins manage the full lifecycle. Performance is near-native since all operations occur within the host kernel's network stack.

#### 5.1.2 Kata Container Networking

Kata must bridge the gap between the host network namespace (where CNI plugins create veth pairs) and the guest VM (which uses virtio-net devices). Three networking models are supported:

**TC-filter (tc-redirect) — Default**

This is the current default networking model, chosen for maximum CNI plugin compatibility. The flow:

1. CNI plugin creates a veth pair as usual (e.g., `eth0` in pod netns, `vethXXXX` on bridge).
2. Kata runtime creates a TAP device (`tap0_kata`) inside the pod network namespace.
3. Linux Traffic Control (TC) mirror rules redirect traffic between the veth's ingress/egress and the TAP device's egress/ingress.
4. The TAP device connects to a virtio-net device inside the VM.
5. Inside the VM, the kata-agent configures the network interface with the same IP/MAC as the original veth.

```
Container (guest) → virtio-net → TAP (host) → TC mirror → veth → bridge → host
```

This model introduces up to five network hops before a packet reaches its destination, adding measurable latency and CPU overhead.

**MACVTAP — Alternative**

Uses the Linux MACVTAP driver, which combines TUN/TAP and bridge functionality into a single module based on the MACVLAN driver. The packet path is slightly shorter than TC-filter, with similar performance characteristics.

**Vhost-user — High Performance**

The virtio-net backend runs in a userspace process, requiring fewer syscalls than a full VMM path. Used for high-performance scenarios and in conjunction with DPDK-based virtual switches.

#### 5.1.3 Feature Parity Matrix

| Feature | Native (runc) | Kata Containers | Gap Assessment |
|---|---|---|---|
| CNI plugin compatibility | Full | Good (TC-filter preserves compatibility) | Minor — some edge cases with unusual CNI configs |
| Overlay networks (VXLAN, Geneve) | Full | Full (via guest virtio-net) | Parity |
| Bridge networking | Full | Full (via TC-filter or MACVTAP) | Parity |
| `--net=host` (host networking) | Supported | **NOT supported** | **Critical gap** — VM cannot share host netns |
| `--link` (container linking) | Supported (deprecated) | **NOT supported** | Minor — deprecated in Docker |
| Network namespace sharing | Full | **Broken** — takes over interfaces | **Significant gap** |
| Service mesh (Istio/Envoy sidecar) | Full | Works (sidecar in same VM) | Parity |
| Network policies (Calico, Cilium) | Full | Full (applied at host level) | Parity |
| IPv6 | Full | Supported | Parity |
| Multicast | Full | Supported (virtio-net) | Parity |
| SR-IOV | Direct | Via VFIO passthrough | Additional configuration required |
| RDMA / InfiniBand | Direct device access | Via VFIO passthrough | Additional configuration, hypervisor-dependent |
| DNS resolution | Full | Full (resolv.conf shared via virtio-fs) | Parity |

#### 5.1.4 Performance Impact

Red Hat benchmarks (OpenShift Sandboxed Containers) show:
- **CPU overhead**: A sandboxed pod consumes approximately 4.5 CPU cores versus approximately 1.8 cores for a non-sandboxed pod during network-intensive workloads (approximately 2.5x overhead).
- **Latency**: Typically under 1ms additional latency per hop.
- **Throughput**: TC-filter and MACVTAP achieve comparable throughput; both are superior to the deprecated bridge mode.

### 5.2 Storage and Volumes

#### 5.2.1 Filesystem Sharing Mechanisms

Container images and volumes stored on the host must be shared with the guest VM. Kata supports multiple mechanisms:

**virtio-fs (Default since Kata 2.0)**

A shared filesystem protocol based on FUSE, implemented as a virtio device. A `virtiofsd` daemon runs on the host, serving filesystem requests from the guest. Key characteristics:
- Near-native performance when combined with DAX (Direct Access) mapping
- Full POSIX compliance
- Used for sharing container rootfs, volumes, ConfigMaps, Secrets, and configuration files (hostname, hosts, resolv.conf)
- Available since Linux 5.4, QEMU 5.0, Kata 1.7

**DAX (Direct Access) Optimization**: On x86_64 with QEMU, virtio-fs can use NVDIMM/DAX mapping to map the guest image directly into VM memory without going through the guest kernel page cache. This provides zero-copy access, reduced memory consumption (pages are shared, not duplicated), and faster boot times.

**9pfs (Legacy, Deprecated)**

Plan 9 file protocol. Simpler implementation but significantly slower — every file operation traverses the 9P protocol and host syscalls. Has POSIX compliance limitations. Only supported on QEMU. Not recommended for production.

**virtio-blk / virtio-SCSI**

Block-level device sharing. The runtime detects whether container images use overlay-based filesystem drivers (shared via virtio-fs) or devicemapper/other block-based snapshotters (shared via virtio-blk/scsi). Used for persistent volumes and block-based workloads.

**vhost-user-blk**

Highest performance option. The virtio block backend runs in a separate userspace process, bypassing the VMM entirely. Benchmarks show near host-level I/O performance.

#### 5.2.2 Feature Parity Matrix

| Feature | Native (runc) | Kata Containers | Gap Assessment |
|---|---|---|---|
| OverlayFS image layers | Direct kernel access | Shared via virtio-fs | Minor overhead |
| Bind mounts | Zero overhead | Via filesystem sharing (virtio-fs) | Measurable overhead |
| Bind mounts (TEE mode) | N/A | **Files copied** into guest; changes NOT synced back | **Critical gap** for TEE |
| tmpfs | Full | Supported | Parity |
| emptyDir (tmpfs-backed) | Full | `/dev/shm` sizing **broken** (capped at 64KB) | **Bug** |
| ConfigMaps | Full, live updates | Supported; SubPath does NOT receive live updates | Gap |
| Secrets | Full, tmpfs-backed | Supported, tmpfs-backed | Parity |
| `volumeMount.subPath` | Supported | **NOT supported** | **Gap** |
| hostPath | Direct | Depends on fs sharing; no sync-back in TEE | Behavioral difference |
| PersistentVolumes (block) | Full | Via virtio-blk/scsi | Parity (minor overhead) |
| PersistentVolumes (NFS/CephFS) | Direct mount | Via virtio-fs passthrough | Overhead |
| CSI drivers | Full | Supported (host-side) | Parity |

#### 5.2.3 I/O Performance Data

StackHPC benchmarks using fio with varying client counts and I/O patterns:

**With 9pfs (legacy — included for reference)**:

| Metric | Bare Metal | Kata (9pfs) | Degradation |
|---|---|---|---|
| Sequential read bandwidth (64 clients) | Baseline | ~15% of bare metal | 6.7x worse |
| Sequential read p99 latency (64 clients) | 47,095 us | 563,806 us | 12x worse |
| Random write p99 latency (64 clients) | 159,285 us | 15,343,845 us | ~100x worse |

**With virtio-fs + DAX**: Dramatic improvement over 9pfs. Near-native sequential read performance. Random write latency reduced significantly but still measurable overhead due to FUSE round-trips.

**With vhost-user-blk**: Near host-level performance for block I/O workloads. Benchmarks by Xinnor show performance within 5-10% of bare metal for NVMe devices.

### 5.3 GPU and Device Passthrough

#### 5.3.1 Mechanism: VFIO

Kata Containers exposes hardware devices to guest VMs using VFIO (Virtual Function I/O), which provides safe, non-privileged userspace device access via IOMMU (Input/Output Memory Management Unit). The VFIO path:

1. Device is unbound from its host driver.
2. Device is bound to the `vfio-pci` driver.
3. The hypervisor maps the device into the VM's address space via IOMMU.
4. The guest VM accesses the device directly (near-native performance for data plane operations).

#### 5.3.2 Feature Parity Matrix

| Feature | Native (runc) | Kata Containers | Gap Assessment |
|---|---|---|---|
| Single GPU access | `--device /dev/nvidia0` | VFIO passthrough (requires IOMMU) | Behavioral difference (VFIO vs. direct) |
| Multi-GPU (same container) | Trivial (`--device` per GPU) | **NOT supported** | **Critical gap** |
| Fractional GPU (MIG, vGPU) | NVIDIA MIG, vGPU supported | vGPU: **NOT supported**; MIG: limited | **Critical gap** |
| GPU sharing (time-slicing) | Supported (NVIDIA MPS, time-slicing) | **NOT supported** | **Critical gap** |
| Intel GPU (GVT-g) | Supported | Supported (mediated device via VFIO) | Parity |
| NVIDIA GPU Operator | Full | Supported (containerd only, install-only, not upgrade) | Limited |
| Large BAR GPUs (e.g., Tesla P100) | Direct | Supported (Kata 1.11+, specific config) | Minor config needed |
| FPGA passthrough | Direct (`--device`) | Via VFIO | Works but requires IOMMU |
| USB device passthrough | Direct (`--device`) | Via VFIO (limited) | Limited |
| `/dev/kvm` access (nested virt) | Direct | Not meaningful (already in VM) | N/A |

#### 5.3.3 Hypervisor-Specific VFIO Support

| Hypervisor | VFIO Support | Notes |
|---|---|---|
| QEMU | Full | Most mature; supports all device types |
| Cloud Hypervisor | Full | Good support for modern devices |
| Firecracker | **None** | Deliberately excluded (minimal VMM) |
| Dragonball | Full | Supports GPU passthrough |
| StratoVirt | **None** | MicroVM mode limitation |

#### 5.3.4 Confidential Computing + GPU

NVIDIA Hopper-generation GPUs support single-GPU confidential compute passthrough when combined with Intel TDX or AMD SEV-SNP. The GPU's on-chip security engine participates in the attestation chain. NVIDIA Blackwell-generation extends this to multi-GPU confidential passthrough.

The NVIDIA GPU Operator (versions 24.6.x through 24.9.x) supports Kata Containers with confidential container configurations, enabling GPU-accelerated workloads within TEE-protected VMs.

#### 5.3.5 Impact on Backend.AI

Backend.AI's accelerator plugin system (`backendai_accelerator_v21`) supports:
- Discrete allocation (whole GPU via `DiscretePropertyAllocMap`)
- Fractional allocation (sub-GPU via `FractionAllocMap`)
- Multi-GPU allocation to single containers
- NUMA-aware placement

Kata's limitation to single-GPU VFIO passthrough per container directly conflicts with Backend.AI's multi-GPU allocation model and fractional GPU sharing via CUDA hook libraries. The VFIO approach also precludes the use of NVIDIA Container Toolkit's device mapping, which Backend.AI relies on through `generate_docker_args()` in its compute plugins.

### 5.4 Resource Management

#### 5.4.1 Dual-Layer Cgroup Architecture

Kata uses a dual-layer resource management strategy:

**Host-level cgroups**: A single cgroup per sandbox constrains the overall VM process (hypervisor + guest memory). The CRI runtime and resource manager can restrict or collect stats at the sandbox level.

**Guest-level cgroups**: Inside the VM, the kata-agent applies per-container cgroup constraints, making containers within the same VM behave like standard Linux containers with individual resource limits.

#### 5.4.2 Feature Parity Matrix

| Feature | Native (runc) | Kata Containers | Gap Assessment |
|---|---|---|---|
| CPU shares/quota | Direct cgroup | Dual-layer (host + guest cgroup) | Parity (semantic) |
| CPU pinning | Direct cgroup | VM vCPU pinning | Behavioral difference |
| Memory limits | Direct cgroup | VM memory + guest cgroup | Parity (semantic) |
| Memory swap | Supported | VM-level swap | Behavioral difference |
| OOM handling | Direct cgroup OOM killer | Guest OOM (host sees VM memory) | Different OOM behavior |
| PID limits | Direct cgroup | Guest-level PID limits | Parity |
| Block I/O weight | cgroup blkio | **NOT supported** | Gap |
| Block I/O limits (bps/iops) | cgroup blkio | Supported (at VM level) | Parity |
| CPU hotplug | N/A | QEMU, CLH: yes; FC, SV: **no** | Hypervisor-dependent |
| Memory hotplug | N/A | QEMU, CLH: yes (virtio-mem); FC: **no** | Hypervisor-dependent |
| Cgroups v2 | Full | Supported (not default) | Parity (with config) |
| `--sysctl` | Supported | **NOT supported** | Gap |

#### 5.4.3 Resource Allocation Behavior

The VM starts with a configurable minimum resource allocation (default: 1 vCPU, 2 GB RAM defined in `configuration.toml`). When containers within the pod request additional resources, the runtime hot-plugs CPU and memory into the VM. This means:

- There is a **base resource cost** per pod regardless of container resource requests.
- Hot-plug operations add latency to container startup (typically milliseconds for CPU, potentially longer for memory).
- Memory hotplug can fail if the guest kernel cannot online the hot-plugged memory due to insufficient initial memory.
- AMD CPU hotplug has reported failures in some configurations.

### 5.5 Container Image Handling

#### 5.5.1 Image Pull Models

Kata supports two distinct image pull models:

**Host Pull (Default)**

The standard model matching native container behavior:
1. containerd/CRI pulls and unpacks the OCI image on the host.
2. Image layers are exposed to the guest via filesystem passthrough:
   - virtio-fs for overlay-based graph drivers (default)
   - virtio-blk/scsi for block-based graph drivers
3. The guest mounts the shared filesystem and constructs the container rootfs.
4. Image layers can be shared across multiple sandboxes on the same node.

**Guest Pull (Confidential Containers)**

Required when the host is considered untrusted:
1. The containerd snapshotter on the host intercepts the image pull.
2. Control is redirected to `image-rs` running inside the guest VM.
3. image-rs downloads, verifies signatures, and decrypts the image within the TEE.
4. Container images never appear in plaintext on the host.
5. **Trade-off**: Images are NOT shared across sandboxes — each VM downloads its own copy.

#### 5.5.2 Nydus Image Acceleration

Available since Kata v2.4.0, Nydus provides on-demand lazy loading of container image layers:

- Research shows 76% of container startup time is spent on image pull, but only 6.4% of pulled data is actually read during execution.
- Nydus uses the RAFS v6 (Registry Acceleration File System) format, which stores image data in content-addressable chunks.
- Chunks are fetched on-demand from the registry as the container accesses files.
- In the Kata integration, `nydusd` replaces `virtiofsd` as the FUSE/virtiofs daemon, serving image data to the guest via virtio-fs.
- Supports P2P distribution via Dragonfly, reducing registry load by over 80%.

### 5.6 Multi-Container Pods

#### 5.6.1 Behavioral Equivalence

Kata's multi-container pod behavior is semantically equivalent to native Kubernetes pods:

- All containers in a pod share the **same VM** (the "sandbox").
- A single kata-agent manages all container processes within the VM.
- Containers share the network namespace (same IP, same ports), IPC namespace, and optionally PID namespace.
- Each container has its own mount namespace, cgroup, and user namespace.

The kata-agent differentiates between sandbox creation and container creation using OCI annotations:
- `io.kubernetes.cri-o.ContainerType: "sandbox"` → triggers VM creation
- `io.kubernetes.cri-o.ContainerType: "container"` → creates a container within the existing VM

#### 5.6.2 Isolation Properties

| Boundary | Native (runc) | Kata Containers |
|---|---|---|
| Inter-pod isolation | Namespace + cgroup (soft) | **Hardware VM boundary** (hard) |
| Intra-pod isolation | Namespace + cgroup | Namespace + cgroup (inside VM) — equivalent |
| Kernel sharing (inter-pod) | Shared host kernel | Separate guest kernels per pod |
| Kernel sharing (intra-pod) | Shared host kernel | Shared guest kernel within pod |

### 5.7 Security Model

#### 5.7.1 Threat Model Comparison

| Threat | Native (runc) | Kata Containers | gVisor |
|---|---|---|---|
| Container escape via kernel CVE | **Vulnerable** (shared kernel) | **Protected** (separate kernel per pod) | **Partially protected** (reduced syscall surface) |
| Container escape via runtime CVE | Vulnerable | Protected (workload in VM, not on host) | Protected (workload in Sentry) |
| Resource exhaustion (noisy neighbor) | cgroup enforcement | VM-level + cgroup enforcement (dual-layer) | cgroup enforcement |
| Network-based attack (pod-to-pod) | Network policy (soft) | Network policy + VM boundary (hard) | Network policy (soft) |
| Privilege escalation (root in container) | Host kernel exposed | Guest kernel only; host devices NOT passed | Sentry kernel only |
| Side-channel attacks (Spectre, etc.) | Vulnerable (shared kernel/CPU) | **Protected** (separate VM; can use TEE hardware) | Partially protected |
| Supply chain (malicious image) | Vulnerable | Vulnerable (unless using CoCo with attestation) | Vulnerable |

#### 5.7.2 Security Hardening Layers

Kata applies defense-in-depth:

1. **VM boundary** (KVM): Hardware-enforced memory isolation between pods.
2. **Minimal guest kernel**: Stripped-down Linux LTS with only virtio drivers, reducing attack surface.
3. **Seccomp filters**: Applied to the VMM process on the host and within the guest.
4. **AppArmor/SELinux**: Profiles applied to the VMM process and virtiofsd.
5. **Rootless VMM**: Hypervisor process can run as an unprivileged user (QEMU, CLH).
6. **Minimal guest rootfs**: Alpine-based initrd with only the kata-agent binary.
7. **Confidential computing** (optional): TEE hardware (TDX, SEV-SNP) for memory encryption and attestation.

#### 5.7.3 Syscall Compatibility

A critical differentiation from gVisor: Kata runs a **real Linux kernel** in the guest, providing full syscall compatibility (all ~330+ Linux syscalls). gVisor's Sentry intercepts syscalls and implements only a subset (~70-80%), causing compatibility issues with some workloads (particularly those using advanced filesystem operations, signaling, or less common syscalls).

This is significant for AI/ML workloads, which may use advanced Linux features (io_uring, perf events, eBPF, RDMA verbs) that gVisor does not support.

---

## 6. Performance Analysis

### 6.1 Startup Latency

| Runtime | Cold Start (typical) | With VM Templating | Notes |
|---|---|---|---|
| Native (runc) | 50-100ms | N/A | Process fork + namespace creation |
| gVisor | 50-100ms | N/A | Sentry initialization |
| Kata + QEMU | ~500ms | ~300ms | Full VM boot; most feature-complete |
| Kata + Cloud Hypervisor | ~200ms | ~125ms | Optimized boot path |
| Kata + Firecracker | ~125ms | N/A (no hotplug) | Minimal VMM; pre-allocated resources |
| Kata + Dragonball | ~200ms | ~150ms | In-process VMM; concurrent boot optimization |

**VM Templating**: Pre-boots a VM and clones it for new sandboxes. Speeds up creation by up to 38.68% and saves approximately 72% of guest memory in high-density scenarios (100 containers saved 9 GB). Currently only available in the Go runtime; migration to runtime-rs is in progress.

### 6.2 Memory Overhead

| Runtime | Per-Pod Overhead | Components |
|---|---|---|
| Native (runc) | 1-5 MB | Namespace metadata, shim process |
| gVisor | 10-50 MB | Sentry process, gofer |
| Kata + QEMU | 50-150 MB | VMM process, guest kernel, agent, virtiofsd |
| Kata + Cloud Hypervisor | 20-50 MB | Smaller VMM, same guest components |
| Kata + Firecracker | 15-30 MB | Minimal VMM, minimal guest |
| Kata + Dragonball | 20-50 MB | In-process VMM, shared memory space |

The per-pod memory overhead directly impacts container density. On a node with 256 GB RAM:
- runc: theoretical maximum ~50,000+ containers (memory-limited by workload, not runtime)
- Kata + QEMU: ~1,700 pods before overhead alone consumes all memory
- Kata + CLH/Dragonball: ~5,000 pods before overhead alone consumes all memory

### 6.3 CPU Performance

For CPU-bound workloads, Kata introduces approximately 4% overhead compared to bare metal. This is consistent across hypervisors because the overhead comes from VM exits for privileged instructions and timer interrupts, not from the VMM itself.

For system-call-heavy workloads, overhead increases to 5-15% due to the additional cost of VM exits per syscall. The exact overhead depends on syscall frequency and type.

### 6.4 I/O Performance

Storage I/O is the area of greatest performance impact. The overhead varies dramatically by filesystem sharing mechanism:

| Mechanism | Sequential Read (vs. bare metal) | Random Write p99 Latency (vs. bare metal) | Use Case |
|---|---|---|---|
| 9pfs (legacy) | ~15% of bare metal | ~100x worse | Not recommended |
| virtio-fs | ~70-90% of bare metal | ~3-10x worse | General purpose (default) |
| virtio-fs + DAX | ~90-98% of bare metal | ~2-5x worse | Recommended for I/O workloads |
| virtio-blk | ~90-95% of bare metal | ~2-3x worse | Block-based volumes |
| vhost-user-blk | ~95-100% of bare metal | ~1-2x worse | High-performance block I/O |

For Backend.AI's use case of mounting distributed storage (CephFS, NetApp) via bind mounts, the I/O path would be:

```
Container → guest kernel → virtio-fs → virtiofsd (host) → host kernel VFS → distributed FS client → network → storage cluster
```

This adds one FUSE round-trip compared to the native path (container → host kernel VFS → distributed FS client → network → storage cluster), which is measurable but not catastrophic for typical AI/ML data loading patterns.

### 6.5 Network Performance

| Metric | Native (runc) | Kata (TC-filter) | Delta |
|---|---|---|---|
| Latency overhead | Baseline | <1ms additional | Minimal |
| CPU per packet | Baseline | ~2.5x | Significant for network-heavy |
| Throughput (single stream) | Near line rate | Near line rate | Parity |
| Throughput (many streams) | Near line rate | Reduced by CPU overhead | Depends on CPU budget |
| Overlay network (VXLAN) | Standard overhead | Standard + virtio overhead | Additive |

The CPU overhead is the primary concern: network-intensive distributed training workloads (e.g., NCCL all-reduce over Ethernet) would consume significantly more CPU for the same data transfer compared to native containers.

---

## 7. Advanced Capabilities

### 7.1 Confidential Containers (CoCo)

Confidential Containers is a CNCF sandbox project that combines Kata Containers with Trusted Execution Environment (TEE) hardware to protect data in use at the pod level. The enclave boundary encompasses the workload pod, kata-agent, and helper processes. Everything outside — hypervisor, other pods, control plane, host OS — is considered untrusted.

#### 7.1.1 Supported TEE Technologies

| TEE | Vendor | RuntimeClass | Capability |
|---|---|---|---|
| Intel TDX | Intel | `kata-qemu-tdx` | Full VM memory encryption + integrity |
| AMD SEV-SNP | AMD | `kata-qemu-snp` | Full VM memory encryption + integrity |
| IBM Secure Execution | IBM | `kata-qemu-se` | s390x secure execution |
| Intel SGX | Intel | N/A (enclave-based) | Application-level enclaves |

#### 7.1.2 Architecture Components

**Attester side (inside guest VM):**
- **Attestation Agent (AA)**: Generates TEE attestation reports from hardware.
- **Confidential Data Hub (CDH)**: Manages secret and key access within the TEE.
- **image-rs**: Downloads, verifies, and decrypts container images inside the guest.

**Verifier side (external service):**
- **Key Broker Service (KBS)**: Validates guest attestation evidence and releases secrets/keys.
- **Attestation Service (AS)**: Verifies TEE evidence against reference values.
- **Reference Value Provider Service (RVPS)**: Manages trusted reference values for verification.

#### 7.1.3 Attestation Workflow

1. Workload or kata-agent requests a secret via CDH.
2. CDH triggers the AA to generate a TEE attestation report.
3. AA sends the report to KBS using the RCAR (Request-Challenge-Attestation-Response) protocol.
4. KBS forwards to AS for verification against reference values.
5. Only upon successful verification does KBS release the encryption key or secret.
6. Supports lazy attestation — triggered on-demand, not at boot.

#### 7.1.4 Production Availability

- **Azure AKS**: Confidential Containers preview with AMD SEV-SNP (DCa_cc, ECa_cc VM sizes) and Intel TDX.
- **Red Hat OpenShift**: Confidential containers on bare metal via Assisted Installer.
- **NVIDIA GPU Operator**: GPU workloads within confidential containers (Hopper GPUs).

### 7.2 Peer Pods / Remote Hypervisor

Peer pods extend Kata so that the pod sandbox VM runs **outside** the Kubernetes worker node as a first-class cloud VM, created via cloud provider IaaS APIs. This addresses two key limitations:

1. **No nested virtualization required**: The VM is a first-level instance, not nested inside a worker node VM.
2. **TEE VMs on demand**: Cloud APIs can provision TEE-enabled VMs (e.g., AMD SEV-SNP instances) for confidential workloads.

The Cloud API Adaptor (CAA) DaemonSet runs on each worker node, translating sandbox lifecycle commands into cloud provider API calls (EC2, Azure Compute, GCE, Libvirt). A VxLAN tunnel provides network connectivity between the pod's network namespace on the worker and the peer pod VM.

Persistent volume support has been developed for peer pods, addressing storage attachment to remote VMs.

### 7.3 Nydus Image Acceleration

Nydus is a CNCF project providing a container image format (RAFS — Registry Acceleration File System) that supports on-demand lazy loading. In the Kata integration:

1. `nydusd` replaces `virtiofsd` as the FUSE/virtiofs daemon.
2. On sandbox creation, nydusd starts and the VM mounts the virtiofs share.
3. On container creation, the shim instructs nydusd to mount a RAFS filesystem for the container's image layers.
4. The guest constructs an overlay filesystem combining the lazy-loaded RAFS layer with snapshot directories.
5. Image data is fetched from the registry on-demand as files are accessed.

Performance impact: Significantly reduces cold start time for large images. Instead of pulling a 10GB ML framework image entirely before starting, only the immediately needed files are fetched, with remaining data loaded in the background.

### 7.4 Monitoring and Observability

#### 7.4.1 Metrics Architecture

Kata 2.0+ implements a pull-based metrics system integrated with Prometheus:

- **Zero overhead when not monitored**: Metrics are collected only when Prometheus scrapes the endpoint.
- **Stateless**: No metrics held in memory between scrapes.
- **Source**: Primarily from `/proc` filesystem for minimal performance impact.

#### 7.4.2 kata-monitor

A per-node management agent that:
- Aggregates metrics from running sandboxes, attaching `sandbox_id` labels.
- Attaches Kubernetes metadata (`cri_uid`, `cri_name`, `cri_namespace`).
- Provides a single Prometheus scrape target per node.
- The shim's metrics socket is at `vc/sbs/${PODID}/shim-monitor.sock`.

#### 7.4.3 Metric Categories

1. **Kata Agent Metrics**: Process statistics from guest `/proc/<pid>/[io, stat, status]`.
2. **Guest OS Metrics**: Guest system-level data from `/proc/[stats, diskstats, meminfo, vmstats]` and `/proc/net/dev`.
3. **Hypervisor Metrics**: VMM process resource consumption.
4. **Shim Metrics**: Runtime process observations.

Performance characteristics:
- End-to-end latency (Prometheus to kata-monitor): ~20ms average
- Agent RPC latency (shim to agent): ~3ms average
- Metrics payload per sandbox: ~144KB uncompressed, ~10KB gzipped

#### 7.4.4 External Integrations

- Grafana Cloud (Prometheus-based)
- Datadog (containerd endpoint-based, zero additional setup)
- Red Hat OpenShift Monitoring (integrated for sandboxed containers)

---

## 8. Known Limitations and Unsupported Features

### 8.1 Comprehensive Limitation Inventory

| Feature | Status | Impact Level | Notes |
|---|---|---|---|
| `--net=host` (host networking) | Not supported | High | Fundamental VM limitation; cannot share host network namespace |
| `--link` (container linking) | Not supported | Low | Deprecated in Docker; replaced by user-defined networks |
| `--shm-size` | Not implemented | Medium | `/dev/shm` sizing broken with tmpfs emptyDir; capped at 64KB |
| `--sysctl` | Not implemented | Medium | Cannot tune guest kernel parameters from host |
| `checkpoint` / `restore` (CRIU) | Not implemented | High | No live migration or suspend/resume; open issue since April 2021 |
| Live VM migration | Not implemented | High | Underlying hypervisors support it but integration is unsolved |
| Block I/O weight (cgroups) | Not supported | Low | Other blkio controls (bps, iops) work |
| `events` (OOM notifications) | Partial | Medium | OOM and Intel RDT stats incomplete |
| `volumeMount.subPath` | Not supported | Medium | Kubernetes volume limitation |
| Podman integration | Not supported | Medium | Docker supported since 22.06 |
| Multi-GPU passthrough | Not supported | **Critical** | Single GPU only via VFIO |
| NVIDIA vGPU | Not supported | **Critical** | Cannot share a physical GPU across multiple Kata VMs |
| GPU time-slicing (MPS) | Not supported | **Critical** | Requires host-side MPS daemon access |
| Network namespace sharing | Broken | Medium | Takes over interfaces, breaking connectivity |
| Full rootless operation | Partial | Medium | Only VMM is rootless; shim + virtiofsd still need root |
| Docker Compose | Limited | Low | Basic support; advanced features may not work |
| `docker exec` with TTY | Supported | — | Works via kata-agent ExecProcess API |
| Privileged containers | Behavioral difference | Medium | Host devices NOT passed by default; must be explicitly configured |

### 8.2 Hypervisor-Specific Feature Gaps

| Feature | QEMU | Cloud Hypervisor | Firecracker | Dragonball | StratoVirt |
|---|---|---|---|---|---|
| CPU hotplug | Yes | Yes | **No** | Yes | **No** |
| Memory hotplug | Yes | Yes | **No** | Yes | **No** |
| Disk hotplug | Yes | Yes | **No** | Yes | Yes |
| VFIO passthrough | Yes | Yes | **No** | Yes | **No** |
| virtio-fs | Yes | Yes | **No** | Yes | Yes |
| 9pfs | Yes | No | No | No | No |
| VM templating | Yes | Yes | N/A | In progress | N/A |
| Confidential computing | TDX, SEV-SNP | TDX, SEV-SNP | No | Planned | No |
| Rootless VMM | Yes | Yes | Jailer mechanism | In progress | No |

### 8.3 Compatibility Issues

- **Docker 26.0.0**: Broke Kata networking (`io.containerd.run.kata.v2`), demonstrating fragility in integration points. Workarounds were required.
- **AMD CPU hotplug**: Reported failures in some configurations (GitHub issue #2875).
- **Memory hotplug with low initial memory**: Can fail if guest kernel cannot online hot-plugged memory.
- **Cgroups v2**: Supported but not default; requires explicit configuration in `configuration.toml` and guest kernel command line.

---

## 9. Production Adoption

### 9.1 Major Adopters

**Ant Group (Alibaba)**
- Using Kata Containers in production since 2019.
- Thousands of tasks scheduled on Kata across thousands of nodes.
- Co-locates online applications and batch jobs.
- Built AntCWPP (Cloud Workload Protection Platform) combining Kata with eBPF for defense-in-depth: eBPF programs attached to LSM hooks and network control points inside the Kata VM kernel.
- Successfully eliminated container escape risks, detected reverse shells, fileless malware, and policy drift.
- Reduced per-payment energy consumption by 50% through improved workload co-location enabled by strong isolation.

**IBM Cloud**
- Deploys Kata for Cloud Shell and CI/CD Pipeline SaaS offerings.
- CI/CD platform scaled 30-40x over five years with sustained ~10% monthly growth.
- Uses Kubernetes with Tekton as pipeline orchestrator; Kata plugs directly into the existing stack.
- Key challenge identified: filesystem/snapshotter setup for the Kata guest is complex and needs simplification.
- Anticipates increasing demand as AI-driven automation generates more workloads requiring secure isolation.

**Northflank**
- Runs over 2 million microVMs per month inside Kubernetes.
- Uses Kata Containers with Cloud Hypervisor in production.
- Multi-tenant platform where security is essential for running untrusted images.
- Developed custom tooling for running Kata on GKE with custom node images.
- Had to customize virtiofs settings and enable non-default kernel features, requiring custom Kata builds.

**Microsoft Azure**
- Pod Sandboxing feature on AKS uses Kata Containers.
- Confidential Containers preview with AMD SEV-SNP and Intel TDX.
- Reported as "extremely well-received by internal and external AKS customers" since February 2023 preview.

**AWS**
- Documents Kata integration with EKS for enhanced workload isolation.
- Requires bare-metal EC2 instances (e.g., `m5.metal`, `c5.metal`) as worker nodes.

**Baidu**
- Runs Kata in production for Function Computing, Cloud Container Instances, and Edge Computing.

### 9.2 Lessons Learned from Production Deployments

1. **Seamless Kubernetes integration** is Kata's greatest operational strength — workloads require minimal configuration changes beyond specifying `runtimeClassName`.
2. **Filesystem/snapshotter complexity** is the biggest barrier to adoption (cited by IBM Cloud).
3. **Custom Kata builds may be required** for advanced use cases (virtiofs tuning, kernel features — cited by Northflank).
4. **VMM selection significantly impacts operational profile**: Cloud Hypervisor is preferred for performance, QEMU for feature completeness.
5. **Defense in depth is essential**: Combining Kata with eBPF (as Ant Group does) provides both strong isolation and fine-grained runtime security.
6. **Steep learning curve**: Operational knowledge of both container and VM management is required.
7. **Cloud provider constraints**: Many cloud providers do not support nested virtualization on standard instances, requiring either bare-metal instances (expensive) or peer pods (complex).

---

## 10. Implications for Backend.AI

### 10.1 Compatibility Assessment

This section maps Kata Containers' capabilities against Backend.AI's four core subsystems:

#### 10.1.1 Scheduling and Orchestration

| Backend.AI Feature | Kata Compatibility | Assessment |
|---|---|---|
| Session lifecycle (PENDING→RUNNING→TERMINATED) | Compatible | Kata is transparent to the scheduler; RuntimeClass selection is the only change |
| Multi-node sessions (cluster_mode=MULTI_NODE) | Compatible | Overlay networking works with Kata (additional overhead) |
| Sokovan scheduler (FIFO, LIFO, DRF) | Compatible | No scheduler changes needed; resource accounting must include VM overhead |
| Agent-Manager RPC (ZeroMQ/Callosum) | Compatible | Agent runs on host; manages Kata containers via containerd |
| Session priority and deprioritization | Compatible | No changes needed |
| Hot-plug resources during session | Partially compatible | Depends on hypervisor; QEMU/CLH support hot-plug |
| Idle session detection and timeout | Compatible | Metrics available via kata-monitor |

**Key consideration**: Resource accounting must include the per-pod VM overhead (15-150MB memory, CPU for VMM). The scheduler's `available_slots` calculation on agents must subtract this overhead per expected concurrent session.

#### 10.1.2 Overlay Networking

| Backend.AI Feature | Kata Compatibility | Assessment |
|---|---|---|
| Docker Swarm overlay networks | Compatible | Kata's TC-filter/MACVTAP works with overlay |
| Multi-container SSH (cluster_ssh_port_mapping) | Compatible | SSH within VM overlay works |
| Port exposure (service ports) | Compatible | Kata network plugin expose_ports() equivalent |
| RDMA / InfiniBand | Partially compatible | Requires VFIO passthrough; hypervisor-dependent |
| MPI over overlay (OMPI) | Compatible | Kata sets OMPI_MCA_btl_tcp_if_exclude automatically |

**Key consideration**: Network-intensive distributed training (NCCL all-reduce) will consume approximately 2.5x more CPU per packet due to the virtio-net path. For GPU-heavy training where network is the bottleneck, this overhead may be acceptable since GPUs consume most wall-clock time.

#### 10.1.3 Distributed Storage

| Backend.AI Feature | Kata Compatibility | Assessment |
|---|---|---|
| VFolder bind mounts (VFolderMount → Docker bind mount) | Compatible | Via virtio-fs passthrough (overhead) |
| CephFS / NetApp / WekaFS mounts | Compatible | Host-side FS client + virtio-fs to guest |
| Intrinsic mounts (/home/work, /home/config) | Compatible | Via virtio-fs |
| Multiple vfolders per session | Compatible | Multiple bind mounts via virtio-fs |
| Read-only / read-write permissions | Compatible | Virtio-fs supports RO/RW |
| /home/config/resource.txt (KernelResourceSpec) | Compatible | Written via virtio-fs shared mount |

**Key consideration**: Every I/O operation traverses the virtio-fs FUSE path, adding measurable latency. For AI/ML workloads with large dataset loading (e.g., reading training data from CephFS), this overhead is most noticeable during data pipeline phases. GPU compute phases are unaffected.

#### 10.1.4 Accelerator Management

| Backend.AI Feature | Kata Compatibility | Assessment |
|---|---|---|
| Single GPU allocation (DiscretePropertyAllocMap) | Compatible | Via VFIO passthrough |
| Multi-GPU allocation (2+ GPUs per container) | **NOT compatible** | Kata limits to single GPU via VFIO |
| Fractional GPU (FractionAllocMap, cuda.shares) | **NOT compatible** | VFIO passes whole GPU; no hook library support |
| CUDA hook libraries (generate_hooks()) | **NOT compatible** | Host-side hook injection does not work across VM boundary |
| NVIDIA Container Toolkit (generate_docker_args()) | **NOT compatible** | Toolkit's device mapping requires host kernel driver sharing |
| GPU metrics (gather_node_measures()) | Partially compatible | VFIO GPU metrics must come from guest-side monitoring |
| NUMA-aware allocation (AffinityHint) | Partially compatible | VM vCPU pinning can respect NUMA; GPU NUMA irrelevant with VFIO |
| ROCm, Habana, IPU, TPU plugins | Partially compatible | VFIO passthrough for each; single device only |
| Xilinx FPGA (fractional) | **NOT compatible** | Fractional allocation requires host-side arbitration |

**This is the most significant incompatibility.** Backend.AI's core value proposition includes fractional GPU sharing and multi-GPU allocation, both of which are fundamentally incompatible with Kata's VFIO passthrough model.

### 10.2 Integration Feasibility Summary

| Criterion | Feasibility | Blocking? |
|---|---|---|
| Single-GPU workloads (inference) | **Feasible** | No |
| Multi-GPU workloads (training) | **Not feasible** | **Yes** |
| Fractional GPU workloads | **Not feasible** | **Yes** |
| CPU-only workloads | **Feasible** | No |
| Storage-intensive workloads | **Feasible with overhead** | No |
| Network-intensive distributed training | **Feasible with overhead** | No |
| Interactive notebooks (startup latency) | **Feasible** (200-500ms overhead) | Marginal |
| High-density deployments | **Feasible with reduced density** | Depends on use case |
| Confidential AI workloads | **Feasible** (compelling use case) | No |

### 10.3 Potential Integration Architecture

If Backend.AI were to support Kata as an optional runtime for specific workload classes, the integration would involve:

1. **RuntimeClass selection**: Add `runtime_class` to SessionCreationSpec, allowing users to opt into Kata isolation for specific sessions.
2. **Resource accounting adjustment**: Agents subtract per-session VM overhead from `available_slots` when Kata runtime is selected.
3. **Accelerator plugin modification**: When Kata is selected, constrain allocation to single whole-GPU VFIO mode. Disable fractional allocation and multi-GPU for Kata sessions.
4. **Storage path**: No changes needed — VFolderMount → bind mount path works through virtio-fs transparently. Accept I/O overhead.
5. **Network path**: No changes needed — Docker Swarm overlay works with Kata's TC-filter. Accept CPU overhead for network-intensive workloads.
6. **Monitoring**: Integrate kata-monitor metrics into Backend.AI's agent statistics collection.

---

## 11. Conclusions and Recommendations

### 11.1 Summary of Findings

Kata Containers provides genuine hardware-enforced isolation for containerized workloads while maintaining OCI compliance and Kubernetes integration. The Kata 3.x Rust rewrite and built-in Dragonball VMM have significantly improved performance and operational characteristics.

However, critical feature gaps exist for Backend.AI's primary use cases:

1. **Multi-GPU and fractional GPU allocation are not supported**, which directly conflicts with Backend.AI's core accelerator management system.
2. **Storage I/O overhead is measurable** but acceptable for most AI/ML workload patterns (data loading is typically not the bottleneck).
3. **Network overhead** (2.5x CPU for network-intensive workloads) is relevant for distributed training but may be acceptable when GPU compute dominates wall-clock time.
4. **Cold start overhead** (125-500ms) is noticeable for interactive sessions but unlikely to be a dealbreaker.
5. **Checkpoint/restore is not supported**, preventing session migration or suspend/resume features.

### 11.2 Recommendations

**Short-term**: Do not adopt Kata as a general-purpose runtime for Backend.AI sessions. The GPU incompatibilities are fundamental and cannot be worked around without architectural changes to either Backend.AI or Kata.

**Medium-term**: Consider supporting Kata as an **optional isolation mode** for specific workload classes:
- CPU-only workloads in multi-tenant environments
- Single-GPU inference workloads where security isolation is required
- Confidential computing workloads (CoCo with TDX/SEV-SNP) for privacy-sensitive AI

**Long-term**: Monitor these Kata developments:
- Multi-GPU VFIO passthrough (NVIDIA Blackwell enables this for confidential containers)
- CDI (Container Device Interface) integration for standardized device management
- Runtime-rs reaching full feature parity with the Go runtime (Kata 4.0 target)
- Improvements to vGPU and MIG support within VMs

### 11.3 Alternative Approaches

For multi-tenant isolation without Kata's GPU limitations:
- **gVisor**: Provides kernel-level isolation without VMs, but has syscall compatibility limitations that may affect AI/ML workloads.
- **NVIDIA MIG + namespace isolation**: Hardware GPU partitioning with standard container isolation; no VM overhead but weaker isolation boundary.
- **Firecracker (direct)**: For serverless/FaaS-style workloads without GPU requirements; excellent density and startup time.
- **Kata + GPU operator evolution**: NVIDIA is actively developing confidential multi-GPU support; this may resolve the GPU limitation within 1-2 years.

---

## 12. References

### Official Documentation
1. Kata Containers Architecture Design. https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/README.md
2. Kata Containers Virtualization Design. https://github.com/kata-containers/kata-containers/blob/main/docs/design/virtualization.md
3. Kata Containers Hypervisor Comparison. https://github.com/kata-containers/kata-containers/blob/main/docs/hypervisors.md
4. Kata Containers Limitations. https://github.com/kata-containers/kata-containers/blob/main/docs/Limitations.md
5. Kata Containers Guest Assets. https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/guest-assets.md
6. Kata Containers 2.0 Metrics Design. https://github.com/kata-containers/kata-containers/blob/main/docs/design/kata-2-0-metrics.md
7. Kata Nydus Design Document. https://github.com/kata-containers/kata-containers/blob/main/docs/design/kata-nydus-design.md
8. Kata Containers Rootless VMM Guide. https://github.com/kata-containers/kata-containers/blob/main/docs/how-to/how-to-run-rootless-vmm.md
9. Kata Containers with Kubernetes. https://github.com/kata-containers/kata-containers/blob/main/docs/how-to/run-kata-with-k8s.md

### Blog Posts and Case Studies
10. Getting Rust-y: Introducing Kata Containers 3.0.0. https://katacontainers.io/blog/getting-rust-y-introducing-kata-containers-3-0-0/
11. Kata 3.0 Technical Deep Dive (Alibaba Cloud). https://www.alibabacloud.com/blog/kata-3-0-is-coming-start-experiencing-the-out-of-the-box-secure-container_599575
12. Kata Containers 3.5.0 Release Overview. https://katacontainers.io/blog/kata-containers-3-5-0-release-overview/
13. Kata Containers Project Updates Q4 2024. https://katacontainers.io/blog/kata-containers-project-updates-q4-2024/
14. Kata Community PTG Updates October 2025. https://katacontainers.io/blog/kata-community-ptg-updates-october-2025/
15. IBM Cloud Kata Case Study. https://katacontainers.io/blog/kata-containers-ibm-cloud-updates/
16. Northflank Kata Case Study. https://katacontainers.io/blog/kata-containers-northflank-case-study/
17. Ant Group Kata + eBPF Whitepaper. https://katacontainers.io/collateral/kata-containers-ant-group_whitepaper.pdf
18. Ant Group Container Security with eBPF. https://ebpf.foundation/ant-group-secures-their-platform-with-kata-containers-and-ebpf-for-fine-grained-control/

### Performance Benchmarks
19. StackHPC Kata I/O Performance Analysis. https://www.stackhpc.com/kata-io-1.html
20. Xinnor vhost-user-blk Performance. https://xinnor.io/blog/bridging-the-storage-performance-gap-in-kata-containers-with-vhost-user-and-xiraid-opus-using-phison-x200-nvme-drives/
21. OpenShift Sandboxed Containers Network Performance. https://www.redhat.com/en/blog/openshift-sandboxed-containers-network-performance
22. Runtime Comparison: gVisor vs Kata vs Firecracker (2025). https://onidel.com/blog/gvisor-kata-firecracker-2025

### Cloud Provider Documentation
23. AWS: Enhancing Kubernetes Workload Isolation with Kata. https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/
24. Azure AKS Pod Sandboxing. https://learn.microsoft.com/en-us/azure/aks/use-pod-sandboxing
25. Azure AKS Confidential Containers Overview. https://learn.microsoft.com/en-us/azure/aks/confidential-containers-overview
26. NVIDIA GPU Operator with Kata. https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/24.9.2/gpu-operator-kata.html
27. NVIDIA GPU Operator with Confidential Containers. https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/24.9.1/gpu-operator-confidential-containers.html

### Confidential Computing
28. Confidential Containers Design Overview. https://confidentialcontainers.org/docs/architecture/design-overview/
29. Red Hat: Introducing Confidential Containers on Bare Metal. https://www.redhat.com/en/blog/introducing-confidential-containers-bare-metal
30. Intel: Confidential Containers Made Easy. https://www.intel.com/content/www/us/en/developer/articles/technical/confidential-containers-made-easy.html
31. Cloud API Adaptor (Peer Pods) Architecture. https://github.com/confidential-containers/cloud-api-adaptor/blob/main/docs/architecture.md

### Comparison Articles
32. Kata vs Firecracker vs gVisor (Northflank). https://northflank.com/blog/kata-containers-vs-firecracker-vs-gvisor
33. Edera Isolation Comparison. https://edera.dev/stories/kata-vs-firecracker-vs-gvisor-isolation-compared
34. Kata Containers for Docker in 2024. https://medium.com/@filippfrizzy/kata-containers-for-docker-in-2024-1e98746237ca
