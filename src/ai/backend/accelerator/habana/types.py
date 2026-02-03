from typing import TypeVar

from ai.backend.agent.resources import AbstractComputeDevice

__all__ = ("AbstractGaudiDevice",)


class AbstractGaudiDevice(AbstractComputeDevice):
    model_name: str
    unique_id: str
    dev_idx: int

    def __init__(
        self,
        dev_idx: int,
        model_name: str,
        unique_id: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.dev_idx = dev_idx
        self.model_name = model_name
        self.unique_id = unique_id

    def __repr__(self) -> str:
        return self.__str__()


TDevice = TypeVar("TDevice", bound=AbstractGaudiDevice)
