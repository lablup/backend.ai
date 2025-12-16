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
    UpdateRoleRequest,
    UpdateRoleResponse,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.rbac_request import UpdateRolePathParam
from ai.backend.manager.errors.permission import InsufficientPermission, RoleNotFound
from ai.backend.manager.services.permission_contoller.actions import UpdateRoleAction

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
    async def update_role(
        self,
        path: PathParam[UpdateRolePathParam],
        body: BodyParam[UpdateRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing role."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise InsufficientPermission("Only superadmin can update roles.")

        # Call service action
        action_result = await processors.permission_controller.update_role.wait_for_complete(
            UpdateRoleAction(
                input=self.role_adapter.build_modifier(path.parsed.role_id, body.parsed)
            )
        )

        if not action_result.success or action_result.data is None:
            raise RoleNotFound(f"Role {path.parsed.role_id} not found")

        # Build response
        resp = UpdateRoleResponse(role=self.role_adapter.convert_to_dto(action_result.data))
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
    cors.add(app.router.add_route("PATCH", "/roles/{role_id}", api_handler.update_role))

    return app, []
