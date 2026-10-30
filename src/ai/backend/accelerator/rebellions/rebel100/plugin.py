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
    device_names: Sequence[str] = ("RBLN-CR13",)
    # CDI always injects /dev/rsd0, and a card moved out of group 0 is invisible to the SDK there.
    enable_rsd_default = False

    _all_devices: list[Rebel100Device] | None
    _unknown_device_names: set[str]

    async def init(self, context: Any = None) -> None:
        self._unknown_device_names = set()
        await super().init(context)
        if self.enabled and self.atom_config["general"]["enable_rsd"]:
            log.warning("ignoring enable_rsd: RSD groups are not supported", plugin_name=self.key)
            self._enable_rsd = False

    async def _list_devices(self) -> list[Rebel100Device]:
        stats = await ATOMAPI.get_stats(self._rbln_stat_path, self.stat_args)
        devices: list[Rebel100Device] = []
        for device_info in stats.devices:
            if device_info.name not in self.device_names:
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

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        args = await super().generate_docker_args(docker, device_alloc)
        # Request only the assigned cards by host index (`rbln<N>`); `npu` is group-relative.
        kind = self.cdi_device_id.partition("=")[0]
        assigned = sorted(
            (k for k, v in device_alloc.get(self.slot_types[0][0], {}).items() if v > 0),
            key=lambda k: int(k.removeprefix("rbln")),
        )
        host_config = args["HostConfig"]
        host_config["DeviceRequests"] = (
            [
                {
                    **host_config["DeviceRequests"][0],
                    "DeviceIDs": [f"{kind}={k.removeprefix('rbln')}" for k in assigned],
                }
            ]
            if assigned
            else []
        )
        # CDI injects the host-numbered /dev/rbln<N> and /dev/rsd0; renumbered copies collide.
        host_config["Devices"] = [
            d
            for d in host_config["Devices"]
            if not d["PathInContainer"].startswith(("/dev/rbln", "/dev/rsd"))
        ]
        return args

    def _container_device_files(self, container_info: Mapping[str, Any]) -> list[str]:
        # The /dev/rbln* entries are not in HostConfig.Devices; the cards come from the CDI ids.
        prefix = self.cdi_device_id.partition("=")[0] + "="
        return [
            f"/dev/rbln{device_id.removeprefix(prefix)}"
            for request in container_info["HostConfig"].get("DeviceRequests") or []
            for device_id in request.get("DeviceIDs") or []
            if device_id.startswith(prefix)
        ]

    async def list_device_files(self, device: Rebel100Device) -> Iterable[str]:
        return [f"/dev/{device.rbln_stat_info.device}"]

    def get_metadata(self) -> AcceleratorMetadata:
        # TODO(rebel100): provisional display values; confirm on a Rebel100 node.
        return {
            "slot_name": "rebel100.device",
            "description": "Rebel100",
            "human_readable_name": "Rebel100 Device",
            "display_unit": "Rebel100",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "rebel",
        }
