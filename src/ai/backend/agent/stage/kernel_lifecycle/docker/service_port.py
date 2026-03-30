from dataclasses import dataclass
from typing import override

from ai.backend.agent.exception import ServicePortAlreadyUsedError
from ai.backend.common.docker import LabelName
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
)
from ai.backend.common.types import ClusterRole, ServicePort, ServicePortProtocols

REPL_PORTS = (2000, 2001)


@dataclass
class ServicePortSpec:
    model_service_ports: list[ServicePort]
    preopen_ports: list[int]
    cluster_role: ClusterRole
    image_labels: dict[LabelName, str]
    allocated_host_ports: list[int]


class ServicePortSpecGenerator(ArgsSpecGenerator[ServicePortSpec]):
    pass


@dataclass
class ServicePortResult:
    service_ports: list[ServicePort]


class ServiceProvisioner(Provisioner[ServicePortSpec, ServicePortResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-service"

    @override
    async def setup(self, spec: ServicePortSpec) -> ServicePortResult:
        service_ports = [*spec.model_service_ports]
        service_ports += self._prepare_intrinsic_service_ports(spec)
        self._check_overlapping_ports(service_ports)
        service_ports += self._prepare_preopen_port(spec)
        self._check_overlapping_ports(service_ports)
        service_ports += self._prepare_image_defined_service_ports(spec)
        service_ports += self._prepare_internal_service_ports(spec)
        return ServicePortResult(service_ports=service_ports)

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

    def _prepare_preopen_port(self, spec: ServicePortSpec) -> list[ServicePort]:
        service_ports: list[ServicePort] = []
        if spec.cluster_role in ("main", "master"):
            for port_no in spec.preopen_ports:
                if port_no in REPL_PORTS:
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
        if spec.cluster_role in ("main", "master"):
            for sport in parse_service_ports(
                spec.image_labels.get(LabelName.SERVICE_PORTS, ""),
                spec.image_labels.get(LabelName.ENDPOINT_PORTS, ""),
            ):
                service_ports.append(sport)
        return service_ports

    def _prepare_internal_service_ports(self, spec: ServicePortSpec) -> list[ServicePort]:
        service_ports: list[ServicePort] = []
        if spec.cluster_role in ("main", "master"):
            for index, port in enumerate(spec.allocated_host_ports):
                service_ports.append({
                    "name": f"hostport{index + 1}",
                    "protocol": ServicePortProtocols.INTERNAL,
                    "container_ports": (port,),
                    "host_ports": (port,),
                    "is_inference": False,
                })
        return service_ports

    @override
    async def teardown(self, resource: ServicePortResult) -> None:
        return
