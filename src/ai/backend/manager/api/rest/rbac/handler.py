"""RBAC handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

from http import HTTPStatus

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import RuntimeEntityID
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
from ai.backend.common.dto.manager.rbac.path import SearchScopesPathParam
from ai.backend.common.dto.manager.rbac.request import (
    DeleteRoleRequest,
    PurgeRoleRequest,
    SearchScopesRequest,
)
from ai.backend.common.dto.manager.rbac.response import (
    GetEntityTypesResponse,
    GetScopeTypesResponse,
    SearchScopesResponse,
)
from ai.backend.manager.data.permission.role import UserRoleAssignmentInput, UserRoleRevocationInput
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.updaters import RoleSoftDeleteUpdater
from ai.backend.manager.services.permission_contoller.actions import (
    CreateRoleAction,
    DeleteRoleAction,
    GetRoleDetailAction,
    SearchRolesAction,
    SearchUsersAssignedToRoleAction,
    UpdateRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    GetEntityTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesAction,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.rbac.actions.role.assign import AssignRoleAction
from ai.backend.manager.services.rbac.actions.role.revoke import RevokeRoleAction
from ai.backend.manager.services.rbac.processors import RbacProcessors

from .assigned_user_adapter import AssignedUserAdapter
from .role_adapter import RoleAdapter
from .scope_adapter import ScopeAdapter


class RBACHandler:
    """REST API handler for RBAC operations with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        permission_controller: PermissionControllerProcessors,
        rbac: RbacProcessors,
    ) -> None:
        self._permission_controller = permission_controller
        self._rbac = rbac
        self._role_adapter = RoleAdapter()
        self._assigned_user_adapter = AssignedUserAdapter()
        self._scope_adapter = ScopeAdapter()

    # Role Management Endpoints

    async def create_role(
        self,
        body: BodyParam[CreateRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Create a new role."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can create roles.")

        result = await self._permission_controller.create_role.run(
            CreateRoleAction(
                creator=RoleCreator(
                    name=body.parsed.name,
                    scope=RuntimeEntityID(body.parsed.scope_type, body.parsed.scope_id),
                    status=body.parsed.status,
                    description=body.parsed.description,
                )
            )
        )
        resp = CreateRoleResponse(role=self._role_adapter.convert_to_dto(result.data))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_roles(
        self,
        body: BodyParam[SearchRolesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search roles with filters, orders, and pagination."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can search roles.")

        querier = self._role_adapter.build_querier(body.parsed)
        action_result = await self._permission_controller.search_roles.wait_for_complete(
            SearchRolesAction(querier=querier)
        )
        resp = SearchRolesResponse(
            roles=[self._role_adapter.convert_to_dto(role) for role in action_result.result.items],
            pagination=PaginationInfo(
                total=action_result.result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_role(
        self,
        path: PathParam[GetRolePathParam],
        ctx: UserContext,
    ) -> APIResponse:
        """Get a specific role with details."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can get role details.")

        action_result = await self._permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=path.parsed.role_id)
        )
        resp = GetRoleResponse(role=self._role_adapter.convert_to_dto(action_result.role))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_role(
        self,
        path: PathParam[UpdateRolePathParam],
        body: BodyParam[UpdateRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Update an existing role."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can update roles.")

        role_id = path.parsed.role_id
        updater = self._role_adapter.build_updater(body.parsed, role_id)
        result = await self._permission_controller.update_role.run(
            UpdateRoleAction(updater=updater)
        )
        resp = UpdateRoleResponse(role=self._role_adapter.convert_to_dto(result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_role(
        self,
        body: BodyParam[DeleteRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Delete a role (soft delete)."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can delete roles.")

        await self._permission_controller.delete_role.run(
            DeleteRoleAction(updater=RoleSoftDeleteUpdater(role_id=RoleID(body.parsed.role_id)))
        )
        resp = DeleteRoleResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def purge_role(
        self,
        body: BodyParam[PurgeRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Purge a role (hard delete)."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can purge roles.")

        await self._permission_controller.purge_role.run(
            PurgeRoleAction(role_id=RoleID(body.parsed.role_id))
        )
        resp = DeleteRoleResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Role Assignment Endpoints

    async def assign_role(
        self,
        body: BodyParam[AssignRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Assign a role to a user."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can assign roles.")

        input_data = UserRoleAssignmentInput(
            user_id=body.parsed.user_id,
            role_id=body.parsed.role_id,
            granted_by=body.parsed.granted_by or ctx.user_uuid,
        )
        action_result = await self._rbac.assign_role.wait_for_complete(
            AssignRoleAction(input=input_data)
        )
        resp = AssignRoleResponse(
            user_id=action_result.data.user_id,
            role_id=action_result.data.role_id,
            granted_by=action_result.data.granted_by,
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def revoke_role(
        self,
        body: BodyParam[RevokeRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Revoke a role from a user."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can revoke roles.")

        input_data = UserRoleRevocationInput(
            user_id=body.parsed.user_id,
            role_id=body.parsed.role_id,
        )
        action_result = await self._rbac.revoke_role.wait_for_complete(
            RevokeRoleAction(input=input_data)
        )
        resp = RevokeRoleResponse(
            user_id=action_result.data.user_id,
            role_id=action_result.data.role_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_assigned_users(
        self,
        path: PathParam[SearchUsersAssignedToRolePathParam],
        body: BodyParam[SearchUsersAssignedToRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search users assigned to a specific role with filters and pagination."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can search assigned users.")

        querier = self._assigned_user_adapter.build_querier(path.parsed, body.parsed)
        action_result = (
            await self._permission_controller.search_users_assigned_to_role.wait_for_complete(
                SearchUsersAssignedToRoleAction(querier=querier)
            )
        )
        resp = SearchUsersAssignedToRoleResponse(
            users=[
                self._assigned_user_adapter.convert_to_dto(user)
                for user in action_result.result.items
            ],
            pagination=PaginationInfo(
                total=action_result.result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Scope Management Endpoints

    async def get_scope_types(
        self,
        ctx: UserContext,
    ) -> APIResponse:
        """Get available scope types for role configuration."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can access scope types.")

        action_result = await self._permission_controller.get_scope_types.wait_for_complete(
            GetScopeTypesAction()
        )
        resp = GetScopeTypesResponse(items=action_result.entity_types)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_scopes(
        self,
        path: PathParam[SearchScopesPathParam],
        body: BodyParam[SearchScopesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search scopes for a specific scope type with filters and pagination."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can search scopes.")

        scope_type = path.parsed.scope_type
        querier = self._scope_adapter.build_querier(scope_type, body.parsed)
        action = SearchScopesAction(scope_type=scope_type, querier=querier)
        action_result = await self._permission_controller.search_scopes.wait_for_complete(action)
        resp = SearchScopesResponse(
            items=[self._scope_adapter.convert_to_dto(item) for item in action_result.result.items],
            pagination=PaginationInfo(
                total=action_result.result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Entity Management Endpoints

    async def get_entity_types(
        self,
        ctx: UserContext,
    ) -> APIResponse:
        """Get available entity types for role configuration."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can access entity types.")

        action_result = await self._permission_controller.get_entity_types.wait_for_complete(
            GetEntityTypesAction()
        )
        resp = GetEntityTypesResponse(items=action_result.entity_types)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
