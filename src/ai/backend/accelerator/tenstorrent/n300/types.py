from tt_tools_common.utils_common.tools_utils import PciChip

from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, DeviceName

__all__ = ("TTn300Device",)


class TTn300Device(AbstractComputeDevice):
    model_name: str
    serial: DeviceId
    device_number: int
    tt_pci_chip: PciChip
    tt_device_idx: int

    def __init__(
        self,
        model_name: str,
        serial: DeviceId,
        device_number: int,
        tt_pci_chip: PciChip,
        tt_device_idx: int,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.serial = serial
        self.device_number = device_number
        self.tt_pci_chip = tt_pci_chip
        self.tt_device_idx = tt_device_idx
        self._device_name = DeviceName(
            "tt-n300"
        )  # without this AbstractComputeDevice will infer TTn300Device.device_name as `ttn300`

    def __str__(self) -> str:
        return (
            f"TTn300Device <{self.hw_location}, Memory {self.memory_size}, NUMA Node"
            f" #{self.numa_node}>"
        )

    def __repr__(self) -> str:
        return self.__str__()
