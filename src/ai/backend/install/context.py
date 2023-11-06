from __future__ import annotations

import enum
from contextvars import ContextVar
from typing import TYPE_CHECKING

from textual.widgets import RichLog

from .types import OSInfo

if TYPE_CHECKING:
    from .cli import InstallerApp

current_log: ContextVar[RichLog] = ContextVar("current_log")
current_app: ContextVar[InstallerApp] = ContextVar("current_app")
current_os: ContextVar[OSInfo] = ContextVar("current_os")


class PostGuide(enum.Enum):
    UPDATE_ETC_HOSTS = 10


class Context:
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

    async def configure_services(self) -> None:
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

    async def populate_bundled_images(self) -> None:
        pass

    async def pull_image(self) -> None:
        pass
