import os
import platform
from collections.abc import Collection, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, override

import aiodocker
import psutil

from ai.backend.agent import __version__
from ai.backend.agent.alloc_map import AllocationStrategy
from ai.backend.agent.containerd.scratch import read_resource_spec
from ai.backend.agent.errors import InvalidArgumentError, InvalidResourceConfigError
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceAllocation,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ai.backend.agent.stats import (
    ContainerMeasurement,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.agent.vendor.linux import libnuma
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)


async def _restore_slot(
    container: Container,
    alloc_map: AbstractAllocMap,
    device_name: DeviceName,
    slot_name: SlotName,
) -> None:
    """Re-apply the kernel's recorded allocation, as the Docker agent does from its records."""
    if not isinstance(alloc_map, DiscretePropertyAllocMap):
        raise InvalidArgumentError(
            f"Expected DiscretePropertyAllocMap, got {type(alloc_map).__name__}"
        )
    resource_spec = await read_resource_spec(container.labels)
    if resource_spec is None:
        return
    allocation = resource_spec.allocations.get(device_name, {}).get(slot_name)
    if allocation:
        alloc_map.apply_allocation({slot_name: allocation})


class CPUDevice(AbstractComputeDevice):
    pass


class CPUPlugin(AbstractComputePlugin):
    """
    Represents the CPU.
    """

    config_watch_enabled = False

    key = DeviceName("cpu")
    slot_types = [
        (SlotName("cpu"), SlotTypes.COUNT),
    ]

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
            "slot_name": "cpu",
            "description": "CPU",
            "human_readable_name": "CPU",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "cpu",
        }

    @override
    async def list_devices(self) -> Collection[CPUDevice]:
        cores = await libnuma.get_available_cores()
        overcommit_factor = int(os.environ.get("BACKEND_CPU_OVERCOMMIT_FACTOR", "1"))
        if not (1 <= overcommit_factor <= 10):
            raise InvalidResourceConfigError(
                f"BACKEND_CPU_OVERCOMMIT_FACTOR must be between 1 and 10, got {overcommit_factor}"
            )
        return [
            CPUDevice(
                device_id=DeviceId(str(core_idx)),
                hw_location="root",
                numa_node=libnuma.node_of_cpu(core_idx),
                memory_size=0,
                processing_units=1 * overcommit_factor,
            )
            for core_idx in sorted(cores)
        ]

    @override
    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("cpu"): Decimal(sum(dev.processing_units for dev in devices)),
        }

    @override
    def get_version(self) -> str:
        return __version__

    @override
    async def extra_info(self) -> Mapping[str, str]:
        return {
            "agent_version": __version__,
            "machine": platform.machine(),
            "os_type": platform.system(),
        }

    # FIXME(containerd-mvp): no CPU statistics are collected for the node, containers or
    # processes
    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    @override
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
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
                dev.device_id: DeviceSlotInfo(
                    SlotTypes.COUNT, SlotName("cpu"), Decimal(dev.processing_units)
                )
                for dev in devices
            },
        )

    @override
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    # FIXME(containerd-mvp): CPU limits are not applied to containerd kernels
    @override
    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, Any]:
        return {}

    @override
    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        await _restore_slot(container, alloc_map, DeviceName("cpu"), SlotName("cpu"))

    @override
    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("cpu")].keys()]
        available_devices = await self.list_devices()
        attached_devices: list[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": "",
                    "data": {"cores": len(device_ids)},
                })
        return attached_devices

    @override
    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

    @override
    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[MountInfo]:
        return []


class MemoryDevice(AbstractComputeDevice):
    pass


class MemoryPlugin(AbstractComputePlugin):
    """
    Represents the main memory.
    """

    config_watch_enabled = False

    key = DeviceName("mem")
    slot_types = [
        (SlotName("mem"), SlotTypes.BYTES),
    ]

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
            "slot_name": "ram",
            "description": "Memory",
            "human_readable_name": "RAM",
            "display_unit": "GiB",
            "number_format": {"binary": True, "round_length": 0},
            "display_icon": "ram",
        }

    @override
    async def list_devices(self) -> Collection[MemoryDevice]:
        memory_size = psutil.virtual_memory().total
        overcommit_factor = int(os.environ.get("BACKEND_MEM_OVERCOMMIT_FACTOR", "1"))
        return [
            MemoryDevice(
                device_id=DeviceId("root"),
                device_name=self.key,
                hw_location="root",
                numa_node=0,  # the kernel setting will do the job.
                memory_size=overcommit_factor * memory_size,
                processing_units=0,
            ),
        ]

    @override
    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("mem"): Decimal(sum(dev.memory_size for dev in devices)),
        }

    @override
    def get_version(self) -> str:
        return __version__

    @override
    async def extra_info(self) -> Mapping[str, str]:
        return {}

    # FIXME(containerd-mvp): no memory statistics are collected for the node, containers or
    # processes
    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    @override
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
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
            allocation_strategy=AllocationStrategy.FILL,
            device_slots={
                dev.device_id: DeviceSlotInfo(
                    SlotTypes.BYTES, SlotName("mem"), Decimal(dev.memory_size)
                )
                for dev in devices
            },
        )

    @override
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    # FIXME(containerd-mvp): memory limits are not applied to containerd kernels
    @override
    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, Any]:
        return {}

    @override
    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        await _restore_slot(container, alloc_map, DeviceName("mem"), SlotName("mem"))

    @override
    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("mem")].keys()]
        available_devices = await self.list_devices()
        attached_devices: list[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": "",
                    "data": {},
                })
        return attached_devices

    @override
    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

    @override
    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[MountInfo]:
        return []
