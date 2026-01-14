"""
REST API handlers for group (project) system.
Provides endpoints for registry quota management.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam, api_handler
from ai.backend.common.dto.manager.group import (
    RegistryQuotaReadRequest,
    RegistryQuotaReadResponse,
    RegistryQuotaRequest,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.auth import superadmin_required
from ai.backend.manager.models.rbac import ProjectScope

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("GroupAPIHandler",)


class GroupAPIHandler:
    """REST API handler class for group (project) operations."""

    @superadmin_required
    @api_handler
    async def create_registry_quota(
        self,
        request: web.Request,
        body: BodyParam[RegistryQuotaRequest],
    ) -> APIResponse:
        """Create a registry quota for a project."""
        params = body.parsed
        log.info("CREATE_REGISTRY_QUOTA (group:{})", params.group_id)
        root_ctx: RootContext = request.app["_root.context"]
        scope_id = ProjectScope(project_id=params.group_id, domain_name=None)

        await root_ctx.services_ctx.per_project_container_registries_quota.create_quota(
            scope_id, params.quota
        )
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @superadmin_required
    @api_handler
    async def read_registry_quota(
        self,
        request: web.Request,
        query: QueryParam[RegistryQuotaReadRequest],
    ) -> APIResponse:
        """Read a registry quota for a project."""
        params = query.parsed
        log.info("READ_REGISTRY_QUOTA (group:{})", params.group_id)
        root_ctx: RootContext = request.app["_root.context"]
        scope_id = ProjectScope(project_id=params.group_id, domain_name=None)

        quota = await root_ctx.services_ctx.per_project_container_registries_quota.read_quota(
            scope_id,
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=RegistryQuotaReadResponse(result=quota),
        )

    @superadmin_required
    @api_handler
    async def update_registry_quota(
        self,
        request: web.Request,
        body: BodyParam[RegistryQuotaRequest],
    ) -> APIResponse:
        """Update a registry quota for a project."""
        params = body.parsed
        log.info("UPDATE_REGISTRY_QUOTA (group:{})", params.group_id)
        root_ctx: RootContext = request.app["_root.context"]
        scope_id = ProjectScope(project_id=params.group_id, domain_name=None)

        await root_ctx.services_ctx.per_project_container_registries_quota.update_quota(
            scope_id, params.quota
        )
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @superadmin_required
    @api_handler
    async def delete_registry_quota(
        self,
        request: web.Request,
        body: BodyParam[RegistryQuotaReadRequest],
    ) -> APIResponse:
        """Delete a registry quota for a project."""
        params = body.parsed
        log.info("DELETE_REGISTRY_QUOTA (group:{})", params.group_id)
        root_ctx: RootContext = request.app["_root.context"]
        scope_id = ProjectScope(project_id=params.group_id, domain_name=None)

        await root_ctx.services_ctx.per_project_container_registries_quota.delete_quota(scope_id)
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)
