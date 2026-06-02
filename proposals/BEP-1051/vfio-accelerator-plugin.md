<!-- context-for-ai
type: detail-doc
parent: BEP-1051 (Kata Containers Agent Backend)
scope: VFIO-based GPU passthrough compute plugin for Kata backend
depends-on: [kata-agent-backend.md]
key-decisions:
  - New CUDAVFIOPlugin separate from existing CUDAPlugin
  - DiscretePropertyAllocMap only (no FractionAllocMap)
  - Device discovery via sysfs PCI scan (not NVML)
  - IOMMU group validation at device scan time
  - GPUDirect RDMA support via Kata VRA: PCIe topology replication (switch-port mode), clique-id P2P grouping, GPU+NIC co-passthrough
  - InfiniBand HCA passthrough alongside GPU requires BAR sizing fix (Kata 3.8+) and RDMA device plugin
-->

# BEP-1051: VFIO Accelerator Plugin

## Summary

A new `CUDAVFIOPlugin` compute plugin manages NVIDIA GPUs via VFIO passthrough for Kata VMs. Unlike the existing `CUDAPlugin` which uses Docker's `DeviceRequests` API and NVML, this plugin discovers devices via sysfs PCI enumeration, validates IOMMU group isolation, and produces VFIO device assignment configuration consumed by `KataKernelCreationContext`.

## Current Design

The existing `CUDAPlugin` (`src/ai/backend/accelerator/cuda_open/plugin.py`):

```python
# Device discovery via NVML/libcudart
async def list_devices(self) -> Collection[CUDADevice]:
    count = libcudart.get_device_count()
    for idx in range(count):
        props = libcudart.get_device_props(idx)
        # Uses nvidia driver to enumerate devices

# Docker-specific GPU attachment
async def generate_docker_args(self, docker, device_alloc):
    return {
        "HostConfig": {
            "DeviceRequests": [{
                "Driver": "nvidia",
                "DeviceIDs": assigned_device_ids,
                "Capabilities": [["utility", "compute", "video", "graphics"]],
            }]
        }
    }

# Allocation via DiscretePropertyAllocMap
async def create_alloc_map(self) -> AbstractAllocMap:
    return DiscretePropertyAllocMap(
        device_slots={
            dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1))
            for dev in devices
        },
    )
```

Key incompatibilities with Kata/VFIO:
1. NVML requires the `nvidia` driver loaded; in VFIO mode, GPUs are bound to `vfio-pci`
2. `DeviceRequests` is a Docker API concept; Kata uses VFIO device annotations
3. Host-side metrics (NVML) are unavailable when device is bound to `vfio-pci`

## Proposed Design

### Package Structure

```
src/ai/backend/accelerator/cuda_vfio/
├── __init__.py
├── plugin.py           # CUDAVFIOPlugin
├── device.py           # CUDAVFIODevice, PCI/sysfs scanning
├── iommu.py            # IOMMU group detection and validation
└── BUILD               # Pants build with backendai_accelerator_v21 entry point
```

### Entry Point Registration

```python
# BUILD
python_distribution(
    name="dist",
    entry_points={
        "backendai_accelerator_v21": {
            "cuda_vfio": "ai.backend.accelerator.cuda_vfio.plugin:CUDAVFIOPlugin",
        }
    },
)
```

The agent config's plugin allowlist/blocklist controls which plugin loads:
- Docker agents: load `cuda` (existing CUDAPlugin)
- Kata agents: load `cuda_vfio` (new CUDAVFIOPlugin)

### CUDAVFIODevice

```python
@attrs.define(slots=True)
class CUDAVFIODevice(AbstractComputeDevice):
    pci_address: str           # "0000:41:00.0"
    iommu_group: int           # IOMMU group number
    vfio_device_path: str      # "/dev/vfio/42"
    pci_vendor_id: str         # "10de" (NVIDIA)
    pci_device_id: str         # "2684" (e.g., RTX 4090)
    model_name: str            # Mapped from PCI device ID
    memory_size: int           # GPU memory in bytes (from PCI BAR or lookup table)
    numa_node: int             # NUMA node affinity
    clique_id: str | None      # PCIe P2P group ID from Kata VRA (e.g., "clusterUUID.0")
```

### Device Discovery via sysfs

