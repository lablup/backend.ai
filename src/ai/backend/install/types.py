import dataclasses
import enum

from ai.backend.common.types import HostPortPair


class InstallModes(enum.StrEnum):
    DEVELOP = "DEVELOP"
    PACKAGE = "PACKAGE"
    MAINTAIN = "MAINTAIN"


class Platform(enum.StrEnum):
    LINUX_ARM64 = "linux-aarch64"
    LINUX_X86_64 = "linux-x86_64"
    MACOS_ARM64 = "macos-arm64"
    MACOS_X86_64 = "macos-x86_64"


@dataclasses.dataclass()
class OSInfo:
    platform: Platform
    distro: str


@dataclasses.dataclass()
class HalfstackConfig:
    postgres_addr: HostPortPair
    redis_addr: list[HostPortPair]  # multiple if HA
    etcd_addr: list[HostPortPair]  # multiple if HA


@dataclasses.dataclass()
class ServiceConfig:
    manager_bind: HostPortPair
    manager_ipc_base_path: str
    manager_var_base_path: str
    web_bind: HostPortPair
    web_ipc_base_path: str
    web_var_base_path: str
    agent_rpc_bind: HostPortPair
    agent_watcher_bind: HostPortPair
    agent_ipc_base_path: str
    agent_var_base_path: str
    storage_manager_facing_bind: HostPortPair
    storage_client_facing_bind: HostPortPair
    storage_ipc_base_path: str
    storage_var_base_path: str
    storage_agent_rpc_bind: HostPortPair
    storage_agent_ipc_base_path: str
    storage_agent_var_base_path: str
    storage_watcher_bind: HostPortPair


@dataclasses.dataclass()
class DevInstallConfig:
    editable_webui: bool
    ha_halfstack: bool
    service_config: ServiceConfig
    halfstack_config: HalfstackConfig


@dataclasses.dataclass()
class PackageInstallConfig:
    download: bool
    service_config: ServiceConfig
    halfstack_config: HalfstackConfig
