from __future__ import annotations

import enum
import os
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widgets import RichLog

from ai.backend.install.utils import request

from . import __version__
from .common import detect_os
from .dev import (
    bootstrap_pants,
    install_editable_webui,
    install_git_hooks,
    install_git_lfs,
    pants_export,
)
from .docker import check_docker, check_docker_desktop_mount, get_preferred_pants_local_exec_root
from .python import check_python
from .types import OSInfo

if TYPE_CHECKING:
    from .cli import InstallerApp

current_log: ContextVar[RichLog] = ContextVar("current_log")
current_app: ContextVar[InstallerApp] = ContextVar("current_app")


class PostGuide(enum.Enum):
    UPDATE_ETC_HOSTS = 10


class Context:
    os_info: OSInfo

    _post_guides: list[PostGuide]

    def __init__(self) -> None:
        self._post_guides = []
        self.log = current_log.get()
        self.cwd = os.getcwd()

    def add_post_guide(self, guide: PostGuide) -> None:
        self._post_guides.append(guide)

    def show_post_guide(self) -> None:
        pass

    async def install_system_package(self, name: dict[str, list[str]]) -> None:
        distro_pkg_name = name[self.os_info.distro]
        match self.os_info.distro:
            case "Debian":
                f"""
                $sudo apt-get install -y {distro_pkg_name}
                """
            case "RedHat":
                f"""
                $sudo yum install -y {distro_pkg_name}
                """
            case "SUSE":
                f"""
                $sudo zypper install -y {distro_pkg_name}
                """
            case "Darwin":
                f"""
                brew install {distro_pkg_name}
                """

    async def run_shell(self, script: str) -> None:
        # TODO: execute the given script as a subprocess
        # TODO: stream the output to self.log & BytesIO
        # TODO: if the command fails and the installer exits, show the output as the exit message
        pass

    async def install_halfstack(self, ha_setup: bool) -> None:
        pass

    async def load_fixtures(self) -> None:
        pass

    async def configure_manager(self) -> None:
        pass

    async def configure_agent(self) -> None:
        pass

    async def configure_storage_proxy(self) -> None:
        pass

    async def configure_webserver(self) -> None:
        pass

    async def configure_webui(self) -> None:
        pass

    async def dump_etcd_config(self) -> None:
        pass

    async def populate_images(self) -> None:
        pass


class DevContext(Context):
    async def check_prerequisites(self) -> None:
        self.os_info = await detect_os(self)
        await install_git_lfs(self)
        await install_git_hooks(self)
        await check_python(self)
        await check_docker(self)
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount(self)
        local_execution_root_dir = await get_preferred_pants_local_exec_root(self)
        await bootstrap_pants(self, local_execution_root_dir)

    async def install(self) -> None:
        await pants_export(self)
        await install_editable_webui(self)

    async def configure(self) -> None:
        await self.configure_manager()
        await self.configure_agent()
        await self.configure_storage_proxy()
        await self.configure_webserver()
        await self.configure_webui()

    async def populate_images(self) -> None:
        # TODO: docker pull
        pass


class PackageContext(Context):
    async def check_prerequisites(self) -> None:
        self.os_info = await detect_os(self)
        await check_docker(self)
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount(self)

    def _mangle_pkgname(self, name: str) -> str:
        return f"backendai-{name}-{self.os_info.platform}"

    async def _fetch_package(self, name: str) -> None:
        url = f"https://github.com/lablup/backend.ai/releases/download/{self.pkg_version}/{self._mangle_pkgname(name)}"
        csum_url = url + ".sha256"
        self.log.write(f"Downloading {url}...")
        # TODO: wget...
        self.log.write(f"Verifying {url}...")
        async with request("GET", csum_url) as r:
            csum = (await r.text()).strip()
        # TODO: verify checksum

    async def _verify_package(self, name: str) -> None:
        path = f"./{self._mangle_pkgname(name)}"
        self.log.write(f"Verifying {path}...")
        csum_path = path + ".sha256"
        csum = Path(csum_path).read_text().strip()
        # TODO: verify checksum

    async def install(self) -> None:
        try:
            self.pkg_version = Path("DIST-INFO").read_text()
            # use the local files
            await self._verify_package("manager")
            await self._verify_package("agent")
            await self._verify_package("agent-watcher")
            # replace above with await self._verify_package("watcher")
            await self._verify_package("client")
            await self._verify_package("webserver")
        except FileNotFoundError:
            self.pkg_version = __version__
            # download
            await self._fetch_package("manager")
            await self._fetch_package("agent")
            await self._fetch_package("agent-watcher")
            # replace above with await self._fetch_package("watcher")
            await self._fetch_package("client")
            await self._fetch_package("webserver")
            # TODO: await self._fetch_package("static wsproxy")

    async def configure(self) -> None:
        await self.configure_manager()
        await self.configure_agent()
        await self.configure_storage_proxy()
        await self.configure_webserver()
        await self.configure_webui()
        # TODO: install as systemd services?

    async def populate_images(self) -> None:
        # TODO: docker load
        pass