Since GPUs are bound to `vfio-pci` (not `nvidia`), NVML is unavailable. Discovery uses PCI sysfs:

```python
async def list_devices(self) -> Collection[CUDAVFIODevice]:
    devices = []
    pci_devices_path = Path("/sys/bus/pci/devices")

    for pci_dir in pci_devices_path.iterdir():
        vendor = (pci_dir / "vendor").read_text().strip()
        if vendor != "0x10de":  # NVIDIA vendor ID
            continue

        device_class = (pci_dir / "class").read_text().strip()
        if not device_class.startswith("0x0302"):  # 3D controller (GPU)
            # Also check 0x0300 (VGA) for display GPUs
            if not device_class.startswith("0x0300"):
                continue

        driver_link = pci_dir / "driver"
        if driver_link.is_symlink():
            driver = driver_link.resolve().name
            if driver != "vfio-pci":
                log.warning("GPU {} bound to {} (expected vfio-pci), skipping",
                           pci_dir.name, driver)
                continue

        iommu_group = self._get_iommu_group(pci_dir)
        if iommu_group is None:
            log.warning("GPU {} has no IOMMU group, skipping", pci_dir.name)
            continue

        pci_device_id = (pci_dir / "device").read_text().strip().removeprefix("0x")
        model_name = PCI_DEVICE_ID_MAP.get(pci_device_id, f"NVIDIA GPU ({pci_device_id})")

        devices.append(CUDAVFIODevice(
            device_id=DeviceId(pci_dir.name),
            hw_location=pci_dir.name,
            numa_node=self._read_numa_node(pci_dir),
            memory_size=self._estimate_memory(pci_dir),
            processing_units=0,  # Unknown without NVML
            pci_address=pci_dir.name,
            iommu_group=iommu_group,
            vfio_device_path=f"/dev/vfio/{iommu_group}",
            pci_vendor_id="10de",
            pci_device_id=pci_device_id,
            model_name=model_name,
        ))

    return devices
```

### IOMMU Group Validation

A GPU can only be safely passed through if its IOMMU group is isolated:

```python
def _validate_iommu_group(self, pci_address: str, iommu_group: int) -> bool:
    """Check that the IOMMU group contains only the GPU and its audio companion."""
    group_path = Path(f"/sys/kernel/iommu_groups/{iommu_group}/devices")
    group_devices = [d.name for d in group_path.iterdir()]

    allowed_companions = set()
    for dev_addr in group_devices:
        if dev_addr == pci_address:
            continue
        dev_class = (Path("/sys/bus/pci/devices") / dev_addr / "class").read_text().strip()
        # 0x0403 = Audio device (NVIDIA GPU audio is commonly co-located)
        # 0x0604 = PCI bridge (acceptable, handled by VFIO)
        if dev_class.startswith("0x0403") or dev_class.startswith("0x0604"):
            allowed_companions.add(dev_addr)
        else:
            log.warning(
                "IOMMU group {} contains non-GPU device {} (class {}), "
                "GPU {} may not be passthrough-safe",
                iommu_group, dev_addr, dev_class, pci_address,
            )
            return False

    return True
```

When multiple GPUs are in separate IOMMU groups, they can be independently assigned to different VMs. When GPUs share an IOMMU group (rare on server hardware, common on consumer motherboards), they must be assigned together or not at all.

### Allocation Map

Same `DiscretePropertyAllocMap` pattern as the existing CUDAPlugin:

```python
async def create_alloc_map(self) -> AbstractAllocMap:
    devices = await self.list_devices()
    return DiscretePropertyAllocMap(
        device_slots={
            dev.device_id: DeviceSlotInfo(
                SlotTypes.COUNT,
                SlotName("cuda.device"),
                Decimal(1),
            )
            for dev in devices
        },
    )
```

The slot name `cuda.device` is the same as the Docker CUDAPlugin — from the scheduler's perspective, a GPU is a GPU regardless of attachment mechanism.

### generate_docker_args() — VFIO Device Config

Despite the method name (inherited from `AbstractComputePlugin`), this returns Kata-specific VFIO configuration:

