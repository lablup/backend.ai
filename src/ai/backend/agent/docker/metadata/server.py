import logging
from typing import Any, Iterable, List, Mapping, MutableMapping
from uuid import UUID

import attr
from aiodocker.docker import Docker
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.agent.docker.kernel import prepare_kernel_metadata_uri_handling
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.types import WebMiddleware
from ai.backend.agent.utils import closing_async
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin import BasePluginContext
from ai.backend.common.types import KernelId, aobject

from .plugin import MetadataPlugin
from .root import ContainerMetadataPlugin

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class MetadataPluginContext(BasePluginContext[MetadataPlugin]):
    plugin_group = "backendai_metadata_app_v20"


class BaseContext:
    pass


@attr.s(slots=True, auto_attribs=True, init=False)
class RootContext(BaseContext):
    local_config: Mapping[str, Any]
    etcd: AsyncEtcd
    metadata_plugin_ctx: MetadataPluginContext


async def on_prepare(request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


@web.middleware
async def container_resolver_middleware(
    request: web.Request, handler: Handler
) -> web.StreamResponse:
    if (
        request.headers.get("X-Forwarded-For") is not None
        and request.app["docker-mode"] == "linuxkit"
    ):
        container_ip = request.headers["X-Forwarded-For"]
    elif remote_ip := request.remote:
        container_ip = remote_ip
    else:
        return web.Response(status=403)
    async with closing_async(Docker()) as docker:
        containers = await docker.containers.list(
            filters='{"label":["ai.backend.kernel-id"],"network":["bridge"],"status":["running"]}',
        )
    target_container = list(
        filter(
            lambda x: x["NetworkSettings"]["Networks"].get("bridge", {}).get("IPAddress")
            == container_ip,
            containers,
        )
    )

    if len(target_container) == 0:
        return web.Response(status=403)
    request["container-ip"] = container_ip
    request["container"] = target_container[0]
    request["kernel"] = request.app["kernel-registry"].get(
        UUID(target_container[0]["Labels"]["ai.backend.kernel-id"])
    )
    return await handler(request)


async def list_versions(request: web.Request) -> web.Response:
    return web.Response(body="latest/")


class MetadataServer(aobject):
    app: web.Application
    runner: web.AppRunner
    route_structure: MutableMapping[str, Any]
    loaded_apps: List[str]

    def __init__(
        self,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
        kernel_registry: Mapping[KernelId, AbstractKernel],
    ) -> None:
        app = web.Application(
            middlewares=[
                container_resolver_middleware,
                self.route_structure_fallback_middleware,
            ],
        )
        app["_root.context"] = RootContext()
        app["_root.context"].local_config = local_config
        app["_root.context"].etcd = etcd
        app["kernel-registry"] = kernel_registry
        self.app = app
        self.loaded_apps = []
        self.route_structure = {"latest": {"extension": {}}}

    async def __ainit__(self):
        local_config = self.app["_root.context"].local_config
        await prepare_kernel_metadata_uri_handling(local_config)
        self.app["docker-mode"] = local_config["agent"]["docker-mode"]
        log.info("Loading metadata plugin: meta-data")
        metadata_plugin = ContainerMetadataPlugin({}, local_config)
        await metadata_plugin.init(None)
        metadata_app, global_middlewares, route_structures = await metadata_plugin.create_app()
        self._init_subapp(
            "meta-data",
            self.app,
            metadata_app,
            global_middlewares,
            route_structures,
            is_extension=False,
        )
        self.app.router.add_route("GET", "/", list_versions)
        self.app.router.add_route("GET", "/{version}", self.list_available_apps)

    async def list_available_apps(self, request: web.Request) -> web.Response:
        return web.Response(body="\n".join([x + "/" for x in self.loaded_apps]))

    @web.middleware
    async def route_structure_fallback_middleware(
        self, request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        try:
            return await handler(request)
        except web.HTTPNotFound:
            components = request.path.split("/")
            if len(components) > 0 and components[0] == "":
                components = components[1:]
            if len(components) > 0 and components[-1] == "":
                components = components[:-1]
            structure_pointer = self.route_structure
            for component in components:
                if structure_pointer.get(component) is None:
                    raise web.HTTPNotFound
                structure_pointer = structure_pointer[component]
            resources = []
            for k, v in structure_pointer.items():
                if isinstance(v, dict):
                    resources.append(k + "/")
                else:
                    resources.append(k)
            resources.sort()
            return web.Response(body="\n".join(resources))

    def _init_subapp(
        self,
        pkg_name: str,
        root_app: web.Application,
        subapp: web.Application,
        global_middlewares: Iterable[WebMiddleware],
        route_structure: Mapping[str, Any],
        is_extension: bool = True,
    ) -> None:
        subapp.on_response_prepare.append(on_prepare)

        async def _set_root_ctx(subapp: web.Application):
            # Allow subapp's access to the root app properties.
            # These are the public APIs exposed to plugins as well.
            subapp["_root.context"] = root_app["_root.context"]

        # We must copy the public interface prior to all user-defined startup signal handlers.
        subapp.on_startup.insert(0, _set_root_ctx)
        prefix = subapp.get("prefix", pkg_name.split(".")[-1].replace("_", "-"))
        if is_extension:
            self.route_structure["latest"]["extension"][prefix] = route_structure
            prefix = "extension/" + prefix
        else:
            self.route_structure["latest"][prefix] = route_structure
        root_app.add_subapp("/latest/" + prefix, subapp)
        root_app.middlewares.extend(global_middlewares)
        self.loaded_apps.append(prefix)

    async def load_metadata_plugins(self):
        root_ctx = self.app["_root.context"]
        plugin_ctx = MetadataPluginContext(root_ctx.etcd, root_ctx.local_config)
        await plugin_ctx.init()
        root_ctx.metadata_plugin_ctx = plugin_ctx
        log.debug("Available plugins: {}", plugin_ctx.plugins)
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            log.info("Loading metadata plugin: {0}", plugin_name)
            subapp, global_middlewares, route_structure = await plugin_instance.create_app()
            self._init_subapp(plugin_name, self.app, subapp, global_middlewares, route_structure)

    async def start_server(self):
        await self.load_metadata_plugins()
        metadata_server_runner = web.AppRunner(self.app)
        await metadata_server_runner.setup()
        local_config = self.app["_root.context"].local_config
        site = web.TCPSite(
            metadata_server_runner,
            local_config["agent"]["metadata-server-bind-host"],
            local_config["agent"]["metadata-server-port"],
        )
        self.runner = metadata_server_runner
        await site.start()

    async def cleanup(self):
        plugin_context = self.app["_root.context"].metadata_plugin_ctx
        await self.runner.cleanup()
        await self.app.shutdown()
        await plugin_context.cleanup()
