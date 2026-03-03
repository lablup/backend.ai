---
Author: Kyujin Cho (kyujin@lablup.com)
Status: Draft
Created: 2026-02-27
Created-Version: 26.3.0
Target-Version:
Implemented-Version:
---

<!-- context-for-ai
type: master-bep
scope: Add Kata Containers as a third container backend (KataAgent) with VFIO GPU passthrough
detail-docs: [configuration-deployment.md, kata-agent-backend.md, storage-compatibility.md, networking.md, vfio-accelerator-plugin.md, scheduler-integration.md, migration-compatibility.md]
key-constraints:
  - Full AbstractAgent implementation, NOT a RuntimeClass annotation
  - Whole-GPU VFIO passthrough only, NO fractional GPU
  - DiscretePropertyAllocMap for cuda.device slot type
  - Must not break existing DockerAgent or KubernetesAgent deployments
key-decisions:
  - KataAgent as independent backend, not a Docker runtime flag
  - VFIO passthrough for GPU, not nvidia-container-runtime in guest
  - New CUDAVFIOPlugin separate from existing CUDAPlugin
  - Homogeneous scaling groups (one backend type per group)
  - VM memory overhead as agent-level deduction from available_slots
  - No new storage interface; virtio-fs is the transparent compatibility layer for bind mounts
  - Calico CNI for inter-VM networking (multi-host, network policy); /etc/hosts for hostname resolution
implementation: 4 phases
-->

# Kata Containers Agent Backend

## Related Issues

- Technical Report: [TR-2026-001](../docs/reports/kata-containers-feature-parity-analysis.md)

## Motivation

Backend.AI's current container backends (Docker, Kubernetes) rely on Linux namespaces and cgroups for isolation. These share the host kernel — a single kernel vulnerability in any container can compromise the entire host and all co-located workloads. This is insufficient for multi-tenant GPU environments where untrusted code runs alongside sensitive models.

Kata Containers 3.x addresses this by running each container inside a lightweight VM with its own guest kernel, providing hardware-enforced isolation via KVM. The Rust-based runtime with built-in Dragonball VMM achieves cold start times of 125-500ms and per-VM memory overhead of 15-150MB — acceptable for AI/ML workloads where GPU compute dominates wall-clock time.

For GPU workloads, VFIO (Virtual Function I/O) passthrough assigns whole GPUs directly to guest VMs via IOMMU, achieving near-native compute performance. This model naturally aligns with discrete GPU allocation (`cuda.device`) — fractional GPU sharing is neither supported nor needed, as the target workloads require dedicated GPU resources with strong isolation guarantees.

Additionally, Kata's integration with Confidential Containers (CoCo) and TEE hardware (Intel TDX, AMD SEV-SNP) enables privacy-preserving AI workloads where even the host operator cannot access model weights or training data in memory.

## Document Index

| Document | Description | Phase |
|----------|-------------|-------|
| [Configuration & Deployment](BEP-1049/configuration-deployment.md) | `[kata]` config section, hypervisor selection, host requirements | 1 |
| [KataAgent Backend](BEP-1049/kata-agent-backend.md) | KataAgent, KataKernel, KataKernelCreationContext | 1 |
| [Storage Compatibility](BEP-1049/storage-compatibility.md) | virtio-fs mount translation, lxcfs/socket exceptions, I/O analysis | 1 |
| [Networking](BEP-1049/networking.md) | Calico CNI integration, inter-VM networking, network policy, hostname resolution | 1 |
| [VFIO Accelerator Plugin](BEP-1049/vfio-accelerator-plugin.md) | CUDAVFIOPlugin, IOMMU group detection, device passthrough | 2 |
| [Scheduler Integration](BEP-1049/scheduler-integration.md) | Agent backend tracking, scaling group policy, VM overhead | 3 |
| [Migration & Compatibility](BEP-1049/migration-compatibility.md) | Additive rollout, backward compatibility, rollback plan | All |

## Design Overview

```
AbstractAgent[KernelObjectType, KernelCreationContextType]
├── DockerAgent[DockerKernel, DockerKernelCreationContext]       ← existing
├── KubernetesAgent[KubernetesKernel, KubernetesKernelCreationContext]  ← existing
└── KataAgent[KataKernel, KataKernelCreationContext]             ← proposed
```

KataAgent manages containers via containerd with the Kata shim (`io.containerd.kata.v2`). Container lifecycle differs from Docker: VM boot → virtio-fs mount setup → VSOCK agent connection → container spawn inside guest. GPU devices are assigned via VFIO passthrough at VM creation time, binding PCI devices directly into the guest's address space through IOMMU.

Storage (scratch dirs, vfolders) is shared via virtio-fs, which provides near-native I/O with DAX mapping. Network traffic traverses a virtio-net path with TC-filter mirroring — Kata's TC filter transparently redirects traffic between host-side veth interfaces and guest-side tap devices, making VMs transparent to the CNI layer. Calico CNI provides multi-host routing (BGP/VXLAN), IP allocation, and network policy enforcement for inter-session isolation. Multi-container sessions use Calico endpoint labeling for policy-based cluster communication with `/etc/hosts`-based hostname resolution.

