from typing import Any, Mapping, Sequence

from aiohttp import web

from ai.backend.agent.docker.kernel import DockerKernel

from .plugin import MetadataPlugin, MetadataPluginRoute, NewMetadataPluginResponse


class ContainerMetadataPlugin(MetadataPlugin):
    async def init(self, context):
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass

    async def prepare_app(self) -> NewMetadataPluginResponse:
        app = web.Application()
        return NewMetadataPluginResponse(app, [])

    async def routes(self) -> Sequence[MetadataPluginRoute]:
        return [
            MetadataPluginRoute("GET", "/envs", self.get_envs, None),
            MetadataPluginRoute("GET", "/sandbox", self.get_sandbox_type, None),
            MetadataPluginRoute("GET", "/local-ipv4", self.get_local_ipv4, None),
        ]

    async def get_envs(self, request: web.Request) -> web.Response:
        kernel: DockerKernel = request["kernel"]
        if kernel is None:
            return web.Response(status=404)
        response = dict(kernel.environ)
        return web.json_response(response)

    async def get_local_ipv4(self, request: web.Request) -> web.Response:
        return web.Response(body=request["container-ip"])

    async def get_sandbox_type(self, request: web.Request) -> web.Response:
        return web.Response(body=self.local_config["container"]["sandbox-type"])
