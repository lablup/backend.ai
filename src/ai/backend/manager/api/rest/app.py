from __future__ import annotations

import asyncio
import importlib.resources
import logging
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import aiohttp_cors
from aiohttp import web

from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager import __version__
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.errors.common import (
    GenericBadRequest,
    InternalServerError,
    ServerMisconfiguredError,
)

from .middleware import build_api_metric_middleware, request_id_middleware
from .routing import RouteRegistry

if TYPE_CHECKING:
    from .types import CORSOptions, WebRequestHandler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

VALID_VERSIONS: Final = frozenset([
    "v4.20181215",
    "v4.20190115",
    "v4.20190315",
    "v4.20190615",
    "v5.20191215",
    "v6.20200815",
    "v6.20220315",
    "v6.20220615",
    "v6.20221201",
    "v6.20230315",
    "v7.20230615",
    "v8.20240315",
    "v8.20240915",
    "v9.20250722",
])
LATEST_REV_DATES: Final = {
    1: "20160915",
    2: "20170915",
    3: "20181215",
    4: "20190615",
    5: "20191215",
    6: "20230315",
    7: "20230615",
    8: "20240915",
    9: "20250722",
}
LATEST_API_VERSION: Final = (
    f"v{max(LATEST_REV_DATES.keys())}.{LATEST_REV_DATES[max(LATEST_REV_DATES.keys())]}"
)


async def hello(_request: web.Request) -> web.Response:
    """
    Returns the API version number.
    """
    return web.json_response({
        "version": LATEST_API_VERSION,
        "manager": __version__,
    })


async def on_prepare(_request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


@web.middleware
async def api_middleware(request: web.Request, handler: WebRequestHandler) -> web.StreamResponse:
    _handler = handler
    method_override = request.headers.get("X-Method-Override", None)
    if method_override:
        request = request.clone(method=method_override)
        new_match_info = await request.app.router.resolve(request)
        if new_match_info is None:
            raise InternalServerError("No matching method handler found")
        _handler = new_match_info.handler
        request._match_info = new_match_info
    ex = request.match_info.http_exception
    if ex is not None:
        raise ex
    new_api_version = request.headers.get("X-BackendAI-Version")
    legacy_api_version = request.headers.get("X-Sorna-Version")
    api_version = new_api_version or legacy_api_version
    try:
        if api_version is None:
            path_major_version = int(request.match_info.get("version", 5))
            revision_date = LATEST_REV_DATES[path_major_version]
            request["api_version"] = (path_major_version, revision_date)
        elif api_version in VALID_VERSIONS:
            hdr_major_version, revision_date = api_version.split(".", maxsplit=1)
            request["api_version"] = (int(hdr_major_version[1:]), revision_date)
        else:
            return GenericBadRequest("Unsupported API version.")
    except (ValueError, KeyError):
        return GenericBadRequest("Unsupported API version.")
    return await _handler(request)


def _mount_registry_tree(
    root_app: web.Application,
    root_registry: RouteRegistry,
    pidx: int = 0,
) -> None:
    """Flatten the registry tree and mount all subapps on *root_app*."""

    async def _bridge_root_app(subapp: web.Application) -> None:
        subapp["_root_app"] = root_app

    for prefix, app, _reg in root_registry.collect_apps():
        if pidx == 0:
            log.info("Loading module: {}", prefix)
        app["_registry_prefix"] = prefix
        app.on_startup.insert(0, _bridge_root_app)
        root_app.add_subapp("/" + prefix, app)


def mount_registries(
    root_app: web.Application,
    registries: Sequence[RouteRegistry],
    *,
    cors_options: CORSOptions | None = None,
) -> None:
    """Mount pre-built registries on *root_app*.

    Public API used by ``tests/component/conftest.py`` to mount only
    the modules needed for a particular test.
    """
    root_registry = RouteRegistry.create("", cors_options or {})
    for reg in registries:
        root_registry.add_subregistry(reg)
    _mount_registry_tree(root_app, root_registry)

    # Install ratelimit middleware on root app if the module is present
    rlim_reg = root_registry.find_subregistry("ratelimit")
    if rlim_reg is not None and rlim_reg.rlim_middleware is not None:
        root_app.middlewares.append(rlim_reg.rlim_middleware)


def build_root_app(
    pidx: int,
    bootstrap_config: BootstrapConfig,
    *,
    scheduler_opts: Mapping[str, Any] | None = None,
    loop_error_handler: Callable[..., Any] | None = None,
) -> web.Application:
    if bootstrap_config.pyroscope.enabled:
        if (
            not bootstrap_config.pyroscope.app_name
            or not bootstrap_config.pyroscope.server_addr
            or not bootstrap_config.pyroscope.sample_rate
        ):
            raise ValueError("Pyroscope configuration is incomplete.")

        Profiler(
            pyroscope_args=PyroscopeArgs(
                enabled=bootstrap_config.pyroscope.enabled,
                application_name=bootstrap_config.pyroscope.app_name,
                server_address=bootstrap_config.pyroscope.server_addr,
                sample_rate=bootstrap_config.pyroscope.sample_rate,
            )
        )

    metrics = CommonMetricRegistry.instance()
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(  # type: ignore[no-untyped-call]
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }
    app = web.Application(
        middlewares=[
            request_id_middleware,
            # exception_middleware and auth_middleware are inserted later
            # in server_main() after dependencies are available.
            api_middleware,
            build_api_metric_middleware(metrics.api),
        ]
    )
    if loop_error_handler is not None:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(loop_error_handler)
    global_exception_handler = loop_error_handler

    # If the request path starts with the following route, the auth_middleware is bypassed.
    # In this case, all authentication flags are turned off.
    # Used in special cases where the request headers cannot be modified.
    app["auth_middleware_allowlist"] = [
        "/container-registries/webhook",
    ]

    app["_pidx"] = pidx
    app["_cors_options"] = cors_options
    app["_metrics"] = metrics
    default_scheduler_opts = {
        "limit": 2048,
        "close_timeout": 30,
        "exception_handler": global_exception_handler,
        "agent_selection_strategy": AgentSelectionStrategy.DISPERSED,
    }
    app["scheduler_opts"] = {
        **default_scheduler_opts,
        **(scheduler_opts if scheduler_opts is not None else {}),
    }
    app.on_response_prepare.append(on_prepare)

    cors = aiohttp_cors.setup(app, defaults=cors_options)
    # should be done in create_app() in other modules.
    cors.add(app.router.add_route("GET", r"", hello))
    cors.add(app.router.add_route("GET", r"/", hello))

    vendor_path = importlib.resources.files("ai.backend.manager.vendor")
    if not isinstance(vendor_path, Path):
        raise ServerMisconfiguredError("vendor_path must be a Path instance")
    app.router.add_static("/static/vendor", path=vendor_path, name="static")
    return app
