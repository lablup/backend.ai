from __future__ import annotations

import logging

import aiohttp_cors
from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter

from ..models.acl import get_all_permissions
from .auth import auth_required
from .manager import ALL_ALLOWED, server_status_required

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@auth_required
@server_status_required(ALL_ALLOWED)
async def get_permission(request: web.Request) -> web.Response:
    access_key = request["keypair"]["access_key"]
    log.info("GET_PERMISSION (ak:{})", access_key)

    return web.json_response(get_all_permissions(), status=200)


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options):
    app = web.Application()
    app["prefix"] = "acl"
    app["api_versions"] = (4,)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", get_permission))
    return app, []
