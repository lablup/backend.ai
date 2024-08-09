from decimal import Decimal
from pathlib import Path
from typing import Any, Collection, Mapping, Sequence

import aiodocker

from ai.backend.agent.types import MountInfo
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)

from .. import __version__
from ..alloc_map import AllocationStrategy
from ..resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ..stats import (
    ContainerMeasurement,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from .agent import Container


class CPUDevice(AbstractComputeDevice):
    pass


class CPUPlugin(AbstractComputePlugin):
    """
    Represents the CPU.
    """

    resource_config: Mapping[str, Any]

    config_watch_enabled = False

    key = DeviceName("cpu")
    slot_types = [
        (SlotName("cpu"), SlotTypes.COUNT),
    ]

    def __init__(
        self,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
        dummy_config: Mapping[str, Any],
    ) -> None:
        super().__init__(plugin_config, local_config)
        self.resource_config = dummy_config["agent"]["resource"]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "cpu",
            "description": "CPU",
            "human_readable_name": "CPU",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "cpu",
        }

    async def list_devices(self) -> Collection[AbstractComputeDevice]:
        cores = self.resource_config["cpu"]["core-indexes"]
        return [
            CPUDevice(
                device_id=DeviceId(str(core_idx)),
                hw_location="root",
                numa_node=None,
                memory_size=0,
                processing_units=1,
            )
            for core_idx in sorted(cores)
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("cpu"): Decimal(sum(dev.processing_units for dev in devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    async def create_alloc_map(self) -> "AbstractAllocMap":
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(
                    SlotTypes.COUNT, SlotName("cpu"), Decimal(dev.processing_units)
                )
                for dev in devices
            },
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc,
    ) -> Mapping[str, Any]:
        cores = [*map(int, device_alloc["cpu"].keys())]
        sorted_core_ids = [*map(str, sorted(cores))]
        return {
            "HostConfig": {
                "CpuPeriod": 100_000,  # docker default
                "CpuQuota": int(100_000 * len(cores)),
                "Cpus": ",".join(sorted_core_ids),
                "CpusetCpus": ",".join(sorted_core_ids),
                # 'CpusetMems': f'{resource_spec.numa_node}',
            },
        }

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        return None

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

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

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

    resource_config: Mapping[str, Any]

    config_watch_enabled = False

    key = DeviceName("mem")
    slot_types = [
        (SlotName("mem"), SlotTypes.BYTES),
    ]

    def __init__(
        self,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
        dummy_config: Mapping[str, Any],
    ) -> None:
        super().__init__(plugin_config, local_config)
        self.resource_config = dummy_config["agent"]["resource"]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "ram",
            "description": "Memory",
            "human_readable_name": "RAM",
            "display_unit": "GiB",
            "number_format": {"binary": True, "round_length": 0},
            "display_icon": "cpu",
        }

    async def list_devices(self) -> Collection[AbstractComputeDevice]:
        memory_size = self.resource_config["memory"]["size"]
        return [
            MemoryDevice(
                device_id=DeviceId("root"),
                device_name=self.key,
                hw_location="root",
                numa_node=0,  # the kernel setting will do the job.
                memory_size=memory_size,
                processing_units=0,
            ),
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("mem"): Decimal(sum(dev.memory_size for dev in devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    async def create_alloc_map(self) -> "AbstractAllocMap":
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

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc,
    ) -> Mapping[str, Any]:
        return {}

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        return None

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

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> list[MountInfo]:
        return []
