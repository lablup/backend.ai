from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from aiodocker.docker import Docker, DockerContainer

from ai.backend.agent.plugin.network import AbstractNetworkAgentPlugin, ContainerNetworkCapability
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

    additional_network_names: Iterable[str]
    network_plugin: Optional[AbstractNetworkAgentPlugin]
    container_bind_host: str

    host_ports: Sequence[int]
    exposed_ports: Sequence[int]


class ContainerStartSpecGenerator(ArgsSpecGenerator[ContainerStartSpec]):
    pass


@dataclass
class ContainerStartResult:
    pass


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
            await self._connect_additional_networks(docker, spec)

        await self._expose_network_ports(spec)
        return ContainerStartResult()

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

    async def _connect_additional_networks(self, docker: Docker, spec: ContainerStartSpec) -> None:
        """
        Connect the container to additional networks.
        """
        for network_name in spec.additional_network_names:
            network = await docker.networks.get(network_name)
            await network.connect({"Container": spec.container_id})

    async def _expose_network_ports(self, spec: ContainerStartSpec) -> None:
        """
        Expose network ports for the container.
        TODO: Move this code to network stage.
        """
        plugin = spec.network_plugin
        if plugin is None:
            return
        if ContainerNetworkCapability.GLOBAL in (await plugin.get_capabilities()):
            tmp_kernel_obj = TmpKernelObject(
                service_ports=list(spec.service_ports),
            )
            container_network_info = await plugin.expose_ports(
                tmp_kernel_obj,
                spec.container_bind_host,
                [
                    (host_port, container_port)
                    for host_port, container_port in zip(spec.host_ports, spec.exposed_ports)
                ],
            )

    @override
    async def teardown(self, resource: ContainerStartResult) -> None:
        pass


class ContainerStartStage(ProvisionStage[ContainerStartSpec, ContainerStartResult]):
    """
    Stage for creating bootstrap scripts in kernel containers.
    """

    pass
