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
from ai.backend.common.dto.manager.rbac import RevokeRoleRequest, RevokeRoleResponse
from ai.backend.manager.data.permission.role import UserRoleRevocationInput
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.errors.permission import InsufficientPermission
from ai.backend.manager.services.permission_contoller.actions import RevokeRoleAction

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    # Role Assignment Endpoints

    @auth_required_for_method
    @api_handler
    async def revoke_role(
        self,
        body: BodyParam[RevokeRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Revoke a role from a user."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise InsufficientPermission("Only superadmin can revoke roles.")

        # Convert request to input
        input_data = UserRoleRevocationInput(
            user_id=body.parsed.user_id,
            role_id=body.parsed.role_id,
        )

        # Call service action
        action_result = await processors.permission_controller.revoke_role.wait_for_complete(
            RevokeRoleAction(input=input_data)
        )

        # Build response
        resp = RevokeRoleResponse(
            user_role_id=action_result.data.user_role_id,
            user_id=action_result.data.user_id,
            role_id=action_result.data.role_id,
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
    cors.add(app.router.add_route("DELETE", "/role-assignments", api_handler.revoke_role))

    return app, []
