"""Backward-compatibility shim for the resource module.

Handler logic has been migrated to ``api.rest.resource.handler.ResourceHandler``.
This module keeps ``create_app()`` functional so that ``server.py`` can still
load it as a legacy subapp.  ``get_watcher_info()`` is preserved as a utility
used by the vfolder module.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import aiohttp_cors
import yarl
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.resource.handler import ResourceHandler
from ai.backend.manager.api.rest.routing import _wrap_api_handler

from .auth import auth_required, superadmin_required
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware, WebRequestHandler

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# ------------------------------------------------------------------
# Utility kept for vfolder module
# ------------------------------------------------------------------


async def get_watcher_info(request: web.Request, agent_id: str) -> dict[str, Any]:
    """
    Get watcher information.

    :return addr: address of agent watcher (eg: http://127.0.0.1:6009)
    :return token: agent watcher token ("insecure" if not set in config server)
    """
    root_ctx: RootContext = request.app["_root.context"]
    token = root_ctx.config_provider.config.watcher.token
    if token is None:
        token = "insecure"
    agent_ip = await root_ctx.etcd.get(f"nodes/agents/{agent_id}/ip")
    raw_watcher_port = await root_ctx.etcd.get(
        f"nodes/agents/{agent_id}/watcher_port",
    )
    watcher_port = 6099 if raw_watcher_port is None else int(raw_watcher_port)
    addr = yarl.URL(f"http://{agent_ip}:{watcher_port}")
    return {
        "addr": addr,
        "token": token,
    }


# ------------------------------------------------------------------
# Lazy handler initialization helpers
# ------------------------------------------------------------------

_HANDLER_APP_KEY = "_resource_handler_wrapped"


def _ensure_handler(app: web.Application) -> dict[str, WebRequestHandler]:
    """Lazily create ResourceHandler and wrap its methods on first request."""
    if _HANDLER_APP_KEY not in app:
        root_ctx: RootContext = app["_root.context"]
        handler = ResourceHandler(processors=root_ctx.processors)
        app[_HANDLER_APP_KEY] = {
            name: _wrap_api_handler(getattr(handler, name))
            for name in (
                "list_presets",
                "check_presets",
                "recalculate_usage",
                "usage_per_month",
                "usage_per_period",
                "user_month_stats",
                "admin_month_stats",
                "get_watcher_status",
                "watcher_agent_start",
                "watcher_agent_stop",
                "watcher_agent_restart",
                "get_container_registries",
            )
        }
    result: dict[str, WebRequestHandler] = app[_HANDLER_APP_KEY]
    return result


def _delegate(method_name: str) -> WebRequestHandler:
    """Return a handler function that delegates to the new-style ResourceHandler."""

    async def _handler(request: web.Request) -> web.StreamResponse:
        wrapped = _ensure_handler(request.app)
        return await wrapped[method_name](request)

    _handler.__name__ = method_name
    _handler.__qualname__ = f"resource._delegate.<{method_name}>"
    return _handler


# ------------------------------------------------------------------
# Legacy create_app() entry point
# ------------------------------------------------------------------


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4,)
    app["prefix"] = "resource"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route("GET", "/presets", auth_required(_delegate("list_presets"))))
    cors.add(
        add_route(
            "GET",
            "/container-registries",
            superadmin_required(_delegate("get_container_registries")),
        )
    )
    cors.add(
        add_route(
            "POST",
            "/check-presets",
            server_status_required(READ_ALLOWED)(auth_required(_delegate("check_presets"))),
        )
    )
    cors.add(
        add_route(
            "POST",
            "/recalculate-usage",
            server_status_required(READ_ALLOWED)(
                superadmin_required(_delegate("recalculate_usage"))
            ),
        )
    )
    cors.add(
        add_route(
            "GET",
            "/usage/month",
            server_status_required(READ_ALLOWED)(superadmin_required(_delegate("usage_per_month"))),
        )
    )
    cors.add(
        add_route(
            "GET",
            "/usage/period",
            server_status_required(READ_ALLOWED)(
                superadmin_required(_delegate("usage_per_period"))
            ),
        )
    )
    cors.add(
        add_route(
            "GET",
            "/stats/user/month",
            server_status_required(READ_ALLOWED)(auth_required(_delegate("user_month_stats"))),
        )
    )
    cors.add(
        add_route(
            "GET",
            "/stats/admin/month",
            server_status_required(READ_ALLOWED)(
                superadmin_required(_delegate("admin_month_stats"))
            ),
        )
    )
    cors.add(
        add_route(
            "GET",
            "/watcher",
            server_status_required(READ_ALLOWED)(
                superadmin_required(_delegate("get_watcher_status"))
            ),
        )
    )
    cors.add(
        add_route(
            "POST",
            "/watcher/agent/start",
            server_status_required(READ_ALLOWED)(
                superadmin_required(_delegate("watcher_agent_start"))
            ),
        )
    )
    cors.add(
        add_route(
            "POST",
            "/watcher/agent/stop",
            server_status_required(READ_ALLOWED)(
                superadmin_required(_delegate("watcher_agent_stop"))
            ),
        )
    )
    cors.add(
        add_route(
            "POST",
            "/watcher/agent/restart",
            server_status_required(READ_ALLOWED)(
                superadmin_required(_delegate("watcher_agent_restart"))
            ),
        )
    )
    return app, []
