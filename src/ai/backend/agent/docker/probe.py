from __future__ import annotations

from typing import Optional, override

from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

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
    @override
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

    @override
    def _compare_with_container(self, container: Optional[Container]) -> None:
        kernel_state = self._kernel_state_getter()
        match kernel_state:
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
