from __future__ import annotations

import logging
from collections.abc import Iterable
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import UUID

import aiohttp_cors
import trafaret as t
from aiohttp import web

from ai.backend.common import validators as tx
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.project_registry_quota.actions.create_project_registry_quota import (
    CreateProjectRegistryQuotaAction,
)
from ai.backend.manager.services.project_registry_quota.actions.delete_project_registry_quota import (
    DeleteProjectRegistryQuotaAction,
)
from ai.backend.manager.services.project_registry_quota.actions.read_project_registry_quota import (
    ReadProjectRegistryQuotaAction,
)
from ai.backend.manager.services.project_registry_quota.actions.update_project_registry_quota import (
    UpdateProjectRegistryQuotaAction,
)

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
        tx.AliasedKey(["quota"]): t.Int,
    })
)
async def update_project_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("UPDATE_PROJECT_REGISTRY_QUOTA (group:{})", params["group_id"])
    root_ctx: RootContext = request.app["_root.context"]
    group_id = UUID(params["group_id"])
    quota = int(params["quota"])
    action = UpdateProjectRegistryQuotaAction(project_id=group_id, quota=quota)
    await (
        root_ctx.processors.project_registry_quota.update_project_registry_quota.wait_for_complete(
            action
        )
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
    })
)
async def delete_project_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("DELETE_PROJECT_REGISTRY_QUOTA (group:{})", params["group_id"])
    root_ctx: RootContext = request.app["_root.context"]
    group_id = UUID(params["group_id"])
    action = DeleteProjectRegistryQuotaAction(project_id=group_id)
    await (
        root_ctx.processors.project_registry_quota.delete_project_registry_quota.wait_for_complete(
            action
        )
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
        tx.AliasedKey(["quota"]): t.Int,
    })
)
async def create_project_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("CREATE_PROJECT_REGISTRY_QUOTA (group:{})", params["group_id"])
    root_ctx: RootContext = request.app["_root.context"]
    group_id = UUID(params["group_id"])
    quota = int(params["quota"])
    action = CreateProjectRegistryQuotaAction(project_id=group_id, quota=quota)
    await (
        root_ctx.processors.project_registry_quota.create_project_registry_quota.wait_for_complete(
            action
        )
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["group_id", "group"]): t.String,
    })
)
async def read_project_registry_quota(request: web.Request, params: Any) -> web.Response:
    log.info("READ_PROJECT_REGISTRY_QUOTA (group:{})", params["group_id"])
    root_ctx: RootContext = request.app["_root.context"]
    group_id = UUID(params["group_id"])
    action = ReadProjectRegistryQuotaAction(project_id=group_id)
    result = await root_ctx.processors.project_registry_quota.read_project_registry_quota.wait_for_complete(
        action
    )
    return web.json_response({"result": result.quota})


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "group"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "/registry-quota", create_project_registry_quota))
    cors.add(app.router.add_route("GET", "/registry-quota", read_project_registry_quota))
    cors.add(app.router.add_route("PATCH", "/registry-quota", update_project_registry_quota))
    cors.add(app.router.add_route("DELETE", "/registry-quota", delete_project_registry_quota))
    return app, []
