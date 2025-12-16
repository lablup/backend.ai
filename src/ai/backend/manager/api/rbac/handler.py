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
from ai.backend.common.dto.manager.rbac import (
    CreateRoleRequest,
    CreateRoleResponse,
)
from ai.backend.manager.data.permission.role import RoleCreateInput
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.models.rbac.exceptions import NotEnoughPermission
from ai.backend.manager.services.permission_contoller.actions import CreateRoleAction

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware
from .adapter import RoleAdapter

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    def __init__(self) -> None:
        self.role_adapter = RoleAdapter()

    # Role CRUD Endpoints

    @auth_required_for_method
    @api_handler
    async def create_role(
        self,
        body: BodyParam[CreateRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new role."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can create roles.")

        # Convert request to creator
        creator = RoleCreateInput(
            name=body.parsed.name,
            source=body.parsed.source,
            status=body.parsed.status,
            description=body.parsed.description,
        )

        # Call service action
        action_result = await processors.permission_controller.create_role.wait_for_complete(
            CreateRoleAction(input=creator)
        )

        # Build response
        resp = CreateRoleResponse(role=self.role_adapter.convert_to_dto(action_result.data))
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

    # Role routes
    cors.add(app.router.add_route("POST", "/roles", api_handler.create_role))

    return app, []
