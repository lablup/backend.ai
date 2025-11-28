from pathlib import Path
from typing import (
    Collection,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import pyhlml

from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceName,
    SlotName,
    SlotTypes,
)

from ..plugin import AbstractGaudiPlugin
from .types import Gaudi2Device

__all__ = (
    "PREFIX",
    "Gaudi2Plugin",
)

PREFIX = "gaudi2"


class Gaudi2Plugin(AbstractGaudiPlugin):
    key = DeviceName("gaudi2")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("gaudi2.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"gaudi2.device"}

    async def list_devices(self) -> Collection[Gaudi2Device]:
        if not self.enabled:
            return []

        if self._all_devices is not None:
            return self._all_devices

        num_devices = pyhlml.hlmlDeviceGetCount()

        devices: List[Gaudi2Device] = []
        for dev_idx in range(num_devices):
            if dev_idx in self.device_mask:
                continue
            handle = pyhlml.hlmlDeviceGetHandleByIndex(dev_idx)
            device_name = pyhlml.hlmlDeviceGetName(handle).decode()

            mem_info = pyhlml.hlmlDeviceGetMemoryInfo(handle)

            pci_info = pyhlml.hlmlDeviceGetPCIInfo(handle)
            pci_bus_id = pci_info.bus_id.decode()

            sysfs_node_path = f"/sys/bus/pci/devices/{pci_bus_id}/numa_node"
            node: Optional[int]
            try:
                node = int(Path(sysfs_node_path).read_text().strip())
            except OSError:
                node = None
            uuid = pyhlml.hlmlDeviceGetUUID(handle).decode()

            dev_info = Gaudi2Device(
                dev_idx=dev_idx,
                device_id=DeviceId(str(dev_idx)),
                hw_location=pci_bus_id,
                numa_node=node,
                memory_size=mem_info.total,
                processing_units=0,
                model_name=device_name,
                unique_id=uuid,
            )
            devices.append(dev_info)

        self._all_devices = devices
        return self._all_devices

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "gaudi2.device",
            "description": "Habana Gaudi 2",
            "human_readable_name": "Gaudi 2 Device",
            "display_unit": "HPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "gaudi",
        }
