from __future__ import annotations

from abc import ABCMeta, abstractmethod

from aiohttp import web

from ai.backend.common.plugin import AbstractPlugin, AbstractWebappPlugin, BasePluginContext

from .base import BaseWatcher, BaseWatcherConfig
from .defs import CORSOptions, WebMiddleware


class AbstractWatcherPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    def get_watcher_class(self) -> tuple[type[BaseWatcher], type[BaseWatcherConfig]]:
        raise NotImplementedError


class WatcherPluginContext(BasePluginContext[AbstractWatcherPlugin]):
    plugin_group = "backendai_watcher_v10"


class AbstractWatcherWebAppPlugin(AbstractWebappPlugin, metaclass=ABCMeta):
    app_path = "ai.backend.watcher_modules"
    route_prefix = "watcher"

    @abstractmethod
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, list[WebMiddleware]]:
        raise NotImplementedError


class WatcherWebAppPluginContext(BasePluginContext[AbstractWatcherWebAppPlugin]):
    plugin_group = "backendai_watcher_webapp_v10"
