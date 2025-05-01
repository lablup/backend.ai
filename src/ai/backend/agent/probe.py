from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Awaitable, Callable

from ai.backend.common.events import (
    DanglingContainerDetected,
    DanglingKernelDetected,
    EventProducer,
)
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from .types import (
    Container,
    ContainerStatus,
)

if TYPE_CHECKING:
    from .kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DanglingKernel(Exception):
    pass


class DanglingContainer(Exception):
    pass


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
