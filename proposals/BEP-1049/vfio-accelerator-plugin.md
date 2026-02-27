<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: VFIO-based GPU passthrough compute plugin for Kata backend
depends-on: [kata-agent-backend.md]
key-decisions:
  - New CUDAVFIOPlugin separate from existing CUDAPlugin
  - DiscretePropertyAllocMap only (no FractionAllocMap)
  - Device discovery via sysfs PCI scan (not NVML)
  - IOMMU group validation at device scan time
-->

# BEP-1049: VFIO Accelerator Plugin

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
- Metrics must be collected via the kata-agent running inside the guest, forwarded over VSOCK
- The agent can periodically query guest-side `nvidia-smi` or NVML via a metrics endpoint exposed by kata-agent

```python
async def gather_container_measures(
    self, stat_ctx, container_ids,
) -> Sequence[ContainerMeasurement]:
    # Query guest-side nvidia-smi via containerd exec
    for container_id in container_ids:
        result = await self._containerd.exec_in_container(
            container_id,
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
        )
        # Parse CSV output into ContainerMeasurement objects
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
| `gather_container_measures()` | Guest-side NVML via containerd exec |
| `restore_from_container()` | Reconstruct allocations from container labels |

## Implementation Notes

- `PCI_DEVICE_ID_MAP` is a static mapping from PCI device IDs to model names (e.g., `"2684"` → `"NVIDIA RTX 4090"`). This can be sourced from the PCI ID database or maintained as a curated subset for common GPU models.
- VFIO requires `/dev/vfio/{group}` device files to be accessible. The agent process needs `CAP_SYS_RAWIO` or root access.
- When BEP-1016 (Accelerator Interface v2) is implemented, `generate_docker_args()` should be migrated to `create_lifecycle_hook()` returning a `WorkloadConfig` with proper VFIO device entries.
- The `docker` parameter in `generate_docker_args()` is passed as `None` by `KataKernelCreationContext` since there is no Docker client.
- GPU audio companion devices in the same IOMMU group must also be passed through; the plugin handles this transparently.
