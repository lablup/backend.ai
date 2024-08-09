from __future__ import annotations

import dataclasses
import enum
from datetime import datetime
from pathlib import Path
from typing import cast

from pydantic import BaseModel, Field
from rich.console import ConsoleRenderable, RichCast
from rich.text import Text

from ai.backend.common.types import HostPortPair

from . import __version__


class InstallModes(enum.StrEnum):
    DEVELOP = "DEVELOP"
    PACKAGE = "PACKAGE"
    MAINTAIN = "MAINTAIN"
    CONFIGURE = "CONFIGURE"


class PackageSource(enum.StrEnum):
    GITHUB_RELEASE = "github-release"
    LOCAL_DIR = "local-dir"


class ImageSource(enum.StrEnum):
    BACKENDAI_REGISTRY = "cr.backend.ai"
    DOCKER_HUB = "index.docker.io"
    LOCAL_REGISTRY = "local-registry"  # not implemented yet
    LOCAL_DIR = "local-dir"


class InstallType(enum.StrEnum):
    SOURCE = "source"
    PACKAGE = "package"


class Platform(enum.StrEnum):
    LINUX_ARM64 = "linux-aarch64"
    LINUX_X86_64 = "linux-x86_64"
    MACOS_ARM64 = "macos-aarch64"
    MACOS_X86_64 = "macos-x86_64"


@dataclasses.dataclass()
class CliArgs:
    mode: InstallModes | None
    target_path: str
    show_guide: bool
    non_interactive: bool
    public_facing_address: str


class PrerequisiteError(RichCast, Exception):
    def __init__(self, msg: str, *, instruction: str | None = None) -> None:
        super().__init__(msg, instruction)
        self.msg = msg
        self.instruction = instruction

    def __rich__(self) -> ConsoleRenderable:
        text = f"[bold red]:warning: [bold white]{self.msg}[/]"
        if self.instruction:
            text += f"\n:hammer: [bright_cyan]{self.instruction}[/]"
        return Text.from_markup(text)


class LocalImageSource(BaseModel):
    ref: str
    file: Path


class DistInfo(BaseModel):
    version: str = __version__
    package_source: PackageSource = PackageSource.GITHUB_RELEASE
    package_dir: Path = Field(default_factory=Path.cwd)
    use_fat_binary: bool = False
    target_path: Path = Field(default_factory=lambda: Path.home() / "backendai")
    image_sources: list[ImageSource] = [ImageSource.BACKENDAI_REGISTRY, ImageSource.DOCKER_HUB]
    image_payloads: list[LocalImageSource] = Field(default_factory=list)
    image_refs: list[str] = Field(default_factory=list)


class InstallInfo(BaseModel):
    version: str
    type: InstallType
    last_updated: datetime
    base_path: Path
    halfstack_config: HalfstackConfig
    service_config: ServiceConfig


@dataclasses.dataclass()
class OSInfo(RichCast):
    platform: Platform
    distro: str
    distro_variants: set[str]

    def __rich__(self) -> ConsoleRenderable:
        variants = [self.distro, *sorted(self.distro_variants)]
        variant = ", ".join(variants)
        return Text.from_markup(f"[bold cyan]{self.platform} [not bold](variant: {variant})[/]")


@dataclasses.dataclass()
class ServerAddr:
    bind: HostPortPair  # the server-bind address (e.g., 0.0.0.0:8080)
    face: HostPortPair = cast(HostPortPair, None)  # the client-facing address (e.g., 10.1.2.3:9090)

    def __post_init__(self) -> None:
        # Ensure that face is always initialized, while its unspecified value is None.
        if self.face is None:
            if self.bind.host == "0.0.0.0" or self.bind.host == "::":
                raise ValueError(
                    f"Cannot use the server-bind address {self.bind.host!r} as the client-facing "
                    "address. In such cases, you must specify a concrete client-facing address."
                )
            self.face = self.bind


@dataclasses.dataclass()
class HalfstackConfig:
    ha_setup: bool
    postgres_addr: ServerAddr
    postgres_user: str
    postgres_password: str
    redis_addr: ServerAddr | None
    redis_sentinel_addrs: list[HostPortPair] | None
    redis_password: str | None
    etcd_addr: list[ServerAddr]  # multiple if HA
    etcd_user: str | None
    etcd_password: str | None


@dataclasses.dataclass()
class ServiceConfig:
    manager_addr: ServerAddr
    manager_ipc_base_path: str
    manager_var_base_path: str
    webserver_addr: ServerAddr
    webserver_ipc_base_path: str
    webserver_var_base_path: str
    webui_menu_blocklist: list[str]
    webui_menu_inactivelist: list[str]
    local_proxy_addr: ServerAddr
    agent_rpc_addr: ServerAddr
    agent_watcher_addr: ServerAddr
    agent_ipc_base_path: str
    agent_var_base_path: str
    storage_proxy_manager_facing_addr: ServerAddr
    storage_proxy_client_facing_addr: ServerAddr
    storage_proxy_ipc_base_path: str
    storage_proxy_var_base_path: str
    storage_proxy_manager_auth_key: str
    storage_proxy_random: str
    storage_agent_rpc_addr: ServerAddr
    storage_agent_ipc_base_path: str
    storage_agent_var_base_path: str
    storage_watcher_addr: ServerAddr
    vfolder_relpath: str
    wsproxy_hash_key: str
    wsproxy_jwt_key: str
    wsproxy_api_token: str


@dataclasses.dataclass
class InstallVariable:
    public_facing_address: str = "127.0.0.1"
