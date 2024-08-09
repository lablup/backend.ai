from abc import ABCMeta, abstractmethod

from aiohttp import web

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext

from .types import CORSOptions, WebMiddleware


class WebappPlugin(AbstractPlugin, metaclass=ABCMeta):
    """
    Webapp plugins should create a valid aiohttp.web.Application instance. The returned app
    instance will be a subapp of the root app defined by the account manager.

    The init/cleanup methods of the plugin are ignored and the account manager uses the standard aiohttp's
    application lifecycle handlers attached to the returned app instance.
    """

    @abstractmethod
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, list[WebMiddleware]]:
        pass


class WebappPluginContext(BasePluginContext[WebappPlugin]):
    plugin_group = "backendai_webapp_v20"
