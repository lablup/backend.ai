from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import override

from aiodocker.docker import Docker, DockerContainer

from ai.backend.common.asyncio import closing_async
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import (
    ContainerId,
    ServicePort,
)
from ai.backend.common.utils import (
    AsyncFileWriter,
)


@dataclass
class ContainerStartSpec:
    container_id: ContainerId
    service_ports: Sequence[ServicePort]
    config_dir: Path


class ContainerStartSpecGenerator(ArgsSpecGenerator[ContainerStartSpec]):
    pass


@dataclass
class ContainerStartResult:
    container_id: ContainerId


@dataclass
class TmpKernelObject:
    service_ports: list[ServicePort]


class ContainerStartProvisioner(Provisioner[ContainerStartSpec, ContainerStartResult]):
    """
    Provisioner for starting Docker containers.
    - Write resource.txt
    - Start container
    - Set sudo session
    - Connect network
    """

    @property
    @override
    def name(self) -> str:
        return "docker-container-create"

    @override
    async def setup(self, spec: ContainerStartSpec) -> ContainerStartResult:
        await self._write_resource_txt(spec)

        async with closing_async(Docker()) as docker:
            container = await self._start_container(docker, spec)
            await self._set_sudo_session(container, spec)
        return ContainerStartResult(spec.container_id)

    async def _write_resource_txt(self, spec: ContainerStartSpec) -> None:
        """
        Write resource.txt file in the container.
        """
        async with AsyncFileWriter(
            target_filename=spec.config_dir / "resource.txt",
            access_mode="a",
        ) as writer:
            await writer.write(f"CID={spec.container_id}\n")

    async def _start_container(self, docker: Docker, spec: ContainerStartSpec) -> DockerContainer:
        container = docker.containers.container(spec.container_id)
        await container.start()
        return container

    async def _set_sudo_session(self, container: DockerContainer, spec: ContainerStartSpec) -> None:
        exec = await container.exec(
            [
                # file ownership is guaranteed to be set as root:root since command is executed on behalf of root user
                "sh",
                "-c",
                'mkdir -p /etc/sudoers.d && echo "work ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-bai-work',
            ],
            user="root",
        )
        shell_response = await exec.start(detach=True)
        if shell_response:
            raise RuntimeError(f"Failed to set up sudo session in container {spec.container_id}")

    @override
    async def teardown(self, resource: ContainerStartResult) -> None:
        async with closing_async(Docker()) as docker:
            container = docker.containers.container(resource.container_id)
            await container.stop()


class ContainerStartStage(ProvisionStage[ContainerStartSpec, ContainerStartResult]):
    """
    Stage for creating bootstrap scripts in kernel containers.
    """

    pass
