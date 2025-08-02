from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.exception import ServicePortAlreadyUsedError
from ai.backend.common.docker import LabelName
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    ClusterRole,
    ClusterSSHPortMapping,
    ResourceGroupType,
    ServicePort,
    ServicePortProtocols,
)

from ..defs import REPL_IN_PORT, REPL_OUT_PORT
from .types import PortMapping

PROTECTED_SERVICE_HOST_IP = "127.0.0.1"


@dataclass
class ServicePortSpec:
    preopen_ports: list[int]
    cluster_role: ClusterRole
    cluster_hostname: str
    image_labels: Mapping[LabelName, str]
    allocated_host_ports: list[int]
    container_bind_host: str

    resource_group_type: ResourceGroupType

    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping]


class ServicePortSpecGenerator(ArgsSpecGenerator[ServicePortSpec]):
    pass


@dataclass
class ServicePortResult:
    service_ports: list[ServicePort]

    port_mapping_result: list[PortMapping]

    repl_in_port: int
    repl_out_port: int

    service_port_container_label: str


class ServicePortProvisioner(Provisioner[ServicePortSpec, ServicePortResult]):
    def __init__(self, agent_config: AgentUnifiedConfig) -> None:
        self._host_port_pool = set(
            range(
                agent_config.container.port_range[0],
                agent_config.container.port_range[1] + 1,
            )
        )

    @property
    @override
    def name(self) -> str:
        return "docker-service"

    @override
    async def setup(self, spec: ServicePortSpec) -> ServicePortResult:
        service_ports: list[ServicePort] = []
        service_ports += self._prepare_intrinsic_service_ports(spec)
        self._check_overlapping_ports(service_ports)
        service_ports += self._prepare_preopen_port(spec)
        self._check_overlapping_ports(service_ports)
        service_ports += self._prepare_image_defined_service_ports(spec)
        service_ports += self._prepare_internal_service_ports(spec)

        port_mappings = self._parse_port_mapping(spec, service_ports)
        service_port_label = self._parse_service_ports_label(spec)

        return ServicePortResult(
            service_ports=service_ports,
            port_mapping_result=port_mappings,
            repl_in_port=REPL_IN_PORT,
            repl_out_port=REPL_OUT_PORT,
            service_port_container_label=service_port_label,
        )

    def _check_overlapping_ports(self, service_ports: list[ServicePort]) -> None:
        used_ports: dict[int, list[str]] = {}  # port number to service name list mapping
        for sport in service_ports:
            for port in sport["container_ports"]:
                if port in used_ports:
                    used_ports[port].append(sport["name"])
                else:
                    used_ports[port] = [sport["name"]]
        overlapping_ports = {port: names for port, names in used_ports.items() if len(names) > 1}
        if overlapping_ports:
            raise ServicePortAlreadyUsedError(
                f"Overlapping ports found: {', '.join(f'{port} ({", ".join(names)})' for port, names in overlapping_ports.items())}"
            )

    def _prepare_intrinsic_service_ports(self, spec: ServicePortSpec) -> list[ServicePort]:
        return [
            {
                "name": "sshd",
                "protocol": ServicePortProtocols.TCP,
                "container_ports": (2200,),
                "host_ports": (None,),
                "is_inference": False,
            },
            {
                "name": "ttyd",
                "protocol": ServicePortProtocols.HTTP,
                "container_ports": (7681,),
                "host_ports": (None,),
                "is_inference": False,
            },
        ]

    def _is_repl_port(self, port_no: int) -> bool:
        return port_no in (REPL_IN_PORT, REPL_OUT_PORT)

    def _is_repl_service_port(self, service_port: ServicePort) -> bool:
        return any(self._is_repl_port(port) for port in service_port["container_ports"])

    def _is_cluster_main(self, spec: ServicePortSpec) -> bool:
        return spec.cluster_role in ("main", "master")

    def _prepare_preopen_port(self, spec: ServicePortSpec) -> list[ServicePort]:
        service_ports: list[ServicePort] = []
        if self._is_cluster_main(spec):
            for port_no in spec.preopen_ports:
                if self._is_repl_port(port_no):
                    raise ServicePortAlreadyUsedError(
                        "Port 2000 and 2001 are reserved for internal use"
                    )

                preopen_sport: ServicePort = {
                    "name": str(port_no),
                    "protocol": ServicePortProtocols.PREOPEN,
                    "container_ports": (port_no,),
                    "host_ports": (None,),
                    "is_inference": False,
                }
                service_ports.append(preopen_sport)
        return service_ports

    def _prepare_image_defined_service_ports(self, spec: ServicePortSpec) -> list[ServicePort]:
        service_ports: list[ServicePort] = []
        if self._is_cluster_main(spec):
            for sport in parse_service_ports(
                spec.image_labels.get(LabelName.SERVICE_PORTS, ""),
                spec.image_labels.get(LabelName.ENDPOINT_PORTS, ""),
            ):
                service_ports.append(sport)
        return service_ports

    def _prepare_internal_service_ports(self, spec: ServicePortSpec) -> list[ServicePort]:
        service_ports: list[ServicePort] = []
        if self._is_cluster_main(spec):
            for index, port in enumerate(spec.allocated_host_ports):
                service_ports.append({
                    "name": f"hostport{index + 1}",
                    "protocol": ServicePortProtocols.INTERNAL,
                    "container_ports": (port,),
                    "host_ports": (port,),
                    "is_inference": False,
                })
        return service_ports

    def _parse_port_mapping(
        self, spec: ServicePortSpec, service_ports: Iterable[ServicePort]
    ) -> list[PortMapping]:
        port_mappings: list[PortMapping] = [
            PortMapping(
                exposed_port=REPL_IN_PORT,
                host_port=self._host_port_pool.pop(),
                host_ip=PROTECTED_SERVICE_HOST_IP,
            ),
            PortMapping(
                exposed_port=REPL_OUT_PORT,
                host_port=self._host_port_pool.pop(),
                host_ip=PROTECTED_SERVICE_HOST_IP,
            ),
        ]

        for sport in service_ports:
            if (
                self._is_ssh_port(sport)
                and (ssh_host_ip_and_port := self._get_ssh_host_ip_and_port(spec, sport))
                is not None
            ):
                _, host_port = ssh_host_ip_and_port
                if len(sport["container_ports"]) != 1:
                    raise RuntimeError(
                        f"SSH host port {host_port} must be mapped to a single container port, but got {sport['container_ports']}"
                    )
                cport = sport["container_ports"][0]
                port_mappings.append(
                    PortMapping(
                        exposed_port=cport,
                        host_port=host_port,
                        host_ip=spec.container_bind_host,
                    )
                )
            elif self._is_repl_service_port(sport) or self._is_protected_service_port(spec, sport):
                for cport in sport["container_ports"]:
                    hport = self._host_port_pool.pop()
                    port_mappings.append(
                        PortMapping(
                            exposed_port=cport,
                            host_port=hport,
                            host_ip=PROTECTED_SERVICE_HOST_IP,
                        )
                    )
            else:
                for cport in sport["container_ports"]:
                    hport = self._host_port_pool.pop()
                    port_mappings.append(
                        PortMapping(
                            exposed_port=cport,
                            host_port=hport,
                            host_ip=spec.container_bind_host,
                        )
                    )
        return port_mappings

    def _is_ssh_port(self, service_port: ServicePort) -> bool:
        return service_port["name"] == "sshd"

    def _get_ssh_host_ip_and_port(
        self, spec: ServicePortSpec, service_port: ServicePort
    ) -> Optional[tuple[str, int]]:
        if (
            spec.cluster_ssh_port_mapping is None
            or (ssh_host_info := spec.cluster_ssh_port_mapping.get(spec.cluster_hostname)) is None
        ):
            return None
        host_ip, host_port = ssh_host_info
        return host_ip, host_port

    def _is_protected_service_port(self, spec: ServicePortSpec, service_port: ServicePort) -> bool:
        match spec.resource_group_type:
            case ResourceGroupType.COMPUTE:
                return False
            case ResourceGroupType.STORAGE:
                return service_port["name"] == "ttyd"

    def _parse_service_ports_label(self, spec: ServicePortSpec) -> str:
        service_ports_label: list[str] = []
        service_ports_label += spec.image_labels.get(LabelName.SERVICE_PORTS, "").split(",")
        service_ports_label += [f"{port_no}:preopen:{port_no}" for port_no in spec.preopen_ports]

        return ",".join([label for label in service_ports_label if label])

    @override
    async def teardown(self, resource: ServicePortResult) -> None:
        port_mappings = resource.port_mapping_result
        for port_mapping in port_mappings:
            self._host_port_pool.add(port_mapping.host_port)


class ServicePortStage(ProvisionStage[ServicePortSpec, ServicePortResult]):
    pass
