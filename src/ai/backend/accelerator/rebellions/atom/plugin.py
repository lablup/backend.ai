import logging
from typing import (
    Iterable,
    List,
)

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
)

from ..common.atom_api import ATOMAPI
from ..common.plugin import AbstractATOMPlugin
from .types import ATOMDevice

PREFIX = "atom"
VALID_DEVICE_NAME = ("ATOM", "RBLN-CA02")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ATOMPlugin(AbstractATOMPlugin[ATOMDevice]):
    async def list_devices(self) -> List[ATOMDevice]:
        if self._all_devices is not None:
            return self._all_devices
        stats = await ATOMAPI.get_stats(self._rbln_stat_path)
        devices: List[ATOMDevice] = []
        for device_info in stats.devices:
            if device_info.name not in VALID_DEVICE_NAME:
                continue
            device = ATOMDevice(
                device_name=self.key,
                model_name=f"RBLN {device_info.name}",
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

        self._all_devices = devices
        return self._all_devices

    async def list_device_files(
        self,
        device: ATOMDevice,
    ) -> Iterable[str]:
        return [f"/dev/{device.rbln_stat_info.device}"]

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "atom.device",
            "description": "ATOM",
            "human_readable_name": "ATOM Device",
            "display_unit": "ATOM",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "rebel",
        }
