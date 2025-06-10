from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter

from .auth import auth_required
from .manager import ALL_ALLOWED, server_status_required

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@auth_required
@server_status_required(ALL_ALLOWED)
async def list_plugins(request: web.Request) -> web.Response:
    username = request["user"]["username"]
    log.info("GET_PLUGINS (username:{})", username)

    root_ctx: RootContext = request.app["_root.context"]
    plugin_names: set[str] = set()
    all_plugins = (
        root_ctx.hook_plugin_ctx.plugins,
        root_ctx.webapp_plugin_ctx.plugins,
        root_ctx.network_plugin_ctx.plugins,
        root_ctx.event_dispatcher_plugin_ctx.plugins,
    )
    for plugins in all_plugins:
        plugin_names.update(plugins.keys())

    return web.json_response(list(plugin_names), status=HTTPStatus.OK)


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options):
    app = web.Application()
    app["prefix"] = "plugin"
    app["api_versions"] = (5,)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_plugins))
    return app, []
