import logging
from collections.abc import Collection, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, cast, override

import aiodocker
import attrs

from ai.backend.agent import __version__
from ai.backend.agent.docker.intrinsic import CPUPlugin as DockerCPUPlugin
from ai.backend.agent.docker.intrinsic import MemoryPlugin as DockerMemoryPlugin
from ai.backend.agent.errors import InitializationError
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    ComputePluginContext,
    DeviceAllocation,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    known_slot_types,
)
from ai.backend.agent.stats import (
    ContainerMeasurement,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.types import MetricKey
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)
from ai.backend.logging import BraceStyleAdapter

from .errors import VfioDeviceUnavailable

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

ALLOC_LABEL = "ai.backend.coco.alloc"
PCI_DEVICES = Path("/sys/bus/pci/devices")
VFIO_DEVICES = Path("/dev/vfio/devices")
NVIDIA_VENDOR_ID = "0x10de"


@dataclass(frozen=True)
class VfioDeviceInfo:
    bdf: str
    char_device: Path
    numa_node: int | None
    vendor: str


def device_id_for(bdf: str) -> DeviceId:
    return DeviceId(bdf.replace(":", "_"))


def bdf_for(device_id: DeviceId | str) -> str:
    return str(device_id).replace("_", ":")


def scan_vfio_devices(vendor_ids: Sequence[str]) -> list[VfioDeviceInfo]:
    found: list[VfioDeviceInfo] = []
    if not PCI_DEVICES.is_dir():
        return found
    for entry in sorted(PCI_DEVICES.glob("*/vfio-dev/vfio*")):
        pci_dir = entry.parent.parent
        try:
            vendor = (pci_dir / "vendor").read_text().strip().lower()
        except OSError:
            continue
        if vendor_ids and vendor not in vendor_ids:
            continue
        try:
            numa_node: int | None = int((pci_dir / "numa_node").read_text().strip())
        except (OSError, ValueError):
            numa_node = None
        if numa_node is not None and numa_node < 0:
            numa_node = None
        found.append(VfioDeviceInfo(pci_dir.name, VFIO_DEVICES / entry.name, numa_node, vendor))
    return found


def resolve_char_devices(device_ids: Sequence[DeviceId | str]) -> list[Path]:
    resolved: list[Path] = []
    for device_id in device_ids:
        bdf = bdf_for(device_id)
        candidates = sorted((PCI_DEVICES / bdf / "vfio-dev").glob("vfio*"))
        if not candidates:
            raise VfioDeviceUnavailable(extra_msg=f"{bdf} has no vfio-dev entry")
        char_device = VFIO_DEVICES / candidates[0].name
        if not char_device.exists():
            raise VfioDeviceUnavailable(extra_msg=f"{char_device} is absent")
        resolved.append(char_device)
    return resolved


