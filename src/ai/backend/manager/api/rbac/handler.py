"""
REST API handlers for RBAC system.
Provides CRUD endpoints for roles and user assignments.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.rbac import AssignRoleRequest, AssignRoleResponse
from ai.backend.manager.data.permission.role import UserRoleAssignmentInput
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.errors.permission import InsufficientPermission
from ai.backend.manager.services.permission_contoller.actions import AssignRoleAction

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    # Role Assignment Endpoints

    @auth_required_for_method
    @api_handler
    async def assign_role(
        self,
        body: BodyParam[AssignRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Assign a role to a user."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise InsufficientPermission("Only superadmin can assign roles.")

        # Convert request to input
        input_data = UserRoleAssignmentInput(
            user_id=body.parsed.user_id,
            role_id=body.parsed.role_id,
            granted_by=body.parsed.granted_by or me.user_id,
        )

        # Call service action
        action_result = await processors.permission_controller.assign_role.wait_for_complete(
            AssignRoleAction(input=input_data)
        )

        # Build response
        resp = AssignRoleResponse(
            user_id=action_result.data.user_id,
            role_id=action_result.data.role_id,
            granted_by=action_result.data.granted_by,
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)


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
    cors.add(app.router.add_route("POST", "/role-assignments", api_handler.assign_role))

    return app, []
