from ..types import AbstractGaudiDevice

__all__ = ("Gaudi2Device",)


class Gaudi2Device(AbstractGaudiDevice):
    def __str__(self) -> str:
        return (
            f"Habana Gaudi 2 <{self.hw_location}, Memory {self.memory_size}, NUMA Node"
            f" #{self.numa_node}>"
        )
