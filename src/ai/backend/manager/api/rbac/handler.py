"""
REST API handlers for RBAC system.
Provides endpoints for searching users assigned to roles.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.rbac import (
    PaginationInfo,
    SearchUsersAssignedToRoleRequest,
    SearchUsersAssignedToRoleResponse,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.rbac_request import SearchUsersAssignedToRolePathParam
from ai.backend.manager.errors.permission import InsufficientPermission
from ai.backend.manager.services.permission_contoller.actions import (
    SearchUsersAssignedToRoleAction,
)

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware
from .assigned_user_adapter import AssignedUserAdapter

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    def __init__(self) -> None:
        self.user_adapter = AssignedUserAdapter()

    # Role Assignment Endpoints

    @auth_required_for_method
    @api_handler
    async def search_users_assigned_to_role(
        self,
        path: PathParam[SearchUsersAssignedToRolePathParam],
        body: BodyParam[SearchUsersAssignedToRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search users assigned to a specific role with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise InsufficientPermission("Only superadmin can search assigned users.")

        # Build querier using adapter
        querier = self.user_adapter.build_querier(body.parsed)

        # Call service action
        action_result = (
            await processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(role_id=path.parsed.role_id, querier=querier)
            )
        )

        # Build response
        resp = SearchUsersAssignedToRoleResponse(
            users=[self.user_adapter.convert_to_dto(user) for user in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
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

    # Role assignment routes
    cors.add(
        app.router.add_route(
            "POST", "/roles/{role_id}/users/search", api_handler.search_users_assigned_to_role
        )
    )

    return app, []
