"""
REST API handlers for RBAC system.
Provides CRUD endpoints for roles and user assignments.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.rbac import (
    GetRoleResponse,
    PaginationInfo,
    SearchRolesRequest,
    SearchRolesResponse,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.rbac_request import GetRolePathParam
from ai.backend.manager.errors.permission import InsufficientPermission
from ai.backend.manager.services.permission_contoller.actions import (
    GetRoleDetailAction,
    SearchRolesAction,
)

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware
from .role_adapter import RoleAdapter

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    def __init__(self) -> None:
        self.role_adapter = RoleAdapter()

    # Role CRUD Endpoints

    @auth_required_for_method
    @api_handler
    async def search_roles(
        self,
        body: BodyParam[SearchRolesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search roles with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise InsufficientPermission("Only superadmin can search roles.")

        # Build querier using adapter
        querier = self.role_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await processors.permission_controller.search_roles.wait_for_complete(
            SearchRolesAction(querier=querier)
        )

        # Build response
        resp = SearchRolesResponse(
            roles=[self.role_adapter.convert_to_dto(role) for role in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_role(
        self,
        path: PathParam[GetRolePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific role."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise InsufficientPermission("Only superadmin can get roles.")

        action_result = await processors.permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=path.parsed.role_id)
        )
        role_data = action_result.role

        # Build response
        resp = GetRoleResponse(role=self.role_adapter.convert_to_dto(role_data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for RBAC API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "rbac"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = RBACAPIHandler()

    # Role routes
    cors.add(app.router.add_route("POST", "/roles/search", api_handler.search_roles))
    cors.add(app.router.add_route("GET", "/roles/{role_id}", api_handler.get_role))

    return app, []
