from typing import Iterable

import aiohttp_cors
from aiohttp import web

from ai.backend.appproxy.common.types import CORSOptions, FrontendMode, WebMiddleware

from .. import __version__
from ..types import RootContext


async def hello(request: web.Request) -> web.Response:
    """Simple health check endpoint"""
    from ai.backend.appproxy.common.types import HealthResponse

    request["do_not_print_access_log"] = True

    response = HealthResponse(
        status="healthy",
        version=__version__,
        component="appproxy-worker",
    )
    return web.json_response(response.model_dump())


async def status(request: web.Request) -> web.Response:
    """
    Returns health status of worker.
    """
    request["do_not_print_access_log"] = True

    root_ctx: RootContext = request.app["_root.context"]
    worker_config = root_ctx.local_config.proxy_worker
    if worker_config.frontend_mode == FrontendMode.WILDCARD_DOMAIN:
        available_slots = 0
    else:
        assert worker_config.port_proxy is not None
        available_slots = (
            worker_config.port_proxy.bind_port_range[1]
            - worker_config.port_proxy.bind_port_range[0]
            + 1
        )
    return web.json_response({
        "version": __version__,
        "authority": worker_config.authority,
        "app_mode": worker_config.frontend_mode,
        "protocol": worker_config.protocol,
        "occupied_slots": len(root_ctx.proxy_frontend.circuits),
        "available_slots": available_slots,
    })


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "health"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", hello))
    cors.add(add_route("GET", "/status", status))
    return app, []
