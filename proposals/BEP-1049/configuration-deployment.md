<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: Agent configuration schema for Kata backend and host deployment requirements
depends-on: []
key-decisions:
  - New [kata] section in agent unified config
  - Cloud Hypervisor as default hypervisor, QEMU as fallback
  - Config validated at agent startup with fail-fast on missing paths
-->

# BEP-1049: Configuration and Deployment

## Summary

This document defines the configuration schema additions for the Kata backend, including hypervisor selection, VFIO settings, VM resource defaults, and host deployment prerequisites. The `[kata]` section is added to the agent's unified config (`AgentUnifiedConfig` at `src/ai/backend/agent/config/unified.py`).

## Current Design

The agent backend is selected via `local_config.agent_common.backend`, which reads the `AgentBackend` enum (`src/ai/backend/agent/types.py:36`). The `get_agent_discovery()` function (`types.py:84`) dynamically imports the backend package.

Docker-specific configuration lives in the `[container]` section:

```toml
[container]
stats-type = "docker"
sandbox-type = "jail"
scratch-root = "/tmp/scratches"
```

There is no VM or hypervisor configuration in the current schema.

## Proposed Design

### Backend Selection

```toml
[agent]
backend = "kata"  # "docker" | "kubernetes" | "kata"
```

When `backend = "kata"`, the agent imports `ai.backend.agent.kata` and instantiates `KataAgentDiscovery`.

### Kata Configuration Section

```toml
[kata]
# --- Hypervisor ---
hypervisor = "cloud-hypervisor"  # "cloud-hypervisor" | "qemu" | "dragonball"

# --- VM Defaults ---
default-vcpus = 2               # Initial vCPUs per VM (hot-plugged as needed)
default-memory-mb = 2048        # Initial memory per VM in MB
vm-overhead-mb = 64             # Per-VM memory overhead deducted from host capacity

# --- Guest VM Image (NOT the container image — see note below) ---
kernel-path = "/opt/kata/share/kata-containers/vmlinux.container"
initrd-path = ""                # Empty = use rootfs image instead of initrd
rootfs-path = "/opt/kata/share/kata-containers/kata-containers.img"

# --- Storage ---
shared-fs = "virtio-fs"         # "virtio-fs" | "virtio-9p" (9p deprecated)
virtiofsd-path = "/opt/kata/libexec/virtiofsd"
virtio-fs-cache-size = 0        # DAX window in MB; 0 = disabled (recommended default)

# --- Networking ---
network-model = "tcfilter"      # "tcfilter" | "macvtap"

# --- VFIO ---
enable-iommu = true
hotplug-vfio = "root-port"      # "root-port" | "bridge-port" | "no-port"

# --- Containerd ---
containerd-socket = "/run/containerd/containerd.sock"
kata-runtime-class = "kata"     # RuntimeClass name registered in containerd

# --- Confidential Computing (Phase 4) ---
confidential-guest = false
guest-attestation = ""          # "tdx" | "sev-snp" | ""
```

### Guest VM Image vs Container Image

Kata Containers uses **two separate filesystem layers** that must not be confused:

1. **Guest VM rootfs** (`rootfs-path` above): A minimal mini-OS image containing only the kata-agent, systemd, and essential utilities. This is the VM's boot disk — shared across all VMs, read-only, and mounted via DAX on a `/dev/pmem*` device inside the guest. It is **not** the user's container image. This is an infrastructure-level asset analogous to a VM template.

2. **Container image** (e.g., `cr.backend.ai/stable/python-tensorflow:2.15-py312-cuda12.3`): The user-selected OCI image that Backend.AI's image management system resolves. containerd pulls this on the host (same as Docker), and the Kata shim mounts it into the guest via virtio-fs or block device passthrough. The kata-agent inside the guest uses it as the container's root filesystem.

```
Host: containerd pulls OCI image (e.g., tensorflow:latest)
  │
  ├─ Kata shim detects image storage backend:
  │   ├─ overlayfs snapshotter → share via virtio-fs
  │   └─ devicemapper snapshotter → attach as virtio-blk block device
  │
  └─ Guest VM boots from kata-containers.img (mini-OS)
       └─ kata-agent mounts container rootfs inside the guest
           └─ Container process runs on the OCI image filesystem
```

**No changes to Backend.AI's image management are needed.** The image registry, image selection, and containerd pull flow are identical to Docker. Only the last mile differs — Kata transports the image into the guest VM instead of using a host-kernel bind mount.

For **confidential computing** (Phase 4), images are pulled and decrypted **inside the guest** using `image-rs` (the host is untrusted and must not see image contents). This is not the standard flow and requires additional CoCo components.

### Pydantic Config Model

