import logging
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceName,
    SlotName,
    SlotTypes,
)

from ..common.atom_api import ATOMAPI
from ..common.plugin import AbstractATOMPlugin
from .types import ATOMPlusDevice

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

VALID_DEVICE_NAME = ("RBLN-CA12", "RBLN-CA22")


class ATOMPlusPlugin(AbstractATOMPlugin[ATOMPlusDevice]):
    key = DeviceName("atom-plus")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("atom-plus.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"atom-plus.device"}

    _all_devices: Optional[List[ATOMPlusDevice]]

    async def _list_devices(self) -> List[ATOMPlusDevice]:
        stats = await ATOMAPI.get_stats(self._rbln_stat_path)
        devices: List[ATOMPlusDevice] = []
        for device_info in stats.devices:
            if device_info.name not in VALID_DEVICE_NAME:
                continue
            device = ATOMPlusDevice(
                model_name=f"RBLN {device_info.name}",
                device_name=self.key,
                serial=DeviceId(device_info.uuid),
                # Some ATOM test cards all show same, zero-filled UUID so we can't use UUID as device_id
                device_id=device_info.device,
                device_number=device_info.npu,
                hw_location=device_info.pci.bus_id,
                memory_size=int(device_info.memory.total),
                processing_units=0,
                numa_node=device_info.pci.numa_node,
                rbln_stat_info=device_info,
            )
            devices.append(device)

        return devices

    async def group_npus(
        self,
        devices: Iterable[ATOMPlusDevice],
    ) -> int:
        non_zero_groups: Set[int] = set([int(d.rbln_stat_info.group_id) for d in devices]) - set([
            0
        ])
        if len(non_zero_groups) > 0:
            await ATOMAPI.destroy_groups(self._rbln_stat_path, list(non_zero_groups))

        live_devices = await self._list_devices()
        device_indexes = [d.rbln_stat_info.npu for d in live_devices]
        group_idx = await ATOMAPI.create_group(self._rbln_stat_path, device_indexes)
        return group_idx

    async def list_device_files(
        self,
        device: ATOMPlusDevice,
    ) -> Iterable[str]:
        return [f"/dev/{device.rbln_stat_info.device}"]

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "atom-plus.device",
            "description": "ATOM Plus",
            "human_readable_name": "ATOM Plus Device",
            "display_unit": "ATOM+",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "rebel",
        }
