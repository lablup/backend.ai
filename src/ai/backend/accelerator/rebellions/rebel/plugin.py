import logging
from collections.abc import Iterable, Sequence

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

from .types import RebelDevice

log = StructuredLogger(logging.getLogger(__spec__.name))

# TODO(rebel100): the exact Rebel100 `name` reported by rbln-smi is unknown until the node is
# available (checklist step 5). Until then every `RBLN-CR*` name is accepted; set
# `device_names` in rebel.toml to restrict it to an exact list.
DEFAULT_DEVICE_NAME_PREFIXES = ("RBLN-CR",)


class RebelPlugin(AbstractATOMPlugin[RebelDevice]):
    key = DeviceName("rebel")
    slot_types: Sequence[tuple[SlotName, SlotTypes]] = (
        (SlotName("rebel.device"), SlotTypes("count")),
    )
    exclusive_slot_types: set[str] = {"rebel.device"}
    config_name = "rebel"
    executable_names: Sequence[str] = ("rbln-smi", "rbln-stat")

    _all_devices: list[RebelDevice] | None
    _unknown_device_names: set[str]

    def _is_valid_device_name(self, name: str) -> bool:
        configured = self.atom_config["general"].get("device_names")
        if configured:
            return name in configured
        return name.startswith(DEFAULT_DEVICE_NAME_PREFIXES)

    async def _list_devices(self) -> list[RebelDevice]:
        if not hasattr(self, "_unknown_device_names"):
            self._unknown_device_names = set()
        stats = await ATOMAPI.get_stats(self._rbln_stat_path)
        devices: list[RebelDevice] = []
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
                RebelDevice(
                    model_name=f"RBLN {device_info.name}",
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

    async def _group_npus(self, devices: Iterable[RebelDevice]) -> int:
        non_zero_groups: set[int] = {int(d.rbln_stat_info.group_id) for d in devices} - {0}
        if len(non_zero_groups) > 0:
            await ATOMAPI.destroy_groups(self._rbln_stat_path, list(non_zero_groups))

        assigned_device_ids = {d.device_id for d in devices}
        live_devices = await self._list_devices()
        device_indexes = [
            d.rbln_stat_info.npu for d in live_devices if d.device_id in assigned_device_ids
        ]
        return await ATOMAPI.create_group(self._rbln_stat_path, device_indexes)

    async def list_device_files(self, device: RebelDevice) -> Iterable[str]:
        return [f"/dev/{device.rbln_stat_info.device}"]

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "rebel.device",
            "description": "Rebellions REBEL",
            "human_readable_name": "REBEL Device",
            "display_unit": "REBEL",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "rebel",
        }
