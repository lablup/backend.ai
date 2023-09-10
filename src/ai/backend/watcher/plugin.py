from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Mapping

from aiohttp import web

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.watcher.base import BaseWatcher

from .defs import CORSOptions, WebMiddleware


class AbstractWatcherPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    def get_watcher_class(self) -> type[BaseWatcher]:
        raise NotImplementedError

    async def init(self, context: Any = None) -> None:
        return

    async def cleanup(self) -> None:
        return

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config


class WatcherPluginContext(BasePluginContext[AbstractWatcherPlugin]):
    plugin_group = "backendai_watcher_v10"


class AbstractWatcherWebAppPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, list[WebMiddleware]]:
        raise NotImplementedError

    async def init(self, context: Any = None) -> None:
        return

    async def cleanup(self) -> None:
        return

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config


class WatcherWebAppPluginContext(BasePluginContext[AbstractWatcherWebAppPlugin]):
    plugin_group = "backendai_watcher_webapp_v10"
