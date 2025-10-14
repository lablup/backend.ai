from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from aiodocker.docker import Docker

from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.asyncio import closing_async
from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import (
    ContainerId,
)


@dataclass
class ContainerCreateSpec:
    container_arg: dict[str, Any]
    image: ImageRef
    ownership_data: KernelOwnershipData


class ContainerCreateSpecGenerator(ArgsSpecGenerator[ContainerCreateSpec]):
    pass


@dataclass
class ContainerCreateResult:
    container_id: ContainerId


class ContainerCreateProvisioner(Provisioner[ContainerCreateSpec, ContainerCreateResult]):
    """
    Provisioner for creating Docker containers based on the provided specifications.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-container-create"

    @override
    async def setup(self, spec: ContainerCreateSpec) -> ContainerCreateResult:
        container_arg = spec.container_arg
        # update_nested_dict(container_arg, spec.resource_container_args)
        # update_nested_dict(container_arg, spec.network_container_args)
        # extra_container_args = await self._get_extra_container_args()
        # for extra_args in extra_container_args:
        #     update_nested_dict(container_arg, extra_args)

        kernel_name = self._get_kernel_name(spec)
        container_id = await self._create_container(container_arg, kernel_name)
        return ContainerCreateResult(
            container_id=container_id,
        )

    def _get_kernel_name(self, spec: ContainerCreateSpec) -> str:
        """
        Generate a unique kernel name based on the image name and kernel ID.
        """
        return f"kernel.{spec.image.name.split('/')[-1]}.{spec.ownership_data.kernel_id}"

    async def _create_container(
        self, container_arg: Mapping[str, Any], kernel_name: str
    ) -> ContainerId:
        async with closing_async(Docker()) as docker:
            container = await docker.containers.create(config=container_arg, name=kernel_name)
        return ContainerId(container.id)

    @override
    async def teardown(self, resource: ContainerCreateResult) -> None:
        async with closing_async(Docker()) as docker:
            container = docker.containers.container(resource.container_id)
            await container.delete(force=True, v=True)


class ContainerCreateStage(ProvisionStage[ContainerCreateSpec, ContainerCreateResult]):
    """
    Stage for creating bootstrap scripts in kernel containers.
    """

    pass
