from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.appproxy.common.types import CORSOptions, FrontendServerMode, WebMiddleware
from ai.backend.appproxy.worker import __version__
from ai.backend.appproxy.worker.errors import MissingPortProxyConfigError
from ai.backend.appproxy.worker.types import RootContext
from ai.backend.common.dto.internal.health import (
    ConnectivityCheckResponse,
    HealthResponse,
    HealthStatus,
)


def _build_worker_health_response(connectivity: ConnectivityCheckResponse) -> web.Response:
    """Detail /health — always 200; informational tier failures reported as
    DEGRADED in the body but not surfaced via HTTP status."""
    response = HealthResponse(
        status=HealthStatus.OK if connectivity.overall_healthy else HealthStatus.DEGRADED,
        version=__version__,
        component="appproxy-worker",
        connectivity=connectivity,
    )
    return web.json_response(response.model_dump_json())


def _build_worker_probe_response(connectivity: ConnectivityCheckResponse) -> web.Response:
    """/livez, /readyz — 503 when any gating check fails so K8s probes trip."""
    is_healthy = connectivity.overall_healthy
    response = HealthResponse(
        status=HealthStatus.OK if is_healthy else HealthStatus.ERROR,
        version=__version__,
        component="appproxy-worker",
        connectivity=connectivity,
    )
    return web.json_response(
        response.model_dump(mode="json"),
        status=HTTPStatus.OK if is_healthy else HTTPStatus.SERVICE_UNAVAILABLE,
    )


async def hello(request: web.Request) -> web.Response:
    """Aggregated health (union of liveness and readiness)."""
    request["do_not_print_access_log"] = True
    root_ctx: RootContext = request.app["_root.context"]
    connectivity = await root_ctx.health_probe.get_connectivity_status()
    return _build_worker_health_response(connectivity)


async def livez(request: web.Request) -> web.Response:
    """Liveness probe — only liveness-registered checkers."""
    request["do_not_print_access_log"] = True
    root_ctx: RootContext = request.app["_root.context"]
    connectivity = await root_ctx.health_probe.get_liveness_status()
    return _build_worker_probe_response(connectivity)


async def readyz(request: web.Request) -> web.Response:
    """Readiness probe — only readiness-registered checkers."""
    request["do_not_print_access_log"] = True
    root_ctx: RootContext = request.app["_root.context"]
    connectivity = await root_ctx.health_probe.get_readiness_status()
    return _build_worker_probe_response(connectivity)


async def status(request: web.Request) -> web.Response:
    """
    Returns health status of worker.
    """
    request["do_not_print_access_log"] = True

    root_ctx: RootContext = request.app["_root.context"]
    worker_config = root_ctx.local_config.proxy_worker
    if worker_config.frontend_mode == FrontendServerMode.WILDCARD_DOMAIN:
        available_slots = 0
    else:
        if worker_config.port_proxy is None:
            raise MissingPortProxyConfigError("Port proxy configuration is required for PORT mode")
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


async def init(_app: web.Application) -> None:
    pass


async def shutdown(_app: web.Application) -> None:
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
    cors.add(add_route("GET", "/livez", livez))
    cors.add(add_route("GET", "/readyz", readyz))
    cors.add(add_route("GET", "/status", status))
    return app, []
