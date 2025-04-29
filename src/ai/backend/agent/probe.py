from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from ai.backend.common.events import (
    DanglingContainerDetected,
    DanglingKernelDetected,
    EventProducer,
)
from ai.backend.common.types import ContainerId, KernelId
from ai.backend.logging import BraceStyleAdapter

from .types import (
    Container,
    ContainerStatus,
    KernelLifecycleStatus,
)

if TYPE_CHECKING:
    from .kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DanglingKernel(Exception):
    pass


class DanglingContainer(Exception):
    pass


class BaseKernelProbe(ABC):
    def __init__(
        self,
        kernel_id: KernelId,
        kernel_state_getter: Callable[..., KernelLifecycleStatus],
        container_id_getter: Callable[..., Optional[ContainerId]],
        event_producer: EventProducer,
    ) -> None:
        self._kernel_id = kernel_id
        self._container_id_getter = container_id_getter
        self._kernel_state_getter = kernel_state_getter
        self._event_producer = event_producer

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
        container_enumerator: Callable[
            [frozenset[ContainerStatus]], Awaitable[Sequence[tuple[KernelId, Container]]]
        ],
        kernel_registry_getter: Callable[..., Mapping[KernelId, AbstractKernel]],
        event_producer: EventProducer,
    ) -> None:
        self._container_enumerator = container_enumerator
        self._kernel_registry_getter = kernel_registry_getter
        self._event_producer = event_producer

    async def probe(self) -> None:
        """
        Scan the kernel containers and check if they are in the kernel registry.
        Produce `DanglingContainerDetected` events if there are any.
        """
        try:
            async with asyncio.timeout(20):
                containers = await self._container_enumerator(ContainerStatus.all())
        except asyncio.TimeoutError:
            log.warning("scan_containers() timeout, continuing")
            return

        kernel_registry = self._kernel_registry_getter()
        for existing_kernel, container in containers:
            if existing_kernel not in kernel_registry:
                log.warning(
                    "scan_containers() detected dangling container (k:{},c:{})",
                    existing_kernel,
                    container.id,
                )
                await self._event_producer.produce_event(
                    DanglingContainerDetected(container.id),
                )

        existing_kernel_ids = set([k for k, _ in containers])
        for registered_kernel_id in kernel_registry:
            if registered_kernel_id not in existing_kernel_ids:
                log.warning(
                    "scan_containers() detected dangling kernel (k:{})",
                    registered_kernel_id,
                )
                await self._event_producer.produce_event(
                    DanglingKernelDetected(registered_kernel_id),
                )
