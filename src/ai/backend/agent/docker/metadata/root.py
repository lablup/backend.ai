from typing import Any, Mapping, Sequence

from aiohttp import web

from ai.backend.agent.docker.kernel import DockerKernel

from .plugin import NewWebappPluginResponse, WebappPlugin, WebappPluginRoute


class ContainerMetadataPlugin(WebappPlugin):
    async def init(self, context):
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass

    async def prepare_app(self) -> NewWebappPluginResponse:
        app = web.Application()
        return NewWebappPluginResponse(app, [])

    async def routes(self) -> Sequence[WebappPluginRoute]:
        return [
            WebappPluginRoute("GET", "/envs", self.get_envs, None),
            WebappPluginRoute("GET", "/local-ipv4", self.get_local_ipv4, None),
        ]

    async def get_envs(self, request: web.Request) -> web.Response:
        kernel: DockerKernel = request["kernel"]
        if kernel is None:
            return web.Response(status=404)
        response = dict(kernel.environ)
        return web.json_response(response)

    async def get_local_ipv4(self, request: web.Request) -> web.Response:
        return web.Response(body=request["container-ip"])