def encode_allocations(
    allocations: Mapping[DeviceName, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
) -> str:
    return dump_json_str({
        str(device): {
            str(slot): {str(dev_id): str(amount) for dev_id, amount in per_device.items()}
            for slot, per_device in per_slot.items()
        }
        for device, per_slot in allocations.items()
    })


def decode_allocations(
    container: Container, device_name: DeviceName
) -> Mapping[SlotName, Mapping[DeviceId, Decimal]] | None:
    raw = container.labels.get(ALLOC_LABEL)
    if not raw:
        return None
    try:
        decoded = load_json(raw)
    except ValueError:
        log.warning("unparsable allocation label on container {}", container.id)
        return None
    per_slot = decoded.get(str(device_name))
    if not per_slot:
        return None
    return {
        SlotName(slot): {DeviceId(dev_id): Decimal(amount) for dev_id, amount in devices.items()}
        for slot, devices in per_slot.items()
    }


HYPERVISOR_PREFIX = "hypervisor_"


def relabel_as_hypervisor(measured: Sequence[NodeMeasurement]) -> Sequence[NodeMeasurement]:
    return [
        attrs.evolve(measurement, key=MetricKey(HYPERVISOR_PREFIX + str(measurement.key)))
        for measurement in measured
    ]


class _HypervisorBlindMixin:
    async def gather_container_measures(
        self, ctx: StatContext, container_ids: Sequence[str]
    ) -> Sequence[ContainerMeasurement]:
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []


class CPUPlugin(_HypervisorBlindMixin, DockerCPUPlugin):
    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return relabel_as_hypervisor(await super().gather_node_measures(ctx))

    @override
    async def restore_from_container(
        self, container: Container, alloc_map: AbstractAllocMap
    ) -> None:
        allocations = decode_allocations(container, self.key)
        if allocations is not None:
            alloc_map.apply_allocation(allocations)


class MemoryPlugin(_HypervisorBlindMixin, DockerMemoryPlugin):
    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return relabel_as_hypervisor(await super().gather_node_measures(ctx))

    @override
    async def restore_from_container(
        self, container: Container, alloc_map: AbstractAllocMap
    ) -> None:
        allocations = decode_allocations(container, self.key)
        if allocations is not None:
            alloc_map.apply_allocation(allocations)


class VfioGpuDevice(AbstractComputeDevice):
    pass


class VfioGpuPlugin(AbstractComputePlugin):
    config_watch_enabled = False

    key = DeviceName("cuda")
    slot_types = [(SlotName("cuda.device"), SlotTypes.COUNT)]

    def __init__(
        self,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
        vendor_ids: Sequence[str],
        device_memory_bytes: int,
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._vendor_ids = [vendor.lower() for vendor in vendor_ids]
        self._device_memory_bytes = device_memory_bytes

    @override
    async def init(self, context: Any | None = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    @override
    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "cuda.device",
            "description": "CUDA GPU passed through whole",
            "human_readable_name": "GPU",
            "display_unit": "GPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "gpu1",
        }

    @override
    async def list_devices(self) -> Collection[AbstractComputeDevice]:
        return [
            VfioGpuDevice(
                device_id=device_id_for(info.bdf),
                device_name=self.key,
                hw_location=info.bdf,
                numa_node=info.numa_node,
                memory_size=self._device_memory_bytes,
                processing_units=1,
            )
            for info in scan_vfio_devices(self._vendor_ids)
        ]

    @override
    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {SlotName("cuda.device"): Decimal(len(devices))}

    @override
    def get_version(self) -> str:
        return __version__

    @override
    async def extra_info(self) -> Mapping[str, str]:
        return {"passthrough": "whole-device", "trusted_io": "unavailable"}

    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    @override
    async def gather_container_measures(
        self, ctx: StatContext, container_ids: Sequence[str]
    ) -> Sequence[ContainerMeasurement]:
        return []

    @override
    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    @override
    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                device.device_id: DeviceSlotInfo(
                    SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1)
                )
                for device in devices
            },
        )

    @override
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    @override
    async def generate_docker_args(
        self, docker: aiodocker.docker.Docker, device_alloc: DeviceAllocation
    ) -> Mapping[str, Any]:
        return {}

    @override
    async def restore_from_container(
        self, container: Container, alloc_map: AbstractAllocMap
    ) -> None:
        allocations = decode_allocations(container, self.key)
        if allocations is not None:
            alloc_map.apply_allocation(allocations)

    @override
    async def get_attached_devices(
        self, device_alloc: DeviceAllocation
    ) -> Sequence[DeviceModelInfo]:
        return [
            {
                "device_id": device_id,
                "model_name": "whole-gpu-passthrough",
                "data": {"pci_address": bdf_for(device_id)},
            }
            for device_id in device_alloc.get(SlotName("cuda.device"), {})
        ]

    @override
    async def get_docker_networks(self, device_alloc: DeviceAllocation) -> list[str]:
        return []

    @override
    async def generate_mounts(
        self, source_path: Path, device_alloc: DeviceAllocation
    ) -> list[MountInfo]:
        return []


async def load_resources(
    etcd: AbstractKVStore, local_config: Mapping[str, Any]
) -> Mapping[DeviceName, AbstractComputePlugin]:
    compute_device_types: MutableMapping[DeviceName, AbstractComputePlugin] = {}
    confidential = local_config.get("confidential", {})
    compute_plugin_ctx = ComputePluginContext(etcd, local_config)
    await compute_plugin_ctx.init(
        allowlist=local_config["agent"]["allow-compute-plugins"],
        blocklist=local_config["agent"]["block-compute-plugins"],
    )
    if "cpu" not in compute_plugin_ctx.plugins:
        cpu_plugin = CPUPlugin(await etcd.get_prefix("config/plugins/cpu"), local_config)
        await cpu_plugin.init()
        compute_plugin_ctx.attach_intrinsic_device(cpu_plugin)
    if "mem" not in compute_plugin_ctx.plugins:
        memory_plugin = MemoryPlugin(await etcd.get_prefix("config/plugins/memory"), local_config)
        await memory_plugin.init()
        compute_plugin_ctx.attach_intrinsic_device(memory_plugin)
    if "cuda" not in compute_plugin_ctx.plugins:
        gpu_plugin = VfioGpuPlugin(
            await etcd.get_prefix("config/plugins/cuda"),
            local_config,
            confidential.get("vfio-vendor-ids") or [NVIDIA_VENDOR_ID],
            int(confidential.get("gpu-memory-bytes") or 0),
        )
        await gpu_plugin.init()
        compute_plugin_ctx.attach_intrinsic_device(gpu_plugin)
    for plugin_instance in compute_plugin_ctx.plugins.values():
        if plugin_instance.key in compute_device_types:
            raise InitializationError(
                f"A plugin defining the same key '{plugin_instance.key}' already exists."
            )
        compute_device_types[plugin_instance.key] = plugin_instance
    return compute_device_types


async def scan_available_resources(
    compute_device_types: Mapping[DeviceName, AbstractComputePlugin],
) -> Mapping[SlotName, Decimal]:
    slots: MutableMapping[SlotName, Decimal] = {}
    mutable_slot_types = cast(MutableMapping[SlotName, SlotTypes], known_slot_types)
    for computer in compute_device_types.values():
        mutable_slot_types.update(computer.slot_types)
        for slot_name, slot_value in (await computer.available_slots()).items():
            slots[slot_name] = Decimal(slot_value)
            if slots[slot_name] <= 0 and slot_name in (SlotName("cpu"), SlotName("mem")):
                raise InitializationError(
                    f"The resource slot '{slot_name}' is not sufficient (zero or below zero)."
                )
    log.info("Confidential resource slots: {!r}", slots)
    return slots
