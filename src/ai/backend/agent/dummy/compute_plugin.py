from decimal import Decimal
from pathlib import Path
from typing import Any, Collection, List, Mapping, Sequence

import aiodocker

from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)

from ..resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    FractionAllocMap,
)
from ..stats import ContainerMeasurement, NodeMeasurement, ProcessMeasurement, StatContext
from ..types import Container as SessionContainer
from ..types import MountInfo
from .defs import AllocationModes


class DummyDevice(AbstractComputeDevice):
    model_name: str | None
    mother_uuid: DeviceId | None
    slot_type: SlotTypes

    def __init__(
        self,
        model_name: str | None,
        mother_uuid: DeviceId | None,
        slot_type: SlotTypes,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.mother_uuid = mother_uuid
        self.slot_type = slot_type


class DummyComputePlugin(AbstractComputePlugin):
    key = DeviceName("dummy")
    slot_types = [
        (SlotName("dummy"), SlotTypes.COUNT),
    ]

    def __init__(
        self,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
        *,
        key: DeviceName,
        allocation_mode: AllocationModes = AllocationModes.DISCRETE,
    ) -> None:
        super().__init__(plugin_config, local_config)
        self.dummy_ag_config: Mapping[str, Any] = self.local_config["dummy"]["agent"]
        self.device_plugin_configs: Mapping[str, Any] = self.dummy_ag_config["device_plugins"]
        self.key = key
        self._mode = allocation_mode

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    def get_metadata(self) -> AcceleratorMetadata:
        device_metadata = self.device_plugin_configs["metadata"]
        return {
            "slot_name": str(self.key),
            "description": f"Dummy {self.key}",
            "human_readable_name": device_metadata["human-readable-name"] or str(self.key).upper(),
            "display_unit": device_metadata["display-unit"],
            "number_format": device_metadata["number-format"],
            "display_icon": device_metadata["display-icon"],
        }

    async def list_devices(self) -> Collection[DummyDevice]:
        return [
            DummyDevice(
                slot_type=device["slot-type"],
                model_name=device["model-name"],
                mother_uuid=device["mother-uuid"],
                device_id=DeviceId(device["device-id"]),
                device_name=device["device-name"],
                hw_location=device["hw-location"],
                memory_size=device["memory-size"],
                processing_units=device["processing-units"],
                numa_node=device["numa-node"],
            )
            for device in self.device_plugin_configs["devices"]
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName(str(self.key)): Decimal(sum(dev.processing_units for dev in devices)),
        }

    def get_version(self) -> str:
        return "1"

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

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        match self._mode:
            case AllocationModes.DISCRETE:
                return DiscretePropertyAllocMap(
                    device_slots={
                        dev.device_id: DeviceSlotInfo(
                            dev.slot_type, SlotName(f"{self.key}.device"), Decimal(1)
                        )
                        for dev in devices
                    }
                )
            case AllocationModes.FRACTIONAL:
                return FractionAllocMap(
                    device_slots={
                        dev.device_id: DeviceSlotInfo(
                            dev.slot_type, SlotName(f"{self.key}.share"), Decimal(1)
                        )
                        for dev in devices
                    }
                )
            case _:
                raise RuntimeError("Wrong allocation mode")

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
        container: SessionContainer,
        alloc_map: AbstractAllocMap,
    ) -> None:
        return

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        return []

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []
