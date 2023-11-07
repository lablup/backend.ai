from __future__ import annotations

import dataclasses
import enum
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from rich.console import ConsoleRenderable
from rich.text import Text

from ai.backend.common.types import HostPortPair

from . import __version__


class InstallModes(enum.StrEnum):
    DEVELOP = "DEVELOP"
    PACKAGE = "PACKAGE"
    MAINTAIN = "MAINTAIN"


class PackageSource(enum.StrEnum):
    GITHUB_RELEASE = "github-release"
    LOCAL_DIR = "local-dir"


class InstallType(enum.StrEnum):
    SOURCE = "source"
    PACKAGE = "package"


class Platform(enum.StrEnum):
    LINUX_ARM64 = "linux-aarch64"
    LINUX_X86_64 = "linux-x86_64"
    MACOS_ARM64 = "macos-arm64"
    MACOS_X86_64 = "macos-x86_64"


@dataclasses.dataclass()
class CliArgs:
    mode: InstallModes | None
    target_path: str


class ConfigError(Exception):
    def __rich__(self) -> ConsoleRenderable:
        return Text.from_markup(f"[bold red]ConfigError: [bold white]{self.args[0]}[/]")


class DistInfo(BaseModel):
    version: str = __version__
    package_source: PackageSource = PackageSource.GITHUB_RELEASE
    package_dir: Path = Field(default_factory=Path.cwd)
    use_fat_binary: bool = False
    target_path: Path = Field(default_factory=lambda: Path.home() / "backendai")


class InstallInfo(BaseModel):
    version: str
    type: InstallType
    last_updated: datetime
    base_path: Path
    halfstack_config: HalfstackConfig
    service_config: ServiceConfig


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
