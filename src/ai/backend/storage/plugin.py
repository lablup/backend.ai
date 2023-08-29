from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Iterator, Optional

from aiohttp import web

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.storage.abc import AbstractVolume
from ai.backend.storage.api.types import CORSOptions, WebMiddleware


class AbstractStoragePlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    def get_volume_class(
        self,
    ) -> type[AbstractVolume]:
        raise NotImplementedError


class StoragePluginContext(BasePluginContext[AbstractStoragePlugin]):
    plugin_group = "backendai_storage_v10"

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: Optional[set[str]] = None,
        blocklist: Optional[set[str]] = None,
    ) -> Iterator[tuple[str, type[AbstractStoragePlugin]]]:
        scanned_plugins = [*super().discover_plugins(plugin_group, allowlist, blocklist)]
        yield from scanned_plugins


class StorageWebappPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, list[WebMiddleware]]:
        raise NotImplementedError


class StorageWebappPluginContext(BasePluginContext[StorageWebappPlugin]):
    plugin_group = "backendai_storage_webapp_v20"
