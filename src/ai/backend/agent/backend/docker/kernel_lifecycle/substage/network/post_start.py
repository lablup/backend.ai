from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Optional, override

from aiodocker.docker import Docker
from aiodocker.types import PortInfo

from ai.backend.agent.plugin.network import (
    AbstractNetworkAgentPlugin,
    ContainerNetworkCapability,
    ContainerNetworkInfo,
)
from ai.backend.common.asyncio import closing_async
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    ContainerId,
    ServicePort,
)

from ...defs import REPL_IN_PORT, REPL_OUT_PORT
from ..types import PortMapping


@dataclass
class NetworkPostSetupSpec:
    container_id: ContainerId

    mode: str
    network_plugin: Optional[AbstractNetworkAgentPlugin]
    container_bind_host: str
    additional_network_names: Iterable[str]

    service_ports: Sequence[ServicePort]
    port_mappings: Sequence[PortMapping]
    advertised_kernel_host: Optional[str]


class NetworkPostSetupSpecGenerator(ArgsSpecGenerator[NetworkPostSetupSpec]):
    pass


@dataclass
class NetworkPostSetupResult:
    kernel_host: str
    repl_in_port: int
    repl_out_port: int

    service_ports: list[ServicePort]  # Why is it needed?


@dataclass
class TmpKernelObject:
    service_ports: list[ServicePort]


class NetworkPostSetupProvisioner(Provisioner[NetworkPostSetupSpec, NetworkPostSetupResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-network-post-setup"

    @override
    async def setup(self, spec: NetworkPostSetupSpec) -> NetworkPostSetupResult:
        async with closing_async(Docker()) as docker:
            await self._connect_additional_networks(spec, docker)
            result = await self._get_real_port_mapping(spec, docker)
        return result

    async def _connect_additional_networks(
        self, spec: NetworkPostSetupSpec, docker: Docker
    ) -> None:
        for name in spec.additional_network_names:
            network = await docker.networks.get(name)
            await network.connect({"Container": spec.container_id})

    async def _expose_ports_from_plugin(
        self, spec: NetworkPostSetupSpec
    ) -> Optional[ContainerNetworkInfo]:
        plugin = spec.network_plugin
        if plugin is None:
            return None
        if ContainerNetworkCapability.GLOBAL in (await plugin.get_capabilities()):
            tmp_kernel_obj = TmpKernelObject(
                service_ports=list(spec.service_ports),
            )
            port_mappings = [
                (port_mapping.host_port, port_mapping.exposed_port)
                for port_mapping in spec.port_mappings
            ]
            container_network_info = await plugin.expose_ports(
                tmp_kernel_obj,
                spec.container_bind_host,
                port_mappings,
            )
            return container_network_info
        return None

    async def _get_real_port_mapping(
        self, spec: NetworkPostSetupSpec, docker: Docker
    ) -> NetworkPostSetupResult:
        container_network_info = await self._expose_ports_from_plugin(spec)
        if container_network_info is not None:
            return await self._get_port_info_from_plugin(spec, container_network_info)
        else:
            return await self._get_port_info_from_docker(spec, docker)

    def _check_port_no(
        self,
        port_name: str,
        port_no: Optional[int],
    ) -> int:
        if port_no is None:
            raise RuntimeError(f"Container does not expose port {port_name} as expected.")
        return port_no

    async def _get_port_info_from_plugin(
        self, spec: NetworkPostSetupSpec, container_network_info: ContainerNetworkInfo
    ) -> NetworkPostSetupResult:
        kernel_host = container_network_info.container_host
        port_map = container_network_info.services
        assert "replin" in port_map and "replout" in port_map

        repl_in_port = port_map["replin"][2000]
        repl_out_port = port_map["replout"][2001]

        final_service_ports: list[ServicePort] = []
        for sport in spec.service_ports:
            created_host_ports = tuple(
                port_map[sport["name"]][cport] for cport in sport["container_ports"]
            )
            final_service_ports.append({
                "name": sport["name"],
                "container_ports": sport["container_ports"],
                "host_ports": created_host_ports,
                "protocol": sport["protocol"],
                "is_inference": sport.get("is_inference", False),
            })
        return NetworkPostSetupResult(kernel_host, repl_in_port, repl_out_port, final_service_ports)

    async def _get_port_info_from_docker(
        self, spec: NetworkPostSetupSpec, docker: Docker
    ) -> NetworkPostSetupResult:
        container = docker.containers.container(spec.container_id)
        kernel_host = spec.advertised_kernel_host or spec.container_bind_host
        ctnr_host_port_map: dict[int, int] = {}
        repl_in_port: Optional[int] = None
        repl_out_port: Optional[int] = None
        for port in spec.port_mappings:
            exposed_port = port.exposed_port
            ports: Optional[list[PortInfo]] = await container.port(exposed_port)
            if not ports:
                raise RuntimeError(f"Container {spec.container_id} does not expose port {port}.")
            host_port = int(ports[0]["HostPort"])
            if host_port != port.host_port:
                raise RuntimeError(
                    f"Container {spec.container_id} does not expose port {port} as expected. "
                    f"Expected host port: {port.host_port}, got: {host_port}"
                )
            if port.exposed_port == REPL_IN_PORT:  # intrinsic
                repl_in_port = host_port
            elif port.exposed_port == REPL_OUT_PORT:  # intrinsic
                repl_out_port = host_port
            else:
                ctnr_host_port_map[port.exposed_port] = host_port
        final_service_ports: list[ServicePort] = []
        for sport in spec.service_ports:
            created_host_ports = tuple(
                ctnr_host_port_map[cport] for cport in sport["container_ports"]
            )
            final_service_ports.append({
                "name": sport["name"],
                "container_ports": sport["container_ports"],
                "host_ports": created_host_ports,
                "protocol": sport["protocol"],
                "is_inference": sport.get("is_inference", False),
            })
        final_repl_in_port = self._check_port_no("repl_in", repl_in_port)
        final_repl_out_port = self._check_port_no("repl_out", repl_out_port)
        return NetworkPostSetupResult(
            kernel_host=kernel_host,
            repl_in_port=final_repl_in_port,
            repl_out_port=final_repl_out_port,
            service_ports=final_service_ports,
        )

    @override
    async def teardown(self, resource: NetworkPostSetupResult) -> None:
        pass


class NetworkPostSetupStage(ProvisionStage[NetworkPostSetupSpec, NetworkPostSetupResult]):
    pass