## Implementation Plan

### Phase 1: Agent Foundation & Networking
- `KataConfig` Pydantic model and `[kata]` config section
- `KataAgent`, `KataKernel`, `KataKernelCreationContext` classes
- Container lifecycle via containerd gRPC API with Kata shim
- CPU-only workload support (no GPU yet)
- virtio-fs shared storage for scratch directories and vfolder mounts
- Calico CNI integration for multi-host inter-VM networking (BGP/VXLAN)
- Calico network policy enforcement for inter-session traffic isolation
- `/etc/hosts` injection for cluster hostname resolution

### Phase 2: VFIO Accelerator Plugin
- `CUDAVFIOPlugin` compute plugin with IOMMU group detection
- VFIO device binding and passthrough configuration
- `DiscretePropertyAllocMap` with `cuda.device` slot type
- Guest-side GPU metrics collection via VSOCK

### Phase 3: Scheduler Integration
- `backend` column on `AgentRow` with Alembic migration
- Homogeneous scaling group policy (one backend type per group)
- VM memory overhead accounting in `available_slots`
- Agent heartbeat protocol extension

### Phase 4: Confidential Computing (Future)
- CoCo integration with TDX/SEV-SNP attestation flow
- Guest image pull (images decrypted inside TEE)
- Sealed secrets via Key Broker Service
- Remote attestation endpoint

