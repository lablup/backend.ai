"""
REST API handlers for RBAC system.
Provides CRUD endpoints for roles and user assignments.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.rbac import DeleteRoleResponse
from ai.backend.manager.data.permission.role import RoleDeleteInput
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.rbac_request import DeleteRolePathParam
from ai.backend.manager.errors.permission import InsufficientPermission, RoleNotFound
from ai.backend.manager.services.permission_contoller.actions import DeleteRoleAction

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    # Role CRUD Endpoints

    @auth_required_for_method
    @api_handler
    async def delete_role(
        self,
        path: PathParam[DeleteRolePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a role."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise InsufficientPermission("Only superadmin can delete roles.")

        # Call service action
        action_result = await processors.permission_controller.delete_role.wait_for_complete(
            DeleteRoleAction(input=RoleDeleteInput(id=path.parsed.role_id))
        )

        if not action_result.success:
            raise RoleNotFound(f"Role {path.parsed.role_id} not found")

        # Build response
        resp = DeleteRoleResponse(deleted=action_result.success)
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
    cors.add(app.router.add_route("DELETE", "/roles/{role_id}", api_handler.delete_role))

    return app, []
