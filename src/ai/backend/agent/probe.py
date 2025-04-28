from __future__ import annotations

from abc import abstractmethod
from typing import Awaitable, Callable, Optional

from ai.backend.common.events import DanglingKernelDetected, EventProducer
from ai.backend.common.types import ContainerId, KernelId

from .types import (
    Container,
    KernelLifecycleStatus,
)


class DanglingKernel(Exception):
    pass


class BaseKernelProbe:
    def __init__(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        kernel_state: KernelLifecycleStatus,
        event_producer: EventProducer,
    ) -> None:
        self._kernel_id = kernel_id
        self._container_id = container_id
        self._kernel_state = kernel_state
        self._event_producer = event_producer

    def set_container_id(self, value: Optional[ContainerId]) -> None:
        self._container_id = value

    @abstractmethod
    async def _get_container_info(self) -> Optional[Container]:
        raise NotImplementedError

    @abstractmethod
    def _compare_with_container(self, container: Optional[Container]) -> None:
        raise NotImplementedError

    async def probe(self) -> None:
        try:
            container = await self._get_container_info()
            self._compare_with_container(container)
        except DanglingKernel:
            await self._event_producer.produce_event(DanglingKernelDetected(self._kernel_id))


class AgentProbe:
    def __init__(
        self,
        task: Callable[..., Awaitable[None]],
    ) -> None:
        self._task = task

    async def probe(self) -> None:
        await self._task()