## Decision Log

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| 2026-02-27 | Full AbstractAgent backend, not RuntimeClass | RuntimeClass is K8s-only; Kata lifecycle (VM boot, VSOCK, virtio-fs) differs fundamentally from Docker API; Backend.AI already has the backend abstraction | RuntimeClass flag on DockerAgent; Docker `--runtime kata` flag |
| 2026-02-27 | VFIO-only for GPU, no fractional allocation | VFIO provides hardware isolation matching the VM boundary; fractional sharing (MPS, hook libraries) requires host kernel driver sharing which breaks isolation; target workloads need whole GPUs | nvidia-container-runtime inside guest VM (complex, shares driver stack); MIG (NVIDIA-specific, limited configurations) |
| 2026-02-27 | Separate CUDAVFIOPlugin, not modified CUDAPlugin | VFIO generates fundamentally different config (PCI addresses, IOMMU groups) vs Docker DeviceRequests; plugin discovery should keep them independent; avoids conditional logic in existing plugin | Single CUDAPlugin with backend-aware mode flag |
| 2026-02-27 | Homogeneous scaling groups | Simpler scheduling — no need for backend-aware agent filtering within a group; existing scaling group mechanism already routes sessions to agent pools | Mixed-backend groups with `allowed_backends` filter; per-session backend preference flag |
| 2026-02-27 | VM overhead as agent-level deduction | Overhead is predictable (configurable per-VM); deducting at registration avoids changing slot semantics visible to users; scheduler sees accurate available capacity | New `kata.vm_overhead` slot type; per-kernel memory inflation; soft margin in scheduler |
| 2026-02-27 | No new storage interface; reuse existing Mount abstraction with virtio-fs | Kata shim automatically translates bind mounts to virtio-fs shares — the agent passes the same mount specs and the runtime handles the VM boundary transparently; avoids duplicating mount logic | New `MountTypes.VIRTIO_FS` type (unnecessary abstraction); agent-managed virtiofsd (complexity without benefit) |
| 2026-02-27 | Agent socket skipped entirely for Kata | The agent socket (`/opt/kernel/agent.sock`) is a ZMQ REP socket used only by C binaries (jail pid translation, `is-jail-enabled`), not by the Python kernel runner. Since jail is skipped for Kata and PID translation is irrelevant (VM boundary isolates PIDs), the socket, socat relay, and handler are all unnecessary. The primary agent↔kernel-runner channel (ZMQ PUSH/PULL) is already TCP-based and works across the VM boundary without changes. | TCP replacement (unnecessary — the agent socket isn't needed, not just unreachable); VSOCK (solves wrong problem) |
| 2026-02-27 | virtio-fs for all storage backends; no direct guest mounts | No vendor (VAST, Weka, NetApp, CephFS, Lustre, GPFS, Pure Storage, Dell EMC, Hammerspace) offers Kata-specific integration; CephFS benchmarks show host-client + virtio-fs outperforms guest-native-client; direct NFS mount in guest has unresolved Kata issues (silent failures, custom kernel required) | Direct NFS mount inside guest (eliminates double-hop but adds credential/lifecycle complexity); Guest-side native filesystem client (CephFS/Lustre — lower throughput than virtio-fs + DAX) |
| 2026-02-27 | Calico CNI for inter-VM networking | Production deployments require multi-host networking and inter-session traffic isolation; Calico provides both via BGP/VXLAN routing and network policy; works with Kata's TC filter transparently; supports standalone containerd (etcd datastore) and Kubernetes; consistent CNI layer across deployment modes | CNI bridge plugin (single-host only, no network policy); Cilium (MTU mismatch issues with Kata); Flannel (no network policy); Docker overlay (not available without Docker) |
| 2026-02-27 | `/etc/hosts` injection for cluster hostname resolution | Docker embedded DNS not available with containerd; `/etc/hosts` via virtio-fs is simple, immediate, and sufficient for small clusters (2-8 containers) | CoreDNS sidecar (heavyweight); containerd-managed DNS (not available); mDNS/Avahi (complex, unreliable) |
| 2026-03-03 | krunner binaries shared via virtio-fs (Phase 1), bake into guest rootfs (Phase 2) | Three-package architecture (agent/kernel/runner): the runner package provides `entrypoint.sh` + static binaries (su-exec, dropbear, tmux, ttyd, etc.), the kernel package provides `BaseRunner` Python code. Both must be inside the guest. Phase 1: share from host directory via virtio-fs (simplest, always current). Phase 2: bake into guest rootfs template to eliminate 15+ individual virtio-fs shares (~225 MB RSS savings). Versioned template naming (`kata-rootfs-{krunner_version}.qcow2`) enables atomic rollover. | Bake from day one (delays Phase 1, requires template build pipeline); Docker volume extraction (Docker volumes not available with containerd) |
| 2026-03-03 | Kata entrypoint.sh skips LD_PRELOAD, jail, and agent.sock | The runner's `entrypoint.sh` sets up `LD_PRELOAD` with libbaihook.so (unnecessary — guest kernel provides accurate sysconf), chowns `agent.sock` (unnecessary — agent socket not mounted), and references jail paths. Kata variant skips these via env var check (`BACKENDAI_CONTAINER_BACKEND=kata`) or a separate entrypoint file. All other operations (user/group creation, SSH setup, dotfiles, password generation, su-exec) remain identical. | Unified entrypoint with no conditional (would fail on missing files); completely separate entrypoint (too much duplication) |
| 2026-03-03 | resource.txt is agent-recovery-only, not consumed by kernel runner | `resource.txt` contains serialized `KernelResourceSpec` (slot allocations, mount lists, device mappings). The agent reads it for recovery after restarts (`resources.py:887-910`, `scratch/utils.py:100-103`) and resource usage tracking. The kernel runner never reads this file — it gets its configuration from `environ.txt` (environment variables for child processes) and `intrinsic-ports.json` (ZMQ/service port assignments). The VM hypervisor enforces resource limits at the VM level. | N/A (factual clarification, not a design choice) |

## Open Questions

1. Should KataAgent use containerd CRI gRPC directly, or the `ctr` / `kata-runtime` CLI? CRI gRPC is more robust but requires maintaining a gRPC client; CLI is simpler but harder to handle async.
2. How to handle image pulling — does the host pre-stage via containerd, or does Kata pull inside the guest? Host-pull is default in non-confidential mode but guest-pull is required for CoCo.
3. How to expose Kata-specific metrics (VM boot time, VSOCK latency, virtio-fs IOPS) alongside existing container metrics gathered by the agent?
4. Multi-GPU VFIO: how to validate IOMMU group isolation at device scan time? What if multiple GPUs share an IOMMU group (common on consumer hardware)?
5. Relationship with BEP-1016 (Accelerator Interface v2) — should CUDAVFIOPlugin implement the proposed `create_lifecycle_hook()` API, or the current `generate_docker_args()` API with Kata-specific return format?
6. Should `ScalingGroupOpts` gain an explicit `backend` field, or is the homogeneous-by-convention approach sufficient?
7. For CoCo (confidential computing) mode, bind mount contents are copied into the guest and changes are NOT synced back — how should this be communicated to users who expect persistent vfolder writes?

## References

- [BEP-1002: Agent Architecture](BEP-1002-agent-architecture.md) — resource management and kernel runner patterns
- [BEP-1016: Accelerator Interface v2](BEP-1016-accelerator-interface-v2.md) — lifecycle hook API proposal
- [BEP-1000: Redefining Accelerator Metadata](BEP-1000-redefining-accelerator-metadata.md) — device metadata model
- [BEP-1044: Multi-Agent Device Split](BEP-1044-multi-agent-device-split.md) — multi-agent GPU allocation
- [TR-2026-001: Kata Containers Feature Parity Analysis](../docs/reports/kata-containers-feature-parity-analysis.md)
- [Kata Containers Architecture](https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/README.md)
- [Linux VFIO Documentation](https://docs.kernel.org/driver-api/vfio.html)
- [Calico CNI Plugin Configuration](https://docs.tigera.io/calico/latest/reference/configure-cni-plugins)
- [Calico Network Policy](https://docs.tigera.io/calico/latest/network-policy/get-started/calico-policy/calico-network-policy)
