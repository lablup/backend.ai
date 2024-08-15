import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Coroutine, Mapping, MutableMapping, NamedTuple, Optional, Sequence

from aiohttp import web

from ai.backend.agent.types import WebMiddleware
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin import AbstractPlugin

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

NewMetadataPluginResponse = NamedTuple(
    "NewMetadataPluginResponse",
    [("app", web.Application), ("global_middlewares", Sequence[WebMiddleware])],
)
InitMetadataPluginResponse = NamedTuple(
    "InitMetadataPluginResponse",
    [
        ("app", web.Application),
        ("global_middlewares", Sequence[WebMiddleware]),
        ("structure", Mapping[str, Any]),
    ],
)
MetadataPluginRoute = NamedTuple(
    "MetadataPluginRoute",
    [
        ("method", str),
        ("route", str),
        ("route_handler", Callable[[web.Request], Coroutine[Any, Any, web.Response]]),
        ("route_name", Optional[str]),
    ],
)


class MetadataPlugin(AbstractPlugin, metaclass=ABCMeta):
    """
    Metadata plugins should create a valid aiohttp.web.Application instance.  The returned app
    instance will be a subapp of the root app defined by the manager, and additional user-properties
    will be set as defined in ``ai.backend.gateway.server.PUBLIC_INTERFACES``.

    The init/cleanup methods of the plugin are ignored and the manager uses the standard aiohttp's
    application lifecycle handlers attached to the returned app instance.
    """

    route_prefix: Optional[str]

    @abstractmethod
    async def prepare_app(self) -> NewMetadataPluginResponse:
        pass

    @abstractmethod
    async def routes(self) -> Sequence[MetadataPluginRoute]:
        pass

    async def create_app(self) -> InitMetadataPluginResponse:
        app, global_middlewares = await self.prepare_app()
        routes = await self.routes()

        # Parse registered webapp's hierarchy to show it to user later
        # e.g. structure with four routes
        # (GET /hello, GET /hello/world, GET /hello/bar, POST /foo)
        # will be:
        # {
        #     '/hello': {
        #         '_': (/hello's handler),
        #         '/world': (/hello/world's handler),
        #         '/bar': (/hello/bar's handler),
        #     }
        #     '/foo': (/foo's handler)
        # }
        # Note that route defined /hello will automatically converted to /hello/_
        # upon actual webapp creation.
        structure: MutableMapping[str, Any] = {}

        for route in routes:
            method, path, handler, name = route

            # This variable will work as a 'traversal pointer' when creating structure object.
            # See for loop below for usage.
            structure_pointer = structure
            _path = path
            if not _path.startswith("/"):
                _path = "/" + _path

            raw_splitted = _path.split("/")
            splitted = []

            chunks = []
            for i in range(len(raw_splitted)):
                s = raw_splitted[i]
                chunks.append(s)
                if not (s.startswith("{") and s.endswith("}")):
                    splitted.append("/".join(chunks))
                    chunks = []

            if len(chunks) > 0:
                splitted.append("/".join(chunks))

            # e.g. if route is /a/b/c/d:
            # components will be ['a', 'b', 'c']
            # resource_name will be 'd'
            components, resource_name = splitted[1:-1], splitted[-1]

            # traverse into subroute
            for component in components:
                if structure_pointer.get(component) is None:
                    structure_pointer[component] = {}
                elif not isinstance(structure_pointer.get(component), dict):
                    structure_pointer[component] = {"_": structure_pointer[component]}
                structure_pointer = structure_pointer[component]

            if isinstance(structure_pointer.get(resource_name), dict):
                structure_pointer[resource_name]["_"] = resource_name
                app.router.add_route(method, path + "/_", handler, name=name)
            else:
                structure_pointer[resource_name] = resource_name
                app.router.add_route(method, path, handler, name=name)
        return InitMetadataPluginResponse(app, global_middlewares, structure)
