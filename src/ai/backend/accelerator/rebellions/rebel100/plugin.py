import logging
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any

import aiodocker

from ai.backend.accelerator.rebellions.common.atom_api import ATOMAPI
from ai.backend.accelerator.rebellions.common.plugin import AbstractATOMPlugin
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceName,
    SlotName,
    SlotTypes,
)
from ai.backend.logging.structured import StructuredLogger

from .types import Rebel100Device

log = StructuredLogger(logging.getLogger(__spec__.name))


class Rebel100Plugin(AbstractATOMPlugin[Rebel100Device]):
    key = DeviceName("rebel100")
    slot_types: Sequence[tuple[SlotName, SlotTypes]] = (
        (SlotName("rebel100.device"), SlotTypes("count")),
    )
    exclusive_slot_types: set[str] = {"rebel100.device"}
    config_name = "rebel100"
    executable_names: Sequence[str] = ("rbln-smi", "rbln-stat")
    stat_args: Sequence[str] = ("-g", "-j")
    device_names: Sequence[str] = ("RBLN-CR13",)
    # CDI always injects /dev/rsd0, and a card moved out of group 0 is invisible to the SDK there.
    enable_rsd_default = False

    _all_devices: list[Rebel100Device] | None
    _unknown_device_names: set[str]

    async def init(self, context: Any = None) -> None:
        self._unknown_device_names = set()
        await super().init(context)

    def _is_valid_device_name(self, name: str) -> bool:
        return name in self.device_names

    async def _list_devices(self) -> list[Rebel100Device]:
        stats = await ATOMAPI.get_stats(self._rbln_stat_path, self.stat_args)
        devices: list[Rebel100Device] = []
        for device_info in stats.devices:
            if not self._is_valid_device_name(device_info.name):
                if device_info.name not in self._unknown_device_names:
                    self._unknown_device_names.add(device_info.name)
                    log.warning(
                        "skipping device with unrecognized name",
                        plugin_name=self.key,
                        device_name=device_info.name,
                        device=device_info.device,
                    )
                continue
            devices.append(
                Rebel100Device(
                    model_name=device_info.name,
                    device_name=self.key,
                    serial=DeviceId(device_info.uuid),
                    device_id=device_info.device,
                    device_number=device_info.npu,
                    hw_location=device_info.pci.bus_id,
                    memory_size=int(device_info.memory.total),
                    processing_units=0,
                    numa_node=device_info.pci.numa_node,
                    rbln_stat_info=device_info,
                )
            )
        return devices

    async def _group_npus(self, devices: Iterable[Rebel100Device]) -> int:
        non_zero_groups: set[int] = {int(d.rbln_stat_info.group_id) for d in devices} - {0}
        if len(non_zero_groups) > 0:
            await ATOMAPI.destroy_groups(self._rbln_stat_path, list(non_zero_groups))

        assigned_device_ids = {d.device_id for d in devices}
        live_devices = await self._list_devices()
        device_indexes = [
            d.rbln_stat_info.npu for d in live_devices if d.device_id in assigned_device_ids
        ]
        return await ATOMAPI.create_group(self._rbln_stat_path, device_indexes, self.stat_args)

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        args = await super().generate_docker_args(docker, device_alloc)
        # Request only the assigned cards by host index (`rbln<N>`); `npu` is group-relative.
        kind = self.cdi_device_id.partition("=")[0]
        assigned = device_alloc.get(self.slot_types[0][0], {})
        host_config = args["HostConfig"]
        host_config["DeviceRequests"][0]["DeviceIDs"] = [
            f"{kind}={d.device_id.removeprefix('rbln')}"
            for d in await self._list_devices()
            if d.device_id in assigned
        ]
        # CDI injects the host-numbered /dev/rbln<N> and /dev/rsd0; renumbered copies collide.
        host_config["Devices"] = [
            d
            for d in host_config["Devices"]
            if not d["PathInContainer"].startswith(("/dev/rbln", "/dev/rsd"))
        ]
        return args

    async def list_device_files(self, device: Rebel100Device) -> Iterable[str]:
        return [f"/dev/{device.rbln_stat_info.device}"]

    def get_metadata(self) -> AcceleratorMetadata:
        # TODO(rebel100): provisional display values; confirm after the plugin is attached and the
        # WebUI is checked on the Rebel100 node (what one slot counts, product vs. family name).
        return {
            "slot_name": "rebel100.device",
            "description": "Rebel100",
            "human_readable_name": "Rebel100 Device",
            "display_unit": "Rebel100",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "rebel",
        }
