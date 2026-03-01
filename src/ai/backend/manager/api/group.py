"""Backward-compatible shim for the group module.

Registry-quota handler logic has been migrated to:

* ``api.rest.group.handler`` — GroupHandler class
* ``api.rest.group`` — route registration

This module keeps ``create_app()`` so that the existing server bootstrap
(which iterates ``global_subapp_pkgs``) continues to work.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable
from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web

from ai.backend.common.dto.manager.group.request import (
    RegistryQuotaModifyRequest,
    RegistryQuotaRequest,
)
from ai.backend.common.dto.manager.group.response import ReadRegistryQuotaResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.rbac import ProjectScope

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@server_status_required(READ_ALLOWED)
@superadmin_required
async def update_registry_quota(request: web.Request) -> web.Response:
    body = await request.json()
    params = RegistryQuotaModifyRequest.model_validate(body)
    log.info("UPDATE_REGISTRY_QUOTA (group:{})", params.group_id)
    root_ctx: RootContext = request.app["_root.context"]
    scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
    await root_ctx.services_ctx.per_project_container_registries_quota.update_quota(
        scope_id, params.quota
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def delete_registry_quota(request: web.Request) -> web.Response:
    body = await request.json()
    params = RegistryQuotaRequest.model_validate(body)
    log.info("DELETE_REGISTRY_QUOTA (group:{})", params.group_id)
    root_ctx: RootContext = request.app["_root.context"]
    scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
    await root_ctx.services_ctx.per_project_container_registries_quota.delete_quota(scope_id)
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def create_registry_quota(request: web.Request) -> web.Response:
    body = await request.json()
    params = RegistryQuotaModifyRequest.model_validate(body)
    log.info("CREATE_REGISTRY_QUOTA (group:{})", params.group_id)
    root_ctx: RootContext = request.app["_root.context"]
    scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
    await root_ctx.services_ctx.per_project_container_registries_quota.create_quota(
        scope_id, params.quota
    )
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def read_registry_quota(request: web.Request) -> web.Response:
    params = RegistryQuotaRequest.model_validate(dict(request.query))
    log.info("READ_REGISTRY_QUOTA (group:{})", params.group_id)
    root_ctx: RootContext = request.app["_root.context"]
    scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
    quota = await root_ctx.services_ctx.per_project_container_registries_quota.read_quota(
        scope_id,
    )
    resp = ReadRegistryQuotaResponse(result=quota)
    return web.json_response(resp.model_dump(mode="json"))


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
