import asyncio
import glob
import logging
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import Any, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

import aiodocker

from .. import __version__
from .rngd_api import RngdAPI

try:
    from ai.backend.agent.resources import get_resource_spec_from_container  # type: ignore
except ImportError:
    from ai.backend.agent.docker.resources import get_resource_spec_from_container

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    ContainerMeasurement,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    NodeMeasurement,
    StatContext,
)
from ai.backend.agent.stats import ProcessMeasurement
from ai.backend.agent.types import Container, MountInfo
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AcceleratorMetadata,
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)

PREFIX = "rngd"


log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.rngd"))


class RngdDevice(AbstractComputeDevice):
    model_name: str
    serial: str

    def __init__(self, model_name: str, serial: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.serial = serial

    def __str__(self) -> str:
        return f"Furiosa {self.model_name} <{self.hw_location}, Memory {self.memory_size}, NUMA Node #{self.numa_node}>"

    def __repr__(self) -> str:
        return self.__str__()


class RngdPlugin(AbstractComputePlugin):
    key = DeviceName("rngd")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("rngd.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"rngd.device"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True
    rngd_config: Any

    _rbln_stat_path: str
    _all_devices: Optional[list[RngdDevice]]

    async def init(self, context: Any = None) -> None:
        self._all_devices = None

        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]

        try:
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            log.info("RNGD acceleration is enabled.")
        except ImportError:
            log.warning("could not find Furiosa devices.")
            self.enabled = False

    async def list_devices(self) -> List[RngdDevice]:
        if self._all_devices is not None:
            return self._all_devices
        devices: List[RngdDevice] = []
        cnt = 0
        async for device_info in RngdAPI.list_devices():
            devices.append(
                RngdDevice(
                    model_name=device_info["model"],
                    serial=device_info["device_sn"],
                    device_id=str(cnt),
                    hw_location=device_info["pci_bus_id"],
                    memory_size=0,
                    processing_units=0,
                    numa_node=device_info["numa_node"],
                )
            )
            cnt += 1

        self._all_devices = devices
        return devices

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("rngd.device"): Decimal(len(devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            return {
                "rngd_support": True,
            }
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        # TODO: Implement
        return []

    async def gather_container_measures(
        self, ctx: StatContext, container_ids: Sequence[str]
    ) -> Sequence[ContainerMeasurement]:
        # TODO: Implement
        return []

    async def create_alloc_map(self) -> DiscretePropertyAllocMap:
        devices = await self.list_devices()
        dpam = DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: (
                    DeviceSlotInfo(SlotTypes.COUNT, SlotName("rngd.device"), Decimal(1))
                )
                for dev in devices
            },
            exclusive_slot_types=self.exclusive_slot_types,
        )
        return dpam

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        device_ids = [
            x.device_id
            for x in await self.list_devices()
            if x.device_id in device_alloc.get(SlotName("rngd.device"), {}).keys()
        ]
        devices: dict[str, str] = {}
        for alloc_idx, device_id in enumerate(device_ids):
            source_paths = await asyncio.get_running_loop().run_in_executor(
                None, glob.glob, f"/dev/rngd/npu{device_id}"
            )
            for source_path in source_paths:
                devices[str(source_path)] = str(source_path).replace(
                    f"npu{device_id}", f"npu{alloc_idx}"
                )

        return {
            "HostConfig": {
                "CapAdd": ["IPC_LOCK"],
                "IpcMode": "host",
                "Ulimits": [{"Name": "memlock", "Hard": -1, "Soft": -1}],
                "Sysctls": {"net.ipv6.conf.all.disable_ipv6": "0"},
                "Devices": [
                    {
                        "PathOnHost": host_path,
                        "PathInContainer": container_path,
                        "CgroupPermissions": "rwm",
                    }
                    for host_path, container_path in devices.items()
                ],
            }
        }

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: List[DeviceId] = []
        if SlotName("rngd.device") in device_alloc:
            device_ids.extend(device_alloc[SlotName("rngd.device")].keys())
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                proc = device.processing_units
                mem = BinarySize(device.memory_size)
                attached_devices.append({  # TODO: update common.types.DeviceModelInfo
                    "device_id": device.device_id,
                    "model_name": device.model_name,
                    "data": {
                        "proc": proc,
                        "mem": mem,
                    },
                })
        return attached_devices

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        if not self.enabled:
            return
        resource_spec = await get_resource_spec_from_container(container.backend_obj)
        if resource_spec is None:
            return
        if hasattr(alloc_map, "apply_allocation"):
            for slot_name, _ in self.slot_types:
                alloc_map.apply_allocation({
                    slot_name: resource_spec.allocations.get(
                        DeviceName("rngd"),
                        {},
                    ).get(
                        slot_name,
                        {
                            dev_id: Decimal(0)
                            for dev_id, dev_slot_info in alloc_map.device_slots.items()
                            if dev_slot_info.slot_name == slot_name
                        },
                    ),
                })
        else:  # older agents without lablup/backend.ai-agent#180
            alloc_map.allocations[SlotName("rngd.device")].update(
                resource_spec.allocations.get(
                    DeviceName("rngd"),
                    {},
                ).get(
                    SlotName("rngd.device"),
                    {},
                ),
            )

    async def generate_resource_data(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, str]:
        data: MutableMapping[str, str] = {}
        if not self.enabled:
            return data

        active_device_id_set: Set[DeviceId] = set()
        for slot_type, per_device_alloc in device_alloc.items():
            for dev_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    active_device_id_set.add(dev_id)
        active_device_ids = sorted(active_device_id_set, key=lambda v: int(v))
        data["FURIOSA_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "rngd.device",
            "description": "RNGD",
            "human_readable_name": "Furiosa RNGD Device",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "npu3",
        }
