from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, cast, override

from ai.backend.agent.types import KernelOwnershipData
from ai.backend.agent.utils import update_nested_dict
from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.json import load_json
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import BinarySize, ServicePort

from ..types import ContainerConfig, ContainerConfigHostConfig, LogConfig, LogConfigInfo


@dataclass
class ContainerConfigSpec:
    ownership_data: KernelOwnershipData

    image: ImageRef
    image_labels: Mapping[str, str]

    container_log_size: BinarySize
    container_log_file_count: int

    # Intrinsic compute plugins
    # cpus: int
    # cpuset_cpus: str
    # memory_swap: int
    # memory: int

    exposed_ports: Sequence[int]
    host_ports: Sequence[int]
    repl_ports: Sequence[int]
    service_ports: list[ServicePort]
    preopen_ports: Sequence[int]
    block_service_ports: bool

    environ: Mapping[str, str]
    cmdargs: list[str]
    cluster_hostname: str

    container_bind_host: str
    protected_services: tuple[str, ...]

    resource_container_args: Mapping[str, Any]
    network_container_args: Mapping[str, Any]


class ContainerConfigSpecGenerator(ArgsSpecGenerator[ContainerConfigSpec]):
    pass


@dataclass
class ContainerConfigResult:
    # config: ContainerConfig
    raw_config: dict[str, Any]


class ContainerConfigProvisioner(Provisioner[ContainerConfigSpec, ContainerConfigResult]):
    """
    Provisioner for bootstrap script creation.

    Creates bootstrap.sh script in the work directory if provided in kernel config.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-container-config"

    @override
    async def setup(self, spec: ContainerConfigSpec) -> ContainerConfigResult:
        # Prepare the container configuration
        image = spec.image.short if spec.image.is_local else spec.image.canonical
        container_log_file_size = BinarySize(
            spec.container_log_size // spec.container_log_file_count
        )
        labels = self._parse_labels(spec)
        labels = cast(dict[str, Optional[str]], labels)

        container_config = ContainerConfig(
            image=image,
            exposed_ports=spec.exposed_ports,
            cmd=spec.cmdargs,
            env=[f"{k}={v}" for k, v in spec.environ.items()],
            host_name=spec.cluster_hostname,
            labels=labels,
            host_config=ContainerConfigHostConfig(
                # cpus=spec.cpus,
                # cpuset_cpus=spec.cpuset_cpus,
                # memory_swap=spec.memory_swap,
                # memory=spec.memory,
                port_bindings=self._parse_port_bindings(spec),
                log_config=LogConfig(
                    config=LogConfigInfo(
                        max_size=f"{container_log_file_size:s}",
                        max_file=str(spec.container_log_file_count),
                    )
                ),
            ),
        )
        raw_container_arg = container_config.model_dump(by_alias=True)

        update_nested_dict(raw_container_arg, spec.resource_container_args)
        update_nested_dict(raw_container_arg, spec.network_container_args)
        extra_container_args = await self._get_extra_container_args()
        for extra_args in extra_container_args:
            update_nested_dict(raw_container_arg, extra_args)

        return ContainerConfigResult(raw_container_arg)

    def _parse_labels(self, spec: ContainerConfigSpec) -> dict[LabelName, Optional[str]]:
        service_ports = spec.image_labels.get(LabelName.SERVICE_PORTS, "").split(",")
        service_ports += [f"{port_no}:preopen:{port_no}" for port_no in spec.preopen_ports]
        service_ports = [port for port in service_ports if port]  # Filter out empty strings

        return {
            LabelName.KERNEL_ID: str(spec.ownership_data.kernel_id),
            LabelName.SESSION_ID: str(spec.ownership_data.session_id),
            LabelName.OWNER_USER: spec.ownership_data.owner_user_id_to_str,
            LabelName.OWNER_PROJECT: spec.ownership_data.owner_project_id_to_str,
            LabelName.OWNER_AGENT: str(spec.ownership_data.agent_id),
            LabelName.BLOCK_SERVICE_PORTS: ("1" if spec.block_service_ports else "0"),
        }

    async def _get_extra_container_args(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        extra_container_opts_name = "agent-docker-container-opts.json"
        for extra_container_opts_file in [
            Path("/etc/backend.ai") / extra_container_opts_name,
            Path.home() / ".config" / "backend.ai" / extra_container_opts_name,
            Path.cwd() / extra_container_opts_name,
        ]:
            if extra_container_opts_file.is_file():
                try:
                    file_data = extra_container_opts_file.read_bytes()
                    extra_container_opts = load_json(file_data)
                    result.append(extra_container_opts)
                except IOError:
                    pass
        return result

    def _parse_port_bindings(self, spec: ContainerConfigSpec) -> dict[str, list]:
        """
        Parse port bindings from the service ports and repl ports.
        """
        protected_service_ports: set[int] = set()
        host_ips: list[str] = []
        for sport in spec.service_ports:
            if sport["name"] in spec.protected_services:
                protected_service_ports.update(sport["container_ports"])
        for eport in spec.exposed_ports:
            if eport in spec.repl_ports:  # always protected
                host_ips.append("127.0.0.1")
            elif eport in protected_service_ports:  # check if protected by resource group type
                host_ips.append("127.0.0.1")
            else:
                host_ips.append(spec.container_bind_host)
        return {
            f"{eport}/tcp": [{"HostPort": str(hport), "HostIp": hip}]
            for eport, hport, hip in zip(spec.exposed_ports, spec.host_ports, host_ips)
        }

    @override
    async def teardown(self, resource: ContainerConfigResult) -> None:
        # Bootstrap script is cleaned up with scratch directory
        pass


class ContainerConfigStage(ProvisionStage[ContainerConfigSpec, ContainerConfigResult]):
    pass
