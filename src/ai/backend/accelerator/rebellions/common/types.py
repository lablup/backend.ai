from ai.backend.agent.resources import AbstractComputeDevice

__all__ = ("AbstractATOMDevice",)


class AbstractATOMDevice(AbstractComputeDevice):
    model_name: str

    def __init__(
        self,
        model_name: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name

    def __str__(self) -> str:
        return (
            f"ATOMDevice <{self.hw_location}, Memory {self.memory_size}, NUMA Node"
            f" #{self.numa_node}>"
        )

    def __repr__(self) -> str:
        return self.__str__()
