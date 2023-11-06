from __future__ import annotations

import enum
from contextvars import ContextVar
from typing import TYPE_CHECKING

from textual.widgets import RichLog

from .common import detect_os
from .dev import bootstrap_pants, install_editable_webui, install_git_hooks, install_git_lfs
from .docker import check_docker, check_docker_desktop_mount, get_preferred_pants_local_exec_root
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

    def add_post_guide(self, guide: PostGuide) -> None:
        self._post_guides.append(guide)

    def show_post_guide(self) -> None:
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
        self.os_info = await detect_os()
        await install_git_lfs()
        await install_git_hooks()
        await check_docker()
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount()
        local_execution_root_dir = await get_preferred_pants_local_exec_root()
        await bootstrap_pants(local_execution_root_dir)

    async def install(self) -> None:
        await install_editable_webui()
        # TODO: install agent-watcher
        # TODO: install storage-agent
        # TODO: install storage-watcher
        # TODO: install webserver

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
        self.os_info = await detect_os()
        await check_docker()
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount()

    async def install(self) -> None:
        pass
        # TODO: install agent-watcher
        # TODO: install storage-agent
        # TODO: install storage-watcher
        # TODO: install webserver
        # TODO: install static wsproxy

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