```python
async def generate_docker_args(
    self,
    docker: Any,  # Unused for Kata; None is passed
    device_alloc: DeviceAllocation,
) -> Mapping[str, Any]:
    vfio_devices = []
    for slot_type, per_device_alloc in device_alloc.items():
        for device_id, alloc in per_device_alloc.items():
            if alloc > 0:
                dev = self._device_map[DeviceId(device_id)]
                vfio_devices.append({
                    "pci_address": dev.pci_address,
                    "iommu_group": dev.iommu_group,
                    "vfio_device": dev.vfio_device_path,
                    "model_name": dev.model_name,
                    "clique_id": dev.clique_id,      # P2P group for Kata VRA topology
                    "memory_size": dev.memory_size,   # GPU memory in bytes
                    "numa_node": dev.numa_node,       # NUMA affinity for CPU pinning
                })
    return {"_kata_vfio_devices": vfio_devices}
```

`KataKernelCreationContext.apply_accelerator_allocation()` (see [kata-agent-backend.md](kata-agent-backend.md)) reads `_kata_vfio_devices` and translates it into Kata container annotations for VFIO hotplug.

### Metrics Collection

Host-side GPU metrics are limited when devices are bound to `vfio-pci`:

**Node-level metrics** (available from sysfs):
- Power consumption: `/sys/bus/pci/devices/{addr}/power/` (limited)
- Temperature: not available from sysfs alone

**Container-level metrics** (from inside guest VM):
- The guest VM has the `nvidia` driver loaded and NVML is functional inside the guest
- CoCo-by-default: kata-agent `ExecProcessRequest` is blocked by policy — `containerd exec nvidia-smi` does **not** work
- Metrics are exposed by **DCGM Exporter** (`:9400`) and **Node Exporter** (`:9100`) running inside the guest as systemd services (baked into the attested rootfs)
- Prometheus scrapes these exporters over the Calico network — standard HTTP, no kata-agent involvement
- The CoCo policy controls tRPC API calls (exec, copy file), NOT network traffic

```python
async def gather_container_measures(
    self, stat_ctx, container_ids,
) -> Sequence[ContainerMeasurement]:
    # CoCo: ExecProcessRequest is blocked by kata-agent policy.
    # GPU metrics are collected by Prometheus scraping DCGM Exporter
    # inside the guest over the Calico network (port 9400).
    # This plugin does NOT collect per-container GPU metrics directly.
    # Backend.AI reads GPU metrics from Prometheus/Grafana instead.
    return []
```

### restore_from_container()

When the agent restarts, reconstruct VFIO bindings from running Kata sandboxes:

```python
async def restore_from_container(self, container, alloc_map):
    labels = container.labels
    # Read allocated device info from container labels
    # (KataKernelCreationContext stores PCI addresses in labels at creation time)
    pci_addresses = labels.get("ai.backend.vfio.pci_addresses", "").split(",")
    for pci_addr in pci_addresses:
        if pci_addr:
            device_id = DeviceId(pci_addr)
            alloc_map.apply_allocation({
                SlotName("cuda.device"): {device_id: Decimal(1)},
            })
```

## Interface / API

| Method | Purpose |
|--------|---------|
| `list_devices()` | PCI sysfs scan for NVIDIA GPUs bound to vfio-pci |
| `available_slots()` | Count of passthrough-ready GPUs |
| `create_alloc_map()` | `DiscretePropertyAllocMap` with `cuda.device` slots |
| `generate_docker_args()` | Returns `_kata_vfio_devices` list for Kata shim |
| `gather_node_measures()` | Limited sysfs metrics (no NVML on host) |
| `gather_container_measures()` | Returns empty — CoCo policy blocks exec; metrics via Prometheus scraping DCGM Exporter |
| `restore_from_container()` | Reconstruct allocations from container labels |

## Multi-Node GPU Interconnect: GPUDirect RDMA

### Overview

Multi-node GPU workloads (distributed training, multi-node inference) require **GPUDirect RDMA** — direct memory access between a GPU and an RDMA-capable NIC (InfiniBand HCA or RoCE adapter) without CPU involvement. This enables NCCL-based collective operations across nodes at near-wire-speed InfiniBand bandwidth.

For Kata VMs, this means **both the GPU and the InfiniBand HCA must be VFIO-passthrough to the same VM**, and peer-to-peer DMA between them must work across the VM boundary.

### Requirements for GPUDirect RDMA in Kata VMs

