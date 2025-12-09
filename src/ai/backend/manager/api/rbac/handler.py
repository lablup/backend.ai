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
    AssignRoleRequest,
    AssignRoleResponse,
    CreateRoleRequest,
    CreateRoleResponse,
    DeleteRoleResponse,
    GetRoleResponse,
    PaginationInfo,
    SearchRolesRequest,
    SearchRolesResponse,
    SearchUsersAssignedToRoleRequest,
    SearchUsersAssignedToRoleResponse,
    UpdateRoleRequest,
    UpdateRoleResponse,
)
from ai.backend.manager.data.permission.role import (
    RoleCreateInput,
    RoleDeleteInput,
    UserRoleAssignmentInput,
)
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.rbac_request import (
    DeleteRolePathParam,
    GetRolePathParam,
    SearchUsersAssignedToRolePathParam,
    UpdateRolePathParam,
)
from ai.backend.manager.services.permission_contoller.actions import (
    AssignRoleAction,
    CreateRoleAction,
    DeleteRoleAction,
    GetRoleDetailAction,
    SearchRolesAction,
    SearchUsersAssignedToRoleAction,
    UpdateRoleAction,
)

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware
from .adapter import AssignedUserAdapter, RoleAdapter

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    def __init__(self) -> None:
        self.role_adapter = RoleAdapter()
        self.user_adapter = AssignedUserAdapter()

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
            raise web.HTTPForbidden(reason="Only superadmin can create roles.")

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
            raise web.HTTPForbidden(reason="Only superadmin can search roles.")

        # Build querier using adapter
        querier = self.role_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await processors.permission_controller.search_roles.wait_for_complete(
            SearchRolesAction(querier=querier)
        )

        # Build response
        resp = SearchRolesResponse(
            roles=[self.role_adapter.convert_to_dto(role) for role in action_result.roles.items],
            pagination=PaginationInfo(
                total=action_result.roles.total_count,
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
            raise web.HTTPForbidden(reason="Only superadmin can get roles.")

        action_result = await processors.permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=path.parsed.role_id)
        )
        role_data = action_result.role

        # Build response
        resp = GetRoleResponse(role=self.role_adapter.convert_to_dto(role_data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

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
            raise web.HTTPForbidden(reason="Only superadmin can update roles.")

        # Call service action
        action_result = await processors.permission_controller.update_role.wait_for_complete(
            UpdateRoleAction(
                input=self.role_adapter.build_modifier(path.parsed.role_id, body.parsed)
            )
        )

        if not action_result.success or action_result.data is None:
            raise web.HTTPNotFound(reason=f"Role {path.parsed.role_id} not found")

        # Build response
        resp = UpdateRoleResponse(role=self.role_adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

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
            raise web.HTTPForbidden(reason="Only superadmin can delete roles.")

        # Call service action
        action_result = await processors.permission_controller.delete_role.wait_for_complete(
            DeleteRoleAction(input=RoleDeleteInput(id=path.parsed.role_id))
        )

        if not action_result.success:
            raise web.HTTPNotFound(reason=f"Role {path.parsed.role_id} not found")

        # Build response
        resp = DeleteRoleResponse(deleted=action_result.success)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

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
            raise web.HTTPForbidden(reason="Only superadmin can assign roles.")

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
            raise web.HTTPForbidden(reason="Only superadmin can search assigned users.")

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
            users=[self.user_adapter.convert_to_dto(user) for user in action_result.users.items],
            pagination=PaginationInfo(
                total=action_result.users.total_count,
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

    # Role routes
    cors.add(app.router.add_route("POST", "/roles", api_handler.create_role))
    cors.add(app.router.add_route("POST", "/roles/search", api_handler.search_roles))
    cors.add(app.router.add_route("GET", "/roles/{role_id}", api_handler.get_role))
    cors.add(app.router.add_route("PATCH", "/roles/{role_id}", api_handler.update_role))
    cors.add(app.router.add_route("DELETE", "/roles/{role_id}", api_handler.delete_role))

    # Role assignment routes
    cors.add(app.router.add_route("POST", "/role-assignments", api_handler.assign_role))
    cors.add(
        app.router.add_route(
            "POST", "/roles/{role_id}/users/search", api_handler.search_users_assigned_to_role
        )
    )

    return app, []
