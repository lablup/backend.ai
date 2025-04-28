from __future__ import annotations

from typing import Optional, override

from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.common.events import EventProducer
from ai.backend.common.types import ContainerId, KernelId

from ..probe import BaseKernelProbe
from ..types import (
    Container,
    ContainerStatus,
    KernelLifecycleStatus,
)
from ..utils import closing_async
from .utils import container_from_docker_container


class DanglingKernel(Exception):
    pass


class DockerKernelProbe(BaseKernelProbe):
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

    def set_kernel_state(self, value: KernelLifecycleStatus) -> None:
        self._kernel_state = value

    @override
    async def _get_container_info(self) -> Optional[Container]:
        if self._container_id is None:
            return None
        async with closing_async(Docker()) as docker:
            try:
                container = await docker.containers.get(self._container_id)
            except DockerError as e:
                if e.status == 404:
                    raise DanglingKernel
        return container_from_docker_container(container)

    @override
    def _compare_with_container(self, container: Optional[Container]) -> None:
        match self._kernel_state:
            case KernelLifecycleStatus.PREPARING:
                if container is None:
                    pass
                else:
                    # container exists but kernel is hanging in PREPARING state
                    raise DanglingKernel
            case KernelLifecycleStatus.RUNNING:
                if container is None or container.status != ContainerStatus.RUNNING:
                    raise DanglingKernel
            case KernelLifecycleStatus.TERMINATING:
                # There might be a delay in the container status change
                # after the kernel is being terminated.
                pass