| Requirement | Details |
|---|---|
| **GPU + NIC co-passthrough** | Both the NVIDIA GPU and InfiniBand HCA (ConnectX-5+) must be VFIO-assigned to the same Kata VM |
| **IOMMU pass-through mode** | GPUDirect RDMA requires physical addresses to be identical from both devices' perspective. The IOMMU must be in 1:1 pass-through mode (`iommu=pt`), not performing address translation. Inside the guest, vIOMMU (if present) must also be in pass-through or both devices must share an IOMMU domain |
| **Same PCIe root complex** | GPU and NIC must share an upstream PCIe root complex. Cross-socket (QPI/UPI) P2P is unreliable or non-functional |
| **ACS/ATS for Direct Translated P2P** | Access Control Services (ACS) normally forces all DMA through the root complex. Address Translation Services (ATS, available on ConnectX-5+ and Volta+ GPUs) allows endpoints to prefetch IOVA→PA translations and DMA directly to peers, bypassing the IOMMU for P2P |
| **PCIe topology replication** | NVIDIA's driver uses PCIe topology to determine P2P capability. Default virtualization flattens topology (all devices on root bus), which disables P2P. The guest must replicate the host's PCIe switch hierarchy |
| **Guest driver stack** | Full NVIDIA + Mellanox stack inside the guest: `nvidia` driver, `mlx5_core`/`mlx5_ib`, `ib_core`, `ib_uverbs`, `nvidia-peermem` (bridges GPU and IB subsystems), MLNX_OFED |

### Kata VRA (Virtualization Reference Architecture)

The Kata project's [VRA design document](https://github.com/kata-containers/kata-containers/blob/main/docs/design/kata-vra.md) explicitly addresses GPUDirect P2P and RDMA with three key mechanisms:

**1. PCIe topology replication via switch ports:**

```toml
# kata configuration.toml
hotplug_vfio = "switch-port"    # Replicate host PCIe switch topology in guest
pcie_switch_port = 8            # Number of switch downstream ports
```

This creates PCIe switch structures inside the guest that mirror the host topology. Devices that were under the same PCIe switch on the host are placed under the same virtual switch in the guest, enabling the NVIDIA driver to recognize P2P capability.

**2. Clique-ID annotation for P2P device grouping:**

Devices with the same `clique-id` form a P2P group. Configured via Container Device Interface (CDI):

```yaml
# GPU on PCIe switch
- annotations:
    bdf: "41:00.0"
    clique-id: "0"

# InfiniBand HCA on same PCIe switch
- annotations:
    bdf: "42:00.0"
    clique-id: "0"    # Same clique → P2P enabled between GPU and NIC
```

The hypervisor uses clique-id to provide topology metadata that the NVIDIA driver reads to enable GPUDirect P2P, even if the virtualized PCIe topology doesn't perfectly match the host.

**3. Multi-function IOMMU group handling:**

NVIDIA datacenter GPUs often contain multiple functions (GPU + audio + USB) in a single IOMMU group. VRA handles this by selectively attaching:
- GPU: PCIe root/switch port (requires express protocol, consumes 4K IO range)
- Audio/USB companions: PCI bridge (standard PCI, no IO range consumption)

This conserves scarce PCIe IO space (64K total, 4K per port, max ~16 ports).

### NVLink / NVSwitch (Intra-Node GPU-GPU)

NVLink connects GPUs directly, bypassing PCIe. NVSwitch enables all-to-all NVLink in DGX/HGX systems.

When GPUs are VFIO-passthrough to a Kata VM:
- NVLink hardware connections remain physically present
- The NVIDIA driver inside the guest detects NVLink via GPU registers accessible through VFIO BAR mapping
- P2P over NVLink works if both GPUs are in the same guest and the driver detects NVLink topology
- This has been demonstrated in VMware vSphere (GPU-passthrough with NVLink), suggesting KVM/VFIO works similarly

For Backend.AI multi-container sessions (clusters on a single host), all GPUs can be passed through to a single Kata sandbox (VM) via the containerd Sandbox API, enabling NVLink communication between containers sharing the VM.

### Current Upstream Status

