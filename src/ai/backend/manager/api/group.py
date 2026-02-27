"""Backward-compatibility shim for the group module.

Handler logic has been migrated to:

* ``api.rest.group.handler`` — GroupHandler with constructor DI
* ``api.rest.group`` — register_routes()

This module retains ``create_app()`` so that the existing server
bootstrap (which calls ``create_app()``) continues to work.
The handler functions below delegate business logic to
:class:`~ai.backend.manager.api.rest.group.handler.GroupHandler`.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp_cors
import trafaret as t
from aiohttp import web

from ai.backend.common import validators as tx
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.group.handler import GroupHandler

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _get_handler(request: web.Request) -> GroupHandler:
    root_ctx: RootContext = request.app["_root.context"]
    return GroupHandler(
        quota_service=root_ctx.services_ctx.per_project_container_registries_quota,
    )


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
        tx.AliasedKey(["quota"]): t.Int,
    })
)
async def update_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("UPDATE_REGISTRY_QUOTA (group:{})", params["group_id"])
    handler = _get_handler(request)
    await handler.update_quota(params["group_id"], int(params["quota"]))
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
    })
)
async def delete_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("DELETE_REGISTRY_QUOTA (group:{})", params["group_id"])
    handler = _get_handler(request)
    await handler.delete_quota(params["group_id"])
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
        tx.AliasedKey(["quota"]): t.Int,
    })
)
async def create_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("CREATE_REGISTRY_QUOTA (group:{})", params["group_id"])
    handler = _get_handler(request)
    await handler.create_quota(params["group_id"], int(params["quota"]))
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
    })
)
async def read_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("READ_REGISTRY_QUOTA (group:{})", params["group_id"])
    handler = _get_handler(request)
    quota = await handler.read_quota(params["group_id"])
    return web.json_response({"result": quota})


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "group"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "/registry-quota", create_registry_quota))
    cors.add(app.router.add_route("GET", "/registry-quota", read_registry_quota))
    cors.add(app.router.add_route("PATCH", "/registry-quota", update_registry_quota))
    cors.add(app.router.add_route("DELETE", "/registry-quota", delete_registry_quota))
    return app, []
