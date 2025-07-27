from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

# TODO: Implement DockerCodeRunner
from ai.backend.common.types import DeviceId


@dataclass
class ContainerOwnershipData:
    # Override UID/GID settings
    uid_override: Optional[int]
    gid_override: Optional[int]

    kernel_features: frozenset[str]
    kernel_uid: int
    kernel_gid: int


class HostPortBinding(BaseModel):
    model_config = ConfigDict(extra="allow")

    host_port: str = Field(serialization_alias="HostPort")
    host_ip: str = Field(serialization_alias="HostIp")


class Ulimit(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(serialization_alias="Name")
    soft: int = Field(serialization_alias="Soft")
    hard: int = Field(serialization_alias="Hard")


DEFAULT_ULIMITS = [
    Ulimit(name="nofile", soft=1048576, hard=1048576),
    Ulimit(name="memlock", soft=-1, hard=-1),
]


class LogConfigInfo(BaseModel):
    """
    Log configuration for Docker containers.
    The fields must be str
    (ref: https://docs.docker.com/config/containers/logging/local/)
    """

    model_config = ConfigDict(extra="allow")

    max_size: str = Field(serialization_alias="max-size")
    max_file: str = Field(serialization_alias="max-file")
    compress: str = Field(default="false", serialization_alias="compress")


class LogConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = Field(
        default="local",
        serialization_alias="Type",
        description="Set 'local' for efficient docker-specific storage",
    )
    config: LogConfigInfo = Field()


class DeviceInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    path_on_host: str = Field(serialization_alias="PathOnHost")
    path_in_container: str = Field(serialization_alias="PathInContainer")
    cgroup_permissions: str = Field(default="rwm", serialization_alias="CgroupPermissions")


class DeviceRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    driver: str = Field(serialization_alias="Driver")
    device_ids: list[DeviceId] = Field(serialization_alias="DeviceIDs")
    capabilities: list[list[str]] = Field(serialization_alias="Capabilities")


class ContainerConfigHostConfig(BaseModel):
    """
    Configuration for creating a Docker container.
    This configuration is used to set 'HostConfig' for a ContainerConfig.

    This allows extra fields because compute plugins may inject additional fields.
    """

    model_config = ConfigDict(extra="allow")

    # Defaults
    init: bool = Field(default=True, serialization_alias="Init")
    publish_all_ports: bool = Field(
        default=False,
        serialization_alias="PublishAllPorts",
        description="we manage port mapping manually",
    )
    cap_add: list[str] = Field(
        default_factory=lambda: ["IPC_LOCK", "SYS_NICE"],
        serialization_alias="CapAdd",
        description="IPC_LOCK for hugepages and RDMA, SYS_NICE for NFS based GPUDirect Storage",
    )
    ulimits: list[Ulimit] = Field(
        default_factory=lambda: DEFAULT_ULIMITS,
        serialization_alias="Ulimits",
    )

    port_bindings: dict[str, list[HostPortBinding]] = Field(serialization_alias="PortBindings")
    log_config: LogConfig = Field(serialization_alias="LogConfig")

    # Intrinsic resource config
    # CPU
    # cpus: int = Field(serialization_alias="Cpus")
    # cpuset_cpus: str = Field(serialization_alias="CpusetCpus")
    cpu_period: Optional[int] = Field(default=None, serialization_alias="CpuPeriod")
    cpu_quota: Optional[int] = Field(default=None, serialization_alias="CpuQuota")

    # Memory
    memory_swap: Optional[int] = Field(
        default=None,
        serialization_alias="MemorySwap",
    )
    memory: Optional[int] = Field(
        default=None,
        serialization_alias="Memory",
    )
    shmsize: Optional[int] = Field(default=None, serialization_alias="ShmSize")
    security_opt: Optional[list[str]] = Field(default=None, serialization_alias="SecurityOpt")

    # Optional fields injected by compute plugins
    devices: Optional[list[DeviceInfo]] = Field(
        default=None,
        serialization_alias="Devices",
    )
    device_requests: Optional[list[DeviceRequest]] = Field(
        default=None, serialization_alias="DeviceRequests"
    )
    runtime: Optional[str] = Field(default=None, serialization_alias="Runtime")
    ipc_mode: Optional[str] = Field(default=None, serialization_alias="IpcMode")
    sysctls: Optional[dict[str, str]] = Field(default=None, serialization_alias="Sysctls")


class NetworkingConfig(BaseModel):
    """
    Configuration for networking in Docker containers.
    This configuration is used to set 'NetworkingConfig' for a ContainerConfig.
    """

    model_config = ConfigDict(extra="allow")

    endpoints_config: Optional[dict[str, dict[str, Any]]] = Field(
        default=None,
        serialization_alias="EndpointsConfig",
    )


class ContainerConfig(BaseModel):
    """
    Configuration for creating a Docker container.
    This configuration is used to create a Docker container with specific settings.
    """

    tty: bool = Field(
        default=True,
        serialization_alias="Tty",
    )
    open_stdin: bool = Field(
        default=True,
        serialization_alias="OpenStdin",
    )
    privileged: bool = Field(
        default=False,
        serialization_alias="Privileged",
    )
    stop_signal: str = Field(
        default="SIGINT",
        serialization_alias="StopSignal",
    )
    entry_point: list[str] = Field(
        default_factory=lambda: ["/opt/kernel/entrypoint.sh"],
        serialization_alias="EntryPoint",
    )
    working_dir: str = Field(default="/home/work", serialization_alias="WorkingDir")

    image: str = Field(
        serialization_alias="Image",
    )
    exposed_ports: dict[str, dict] = Field(serialization_alias="ExposedPorts")
    cmd: list[str] = Field(serialization_alias="Cmd")
    env: list[str] = Field(serialization_alias="Env")
    host_name: str = Field(serialization_alias="HostName")
    labels: Mapping[str, Optional[str]] = Field(serialization_alias="Labels")
    host_config: ContainerConfigHostConfig = Field(serialization_alias="HostConfig")

    network_mode: Optional[str] = Field(default=None, serialization_alias="NetworkMode")
    networking_config: Optional[NetworkingConfig] = Field(
        default=None, serialization_alias="NetworkingConfig"
    )


@dataclass
class NetworkConfig:
    mode: Optional[str]
    network_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "network_name": self.network_name,
        }


@dataclass
class PortMapping:
    """
    Represents a port mapping for a Docker container.
    This is used to map container ports to host ports.
    """

    exposed_port: int
    host_port: int
    host_ip: str