| Component | Status | Reference |
|---|---|---|
| kata-vra.md design | Written, covers GPUDirect P2P + RDMA | [kata-vra.md](https://github.com/kata-containers/kata-containers/blob/main/docs/design/kata-vra.md) |
| GPU VFIO passthrough | Working (A100, H100 with caveats) | [#12723](https://github.com/kata-containers/kata-containers/issues/12723) |
| InfiniBand HCA passthrough | Partially working; BAR allocation fixed in Kata 3.8+ | [#10392](https://github.com/kata-containers/kata-containers/issues/10392) |
| SR-IOV VF passthrough | Broken — "No PCI mapping found" | [#11910](https://github.com/kata-containers/kata-containers/issues/11910) |
| GPUDirect RDMA end-to-end | Not yet demonstrated in Kata | [#10796](https://github.com/kata-containers/kata-containers/issues/10796) (open, high-priority) |

### InfiniBand HCA BAR Allocation Fix

Kata 3.8+ added `getBARsMaxAddressableMemory()` to auto-size PCIe BAR windows for large-BAR devices. However, this function initially only detected NVIDIA GPUs (via `IsGPU()` check), skipping InfiniBand HCAs. ConnectX-6 requires 32MB+ BAR0 but the default 2MB allocation caused `"BAR0: no space for [mem size 32MB 64bit pref]"`. The fix: include Mellanox device detection alongside GPU detection in BAR sizing logic ([#10392](https://github.com/kata-containers/kata-containers/issues/10392)).

### Impact on CUDAVFIOPlugin

For GPUDirect RDMA support, the `CUDAVFIOPlugin` needs awareness of co-located InfiniBand HCAs:

```python
async def generate_docker_args(self, docker, device_alloc):
    vfio_devices = []
    for device_id, alloc in per_device_alloc.items():
        dev = self._device_map[DeviceId(device_id)]
        vfio_devices.append({
            "pci_address": dev.pci_address,
            "iommu_group": dev.iommu_group,
            "vfio_device": dev.vfio_device_path,
            "model_name": dev.model_name,
            "clique_id": dev.clique_id,          # NEW: P2P group identifier
        })
    return {
        "_kata_vfio_devices": vfio_devices,
        "_kata_rdma_devices": self._get_colocated_rdma_devices(vfio_devices),  # NEW
    }
```

A separate **RDMAVFIOPlugin** (or extension to `CUDAVFIOPlugin`) would handle InfiniBand HCA discovery, IOMMU group validation, and VFIO device configuration for the NIC side. The `clique_id` links GPU and NIC devices for P2P topology replication.

### Guest VM Base Image Requirements (GPUDirect RDMA)

In addition to storage filesystem clients (see [migration-compatibility.md](migration-compatibility.md)), the guest rootfs must include:

| Component | Purpose |
|---|---|
| NVIDIA GPU driver + CUDA toolkit | GPU compute + `nvidia-peermem` module |
| MLNX_OFED | InfiniBand/RoCE driver stack (`mlx5_core`, `mlx5_ib`) |
| `nvidia-peermem` kernel module | Registers GPU memory with IB subsystem for GPUDirect RDMA |
| `libibverbs`, `librdmacm` | RDMA userspace libraries |
| NCCL | Multi-GPU collective communication (uses GPUDirect RDMA for inter-node) |
| Guest kernel with `CONFIG_INFINIBAND=y`, `CONFIG_MLX5_CORE=y`, `CONFIG_VFIO=y` | InfiniBand + VFIO kernel support |

**Note:** MLNX_OFED must be installed before or alongside the NVIDIA GPU driver. If the GPU driver is installed first, it must be reinstalled after OFED to build `nvidia-peermem` correctly.

## Implementation Notes

- `PCI_DEVICE_ID_MAP` is a static mapping from PCI device IDs to model names (e.g., `"2684"` → `"NVIDIA RTX 4090"`). This can be sourced from the PCI ID database or maintained as a curated subset for common GPU models.
- VFIO requires `/dev/vfio/{group}` device files to be accessible. The agent process needs `CAP_SYS_RAWIO` or root access.
- When BEP-1016 (Accelerator Interface v2) is implemented, `generate_docker_args()` should be migrated to `create_lifecycle_hook()` returning a `WorkloadConfig` with proper VFIO device entries.
- The `docker` parameter in `generate_docker_args()` is passed as `None` by `KataKernelCreationContext` since there is no Docker client.
- GPU audio companion devices in the same IOMMU group must also be passed through; the plugin handles this transparently.
