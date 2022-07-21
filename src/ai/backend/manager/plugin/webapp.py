from abc import ABCMeta, abstractmethod
from typing import Sequence, Tuple

from aiohttp import web

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.manager.api.types import CORSOptions, WebMiddleware


class WebappPlugin(AbstractPlugin, metaclass=ABCMeta):
    """
    Webapp plugins should create a valid aiohttp.web.Application instance.  The returned app
    instance will be a subapp of the root app defined by the manager, and additional user-properties
    will be set as defined in ``ai.backend.gateway.server.PUBLIC_INTERFACES``.

    The init/cleanup methods of the plugin are ignored and the manager uses the standard aiohttp's
    application lifecycle handlers attached to the returned app instance.
    """

    @abstractmethod
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> Tuple[web.Application, Sequence[WebMiddleware]]:
        pass


class WebappPluginContext(BasePluginContext[WebappPlugin]):
    plugin_group = "backendai_webapp_v20"
