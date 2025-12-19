"""
REST API handlers for RBAC (Role-Based Access Control) system.
Provides CRUD endpoints for role management and role assignment operations.
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
    GetRolePathParam,
    GetRoleResponse,
    PaginationInfo,
    RevokeRoleRequest,
    RevokeRoleResponse,
    SearchRolesRequest,
    SearchRolesResponse,
    SearchUsersAssignedToRolePathParam,
    SearchUsersAssignedToRoleRequest,
    SearchUsersAssignedToRoleResponse,
    UpdateRolePathParam,
    UpdateRoleRequest,
    UpdateRoleResponse,
)
from ai.backend.common.dto.manager.rbac.request import DeleteRoleRequest, PurgeRoleRequest
from ai.backend.manager.data.permission.role import UserRoleAssignmentInput, UserRoleRevocationInput
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base import Creator, Purger, Updater
from ai.backend.manager.repositories.permission_controller.creators import RoleCreatorSpec
from ai.backend.manager.services.permission_contoller.actions import (
    AssignRoleAction,
    CreateRoleAction,
    DeleteRoleAction,
    GetRoleDetailAction,
    RevokeRoleAction,
    SearchRolesAction,
    SearchUsersAssignedToRoleAction,
    UpdateRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware
from .assigned_user_adapter import AssignedUserAdapter
from .role_adapter import RoleAdapter

__all__ = ("create_app",)


class RBACAPIHandler:
    """REST API handler class for RBAC operations."""

    def __init__(self) -> None:
        self.role_adapter = RoleAdapter()
        self.assigned_user_adapter = AssignedUserAdapter()

    # Role Management Endpoints

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
        creator = Creator(
            spec=RoleCreatorSpec(
                name=body.parsed.name,
                source=body.parsed.source,
                status=body.parsed.status,
                description=body.parsed.description,
            )
        )

        # Call service action
        action_result = await processors.permission_controller.create_role.wait_for_complete(
            CreateRoleAction(creator=creator)
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
            raise NotEnoughPermission("Only superadmin can search roles.")

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
        """Get a specific role with details."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can get role details.")

        # Call service action
        action_result = await processors.permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=path.parsed.role_id)
        )

        # Build response
        resp = GetRoleResponse(role=self.role_adapter.convert_to_dto(action_result.role))
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
            raise NotEnoughPermission("Only superadmin can update roles.")

        # Build updater using adapter
        role_id = path.parsed.role_id
        updater = self.role_adapter.build_updater(body.parsed, role_id)

        # Call service action
        action_result = await processors.permission_controller.update_role.wait_for_complete(
            UpdateRoleAction(updater=updater)
        )

        # Build response
        resp = UpdateRoleResponse(role=self.role_adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete_role(
        self,
        body: BodyParam[DeleteRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a role (soft delete)."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can delete roles.")

        role_id = body.parsed.role_id

        # Create updater
        updater: Updater[RoleRow] = self.role_adapter.build_deleter(role_id)

        # Call service action
        await processors.permission_controller.delete_role.wait_for_complete(
            DeleteRoleAction(updater=updater)
        )

        # Build response
        resp = DeleteRoleResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def purge_role(
        self,
        body: BodyParam[PurgeRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a role (soft delete)."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can delete roles.")

        role_id = body.parsed.role_id

        # Create purger
        purger: Purger[RoleRow] = self.role_adapter.build_purger(role_id)

        # Call service action
        await processors.permission_controller.purge_role.wait_for_complete(
            PurgeRoleAction(purger=purger)
        )

        # Build response
        resp = DeleteRoleResponse(deleted=True)
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
            raise NotEnoughPermission("Only superadmin can assign roles.")

        # Create assignment input
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
    async def revoke_role(
        self,
        body: BodyParam[RevokeRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Revoke a role from a user."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can revoke roles.")

        # Create revocation input
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
            user_id=action_result.data.user_id,
            role_id=action_result.data.role_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_assigned_users(
        self,
        path: PathParam[SearchUsersAssignedToRolePathParam],
        body: BodyParam[SearchUsersAssignedToRoleRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search users assigned to a specific role with filters and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can search assigned users.")

        # Build querier using adapter (includes role_id as filter condition)
        querier = self.assigned_user_adapter.build_querier(path.parsed, body.parsed)

        # Call service action
        action_result = (
            await processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(querier=querier)
            )
        )

        # Build response
        resp = SearchUsersAssignedToRoleResponse(
            users=[self.assigned_user_adapter.convert_to_dto(user) for user in action_result.items],
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
    app["prefix"] = "v2.0"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = RBACAPIHandler()

    # Role management routes
    cors.add(app.router.add_route("POST", "/admin/rbac/roles", api_handler.create_role))
    cors.add(app.router.add_route("POST", "/admin/rbac/roles/search", api_handler.search_roles))
    cors.add(app.router.add_route("GET", "/admin/rbac/roles/{role_id}", api_handler.get_role))
    cors.add(app.router.add_route("PATCH", "/admin/rbac/roles/{role_id}", api_handler.update_role))
    cors.add(app.router.add_route("POST", "/admin/rbac/roles/delete", api_handler.delete_role))
    cors.add(app.router.add_route("POST", "/admin/rbac/roles/purge", api_handler.purge_role))

    # Role assignment routes
    cors.add(app.router.add_route("POST", "/admin/rbac/roles/assign", api_handler.assign_role))
    cors.add(app.router.add_route("POST", "/admin/rbac/roles/revoke", api_handler.revoke_role))
    cors.add(
        app.router.add_route(
            "POST",
            "/admin/rbac/roles/{role_id}/assigned-users/search",
            api_handler.search_assigned_users,
        )
    )

    return app, []
