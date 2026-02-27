"""RBAC handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

from http import HTTPStatus

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
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
from ai.backend.common.dto.manager.rbac.path import SearchEntitiesPathParam, SearchScopesPathParam
from ai.backend.common.dto.manager.rbac.request import (
    DeleteRoleRequest,
    PurgeRoleRequest,
    SearchEntitiesRequest,
    SearchScopesRequest,
)
from ai.backend.common.dto.manager.rbac.response import (
    GetEntityTypesResponse,
    GetScopeTypesResponse,
    SearchEntitiesResponse,
    SearchScopesResponse,
)
from ai.backend.manager.api.rbac.assigned_user_adapter import AssignedUserAdapter
from ai.backend.manager.api.rbac.entity_adapter import EntityAdapter
from ai.backend.manager.api.rbac.role_adapter import RoleAdapter
from ai.backend.manager.api.rbac.scope_adapter import ScopeAdapter
from ai.backend.manager.data.permission.role import UserRoleAssignmentInput, UserRoleRevocationInput
from ai.backend.manager.dto.context import UserContext
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
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    GetEntityTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.search_entities import (
    SearchEntitiesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesAction,
)
from ai.backend.manager.services.processors import Processors


class RBACHandler:
    """REST API handler for RBAC operations with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors
        self._role_adapter = RoleAdapter()
        self._assigned_user_adapter = AssignedUserAdapter()
        self._scope_adapter = ScopeAdapter()
        self._entity_adapter = EntityAdapter()

    # Role Management Endpoints

    async def create_role(
        self,
        body: BodyParam[CreateRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Create a new role."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can create roles.")

        creator = Creator(
            spec=RoleCreatorSpec(
                name=body.parsed.name,
                source=body.parsed.source,
                status=body.parsed.status,
                description=body.parsed.description,
            )
        )
        action_result = await self._processors.permission_controller.create_role.wait_for_complete(
            CreateRoleAction(creator=creator)
        )
        resp = CreateRoleResponse(role=self._role_adapter.convert_to_dto(action_result.data))
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
        action_result = await self._processors.permission_controller.search_roles.wait_for_complete(
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

        action_result = (
            await self._processors.permission_controller.get_role_detail.wait_for_complete(
                GetRoleDetailAction(role_id=path.parsed.role_id)
            )
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
        action_result = await self._processors.permission_controller.update_role.wait_for_complete(
            UpdateRoleAction(updater=updater)
        )
        resp = UpdateRoleResponse(role=self._role_adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_role(
        self,
        body: BodyParam[DeleteRoleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Delete a role (soft delete)."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can delete roles.")

        role_id = body.parsed.role_id
        updater: Updater[RoleRow] = self._role_adapter.build_deleter(role_id)
        await self._processors.permission_controller.delete_role.wait_for_complete(
            DeleteRoleAction(updater=updater)
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

        role_id = body.parsed.role_id
        purger: Purger[RoleRow] = self._role_adapter.build_purger(role_id)
        await self._processors.permission_controller.purge_role.wait_for_complete(
            PurgeRoleAction(purger=purger)
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
        action_result = await self._processors.permission_controller.assign_role.wait_for_complete(
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
        action_result = await self._processors.permission_controller.revoke_role.wait_for_complete(
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
        action_result = await self._processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
            SearchUsersAssignedToRoleAction(querier=querier)
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

        action_result = (
            await self._processors.permission_controller.get_scope_types.wait_for_complete(
                GetScopeTypesAction()
            )
        )
        resp = GetScopeTypesResponse(items=action_result.scope_types)
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
        action_result = (
            await self._processors.permission_controller.search_scopes.wait_for_complete(action)
        )
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

        action_result = (
            await self._processors.permission_controller.get_entity_types.wait_for_complete(
                GetEntityTypesAction()
            )
        )
        resp = GetEntityTypesResponse(items=action_result.entity_types)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_entities(
        self,
        path: PathParam[SearchEntitiesPathParam],
        body: BodyParam[SearchEntitiesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search entities within a scope by entity type with filters and pagination."""
        if not ctx.is_superadmin:
            raise NotEnoughPermission("Only superadmin can search entities.")

        querier = self._entity_adapter.build_querier(
            scope_type=path.parsed.scope_type,
            scope_id=path.parsed.scope_id,
            entity_type=path.parsed.entity_type,
            request=body.parsed,
        )
        action = SearchEntitiesAction(querier=querier)
        action_result = (
            await self._processors.permission_controller.search_entities.wait_for_complete(action)
        )
        resp = SearchEntitiesResponse(
            items=[
                self._entity_adapter.convert_to_dto(item) for item in action_result.result.items
            ],
            pagination=PaginationInfo(
                total=action_result.result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