```python
class KataConfig(BaseConfigSchema):
    hypervisor: Literal["cloud-hypervisor", "qemu", "dragonball"] = "cloud-hypervisor"

    # VM defaults
    default_vcpus: int = 2
    default_memory_mb: int = 2048
    vm_overhead_mb: int = 64

    # Guest image
    kernel_path: Path = Path("/opt/kata/share/kata-containers/vmlinux.container")
    initrd_path: Path | None = None
    rootfs_path: Path = Path("/opt/kata/share/kata-containers/kata-containers.img")

    # Storage
    shared_fs: Literal["virtio-fs", "virtio-9p"] = "virtio-fs"
    virtiofsd_path: Path = Path("/opt/kata/libexec/virtiofsd")
    virtio_fs_cache_size: int = 0

    # Networking
    network_model: Literal["tcfilter", "macvtap"] = "tcfilter"

    # VFIO
    enable_iommu: bool = True
    hotplug_vfio: Literal["root-port", "bridge-port", "no-port"] = "root-port"

    # Containerd
    containerd_socket: Path = Path("/run/containerd/containerd.sock")
    kata_runtime_class: str = "kata"

    # Confidential computing (Phase 4)
    confidential_guest: bool = False
    guest_attestation: Literal["tdx", "sev-snp", ""] = ""
```

Integration in `AgentUnifiedConfig`:

```python
class AgentUnifiedConfig(BaseConfigSchema):
    # ... existing fields ...
    kata: KataConfig | None = None  # Only present when backend = "kata"
```

### Startup Validation

At `KataAgent.__ainit__()`, validate:

1. `kernel_path` exists and is readable
2. `rootfs_path` (or `initrd_path`) exists and is readable
3. `virtiofsd_path` exists and is executable
4. `containerd_socket` exists and is connectable
5. Kata runtime class is registered in containerd config
6. If `enable_iommu`: IOMMU is enabled in the kernel (`/sys/class/iommu` is non-empty)
7. `vhost_vsock` kernel module is loaded

Fail fast with descriptive error messages on any validation failure.

### Hypervisor Comparison

| Feature | Cloud Hypervisor | QEMU | Dragonball |
|---------|-----------------|------|------------|
| Boot time | ~125ms | ~300ms | ~100ms |
| Memory overhead | ~15MB | ~60MB | ~10MB |
| VFIO passthrough | Yes | Yes | Yes |
| virtio-fs | Yes | Yes | Yes |
| CPU/mem hotplug | Yes | Yes | Yes |
| Confidential (TDX/SEV) | Yes | Yes | No |
| Code size | ~50K LOC (Rust) | ~2M LOC (C) | Rust (in-process) |
| Maturity | Production | Production | Production (Alibaba) |

**Default: Cloud Hypervisor** — best balance of feature completeness, security (small Rust codebase), and performance. QEMU recommended only for confidential computing on older hardware or non-x86 architectures.

## Host Deployment Requirements

### Kernel and Hardware

- Linux kernel >= 5.10 with KVM enabled
- Intel VT-x/VT-d or AMD-V/AMD-Vi (IOMMU)
- Kernel parameters: `intel_iommu=on iommu=pt` (Intel) or `amd_iommu=on iommu=pt` (AMD)
- Kernel modules: `kvm`, `kvm_intel`/`kvm_amd`, `vfio`, `vfio_pci`, `vfio_iommu_type1`, `vhost_vsock`

### Software

- Kata Containers 3.x (`kata-runtime`, guest kernel, guest rootfs/initrd)
- containerd >= 1.7 with Kata shim (`io.containerd.kata.v2`)
- virtiofsd (included in Kata installation)

### containerd Configuration

```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
  runtime_type = "io.containerd.kata.v2"
  privileged_without_host_devices = true

  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata.options]
    ConfigPath = "/opt/kata/share/defaults/kata-containers/configuration.toml"
```

### VFIO GPU Binding

GPUs intended for VFIO passthrough must be unbound from the `nvidia` driver and bound to `vfio-pci`:

```bash
# Identify GPU PCI addresses
lspci -nn | grep -i nvidia

# Bind to vfio-pci (example for 0000:41:00.0)
echo "0000:41:00.0" > /sys/bus/pci/devices/0000:41:00.0/driver/unbind
echo "10de 2684" > /sys/bus/pci/drivers/vfio-pci/new_id

# Verify
ls -la /dev/vfio/
```

For persistent binding, use `driverctl` or modprobe configuration.

## Implementation Notes

- `KataConfig` is validated at agent startup; the agent refuses to start if prerequisites are not met
- The `generate-sample` CLI command should include the `[kata]` section with comments
- Hypervisor binary paths can be auto-detected from `kata-runtime env` output
- The `[container]` section's `scratch-root` and `port-range` settings are reused by KataAgent
