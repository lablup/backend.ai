from ..types import AbstractGaudiDevice

__all__ = ("Gaudi3Device",)


class Gaudi3Device(AbstractGaudiDevice):
    def __str__(self) -> str:
        return (
            f"Habana Gaudi 2 <{self.hw_location}, Memory {self.memory_size}, NUMA Node"
            f" #{self.numa_node}>"
        )
