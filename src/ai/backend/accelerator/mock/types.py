from typing import AsyncContextManager, NamedTuple, Protocol, TypeVar

from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId


class MockDevice(AbstractComputeDevice):
    plugin_name: str
    model_name: str
    mother_uuid: DeviceId

    def __init__(
        self, plugin_name: str, model_name: str, mother_uuid: DeviceId, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.plugin_name = plugin_name
        self.model_name = model_name
        self.mother_uuid = mother_uuid

    def __str__(self) -> str:
        return f"{self.plugin_name}: {self.model_name} [{self.device_id}]"

    def __repr__(self) -> str:
        return self.__str__()


class CUDADevice(MockDevice):
    is_mig_device: bool

    def __init__(self, is_mig_device: bool, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.is_mig_device = is_mig_device


class DeviceStat(NamedTuple):
    device_id: DeviceId
    mem_total: int
    mem_used: int
    mem_free: int
    gpu_util: int
    mem_util: int
    power_usage: int  # milli-watts
    power_max: int  # milli-watts
    core_temperature: int


class ProcessStat(NamedTuple):
    # absolute value (bytes)
    used_gpu_memory: int
    # percent-based samples
    sm_util: int
    mem_util: int
    enc_util: int
    dec_util: int


class SupportsAsyncClose(Protocol):
    async def close(self) -> None: ...


_SupportsAsyncCloseT = TypeVar("_SupportsAsyncCloseT", bound=SupportsAsyncClose)


class closing_async(AsyncContextManager[_SupportsAsyncCloseT]):
    """
    A local copy of ai.backend.agent.utils.closing_async()
    to avoid version compatibility issues
    """

    def __init__(self, obj: _SupportsAsyncCloseT) -> None:
        self.obj = obj

    async def __aenter__(self) -> _SupportsAsyncCloseT:
        return self.obj

    async def __aexit__(self, *exc_info) -> None:
        await self.obj.close()
