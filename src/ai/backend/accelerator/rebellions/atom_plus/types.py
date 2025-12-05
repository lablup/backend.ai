from ai.backend.common.types import DeviceId

from ..common.atom_api import ATOMDeviceStat
from ..common.types import AbstractATOMDevice

__all__ = ("ATOMPlusDevice",)


class ATOMPlusDevice(AbstractATOMDevice):
    model_name: str
    serial: DeviceId
    device_number: int

    rbln_stat_info: ATOMDeviceStat

    def __init__(
        self,
        model_name: str,
        serial: DeviceId,
        device_number: int,
        rbln_stat_info: ATOMDeviceStat,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(model_name, *args, **kwargs)
        self.serial = serial
        self.device_number = device_number
        self.rbln_stat_info = rbln_stat_info

    def __str__(self) -> str:
        return (
            f"ATOMPlusDevice <{self.hw_location}, Memory {self.memory_size}, NUMA Node"
            f" #{self.numa_node}>"
        )

    def __repr__(self) -> str:
        return self.__str__()
