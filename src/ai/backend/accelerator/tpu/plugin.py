import asyncio
import logging
import re
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import Any, Collection, List, Mapping, MutableMapping, Sequence, Set, Tuple

import aiodocker

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ai.backend.agent.stats import ContainerMeasurement, NodeMeasurement, StatContext
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    SlotName,
    SlotTypes,
)

from . import __version__
from .tpu import libtpu

log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.tpu"))


class TPUDevice(AbstractComputeDevice):
    model_name: str

    def __init__(self, model_name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name


class TPUPlugin(AbstractComputePlugin):
    key = DeviceName("tpu")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("tpu.device"), SlotTypes("count")),
    )

    gcloud_sdk_version: Tuple[int, ...] = (0, 0, 0)
    enabled: bool = True

    async def init(self, context: Any = None) -> None:
        rx_sdk_version = re.compile(r"Google Cloud SDK (\d+\.\d+\.\d+)")
        try:
            proc = await asyncio.create_subprocess_exec(
                "gcloud",
                "version",
                stdout=subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            lines = stdout.decode().splitlines()
        except FileNotFoundError:
            log.warning("Gcloud SDK not found.")
            log.info("TPU acceleration is disabled.")
            self.enabled = False
        m = rx_sdk_version.search(lines[0])
        if m:
            self.gcloud_sdk_version = tuple(map(int, m.group(1).split(".")))
        else:
            log.error("could not detect gcloud version!")
            log.info("TPU acceleration is disabled.")
            self.enabled = False
            return

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(
        self,
        new_plugin_config: Mapping[str, Any],
    ) -> None:
        pass

    async def list_devices(self) -> Collection[TPUDevice]:
        all_devices = []
        num_devices = await libtpu.get_device_count()
        for dev_idx in range(num_devices):
            dev_name = await libtpu.get_device_name(dev_idx)
            raw_info = await libtpu.get_device_props(dev_name)
            dev_info = TPUDevice(
                device_id=DeviceId(str(dev_idx)),
                hw_location=raw_info["hw_location"],
                numa_node=None,
                memory_size=raw_info["memory_size"],
                model_name=raw_info["model_name"],
                processing_units=1,  # TPU sharing is not possible for now
            )
            all_devices.append(dev_info)
        return all_devices

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        slots = {
            # TODO: fractional alloc map
            SlotName("tpu.device"): Decimal(len(devices)),
        }
        return slots

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        if self.enabled:
            return {
                "tpu_support": "true",
                "gcloud_sdk_version": "{}.{}.{}".format(*self.gcloud_sdk_version),
            }
        else:
            return {
                "tpu_support": "false",
            }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        # TODO: Implement
        return []

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        # TODO: Implement
        return []

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            # TODO: fractional alloc map
            device_slots={
                dev.device_id: (DeviceSlotInfo(SlotTypes.COUNT, SlotName("tpu.device"), Decimal(1)))
                for dev in devices
            }
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ):
        assigned_device_ids: List[DeviceId] = []

        for slot_type, per_device_alloc in device_alloc.items():
            for device_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    assigned_device_ids.append(device_id)

        devices = await self.list_devices()
        for device in devices:
            if device.device_id in assigned_device_ids:
                # TODO: User code can access TPU with TPU_NAME environment variable. How to
                # make this eaiser if there are multiple TPU devices? Currently, we assume
                # there's only one TPU device.
                return {
                    "Env": [
                        f"TPU_VISIBLE_DEVICES={','.join(map(str, assigned_device_ids))}",
                        f"TPU_NAME={device.hw_location}",
                    ]
                }
        else:
            raise RuntimeError("Should not reach here")

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: List[DeviceId] = []
        if SlotName("tpu.device") in device_alloc:
            device_ids.extend(device_alloc[SlotName("tpu.device")].keys())
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                proc = device.processing_units
                mem = BinarySize(device.memory_size)
                attached_devices.append({  # TODO: update common.types.DeviceModelInfo
                    "device_id": device.device_id,
                    "model_name": device.hw_location,
                    "data": {
                        "proc": proc,
                        "mem": mem,
                    },
                })
        return attached_devices

    async def restore_from_container(cls, container, alloc_map):
        # TODO: implement!
        pass

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
        data["TPU_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data
