from dataclasses import dataclass
from typing import List

from ..common.atom_api import ATOMDeviceStat
from ..common.types import AbstractATOMDevice

__all__ = (
    "ATOMMaxDevice",
    "ATOMMaxChildDevice",
)


@dataclass
class ATOMMaxChildDevice:
    serial: str
    hw_location: str
    device_number: int
    rbln_stat_info: ATOMDeviceStat


class ATOMMaxDevice(AbstractATOMDevice):
    model_name: str
    children: List[ATOMMaxChildDevice]

    def __init__(
        self,
        model_name: str,
        children: List[ATOMMaxChildDevice],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(model_name, *args, **kwargs)
        self.children = children

    def __str__(self) -> str:
        return (
            f"ATOMMaxDevice <SID {self.device_id}, Memory {self.memory_size}, NUMA Node"
            f" #{self.numa_node}>"
        )

    def __repr__(self) -> str:
        return self.__str__()
