from typing import List

from ai.backend.agent.resources import AbstractComputeDevice

__all__ = ("ROCmDevice",)


class ROCmXCD(AbstractComputeDevice):
    pass


class ROCmDevice(AbstractComputeDevice):
    model_name: str
    unique_id: str
    sku: str
    xcds: List[ROCmXCD]

    def __init__(
        self,
        model_name: str,
        unique_id: str,
        sku: str,
        xcds: List[ROCmXCD],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.unique_id = unique_id
        self.sku = sku
        self.xcds = xcds

    def __str__(self) -> str:
        return (
            f"AMD {self.model_name} (SKU {self.sku}) <{self.hw_location}, Memory"
            f" {self.memory_size}, NUMA Node #{self.numa_node}>"
        )

    def __repr__(self) -> str:
        return self.__str__()
