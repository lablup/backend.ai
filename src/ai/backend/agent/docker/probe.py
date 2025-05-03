from __future__ import annotations

from typing import Callable, Optional

from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.common.events import (
    DanglingKernelDetected,
    EventProducer,
)
from ai.backend.common.types import ContainerId, KernelId

from ..probe import DanglingKernel
from ..types import (
    Container,
    ContainerStatus,
    KernelLifecycleStatus,
)
from ..utils import closing_async
from .utils import container_from_docker_container


class DockerKernelProbe:
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

    async def _get_container_info(self) -> Optional[Container]:
        cid = self._container_id_getter()
        if cid is None:
            return None
        async with closing_async(Docker()) as docker:
            try:
                container = await docker.containers.get(str(cid))
            except DockerError as e:
                if e.status == 404:
                    raise DanglingKernel
        return container_from_docker_container(container)

    def _compare_with_container(self, container: Optional[Container]) -> None:
        kernel_state = self._kernel_state_getter()
        match kernel_state:
            case KernelLifecycleStatus.PREPARING:
                if container is not None:
                    # container exists but kernel is hanging in PREPARING state
                    raise DanglingKernel
            case KernelLifecycleStatus.RUNNING:
                if container is None or container.status != ContainerStatus.RUNNING:
                    raise DanglingKernel
            case KernelLifecycleStatus.TERMINATING:
                # There might be a delay in the container status change
                # after the kernel is being terminated.
                pass

    async def probe(self, resource_ctx: None) -> None:
        try:
            container = await self._get_container_info()
            self._compare_with_container(container)
        except DanglingKernel:
            await self._event_producer.produce_event(DanglingKernelDetected(self._kernel_id))
