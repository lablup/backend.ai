import logging
from typing import Any, Mapping
from uuid import UUID
from ai.backend.common.types import KernelId

from aiodocker.docker import Docker
from aiohttp import web

from ai.backend.agent.utils import closing_async
from ai.backend.common.logging import BraceStyleAdapter

from ai.backend.agent.docker.kernel import DockerKernel

from ai.backend.agent.kernel import AbstractKernel
from aiohttp.typedefs import Handler

log = BraceStyleAdapter(logging.getLogger(__name__))


@web.middleware
async def container_resolver(request: web.Request, handler: Handler):
    if request.headers.get('X-Forwarded-For') is not None and request.app['docker-mode'] == 'linuxkit':
        container_ip = request.headers['X-Forwarded-For']
    elif remote_ip := request.remote:
        container_ip = remote_ip
    else:
        return web.Response(status=403)
    async with closing_async(Docker()) as docker:
        containers = await docker.containers.list(
            filters='{"label":["ai.backend.kernel-id"],"network":["bridge"],"status":["running"]}',
        )
    target_container = list(filter(
        lambda x: x['NetworkSettings']['Networks'].get('bridge', {}).get('IPAddress') == container_ip,
        containers,
    ))

    if len(target_container) == 0:
        return web.Response(status=403)
    request['container-ip'] = container_ip
    request['container'] = target_container[0]
    return await handler(request)


async def get_metadata(request: web.Request) -> web.Response:
    kernel: DockerKernel = \
        request.app['kernel-registry'].get(UUID(request['container']['Labels']['ai.backend.kernel-id']))
    if kernel is None:
        return web.Response(status=404)
    response = dict(kernel.environ)
    return web.json_response(response)


# TODO: Split out metadata server as seperate backend.ai plugin
async def create_server(
    local_config: Mapping[str, Any],
    kernel_registry: Mapping[KernelId, AbstractKernel],
) -> web.Application:
    app = web.Application(
        middlewares=[container_resolver],
    )
    app['docker-mode'] = local_config['agent']['docker-mode']
    app['kernel-registry'] = kernel_registry
    app.router.add_route('GET', '/meta-data', get_metadata)
    return app
