import logging

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    CreateRoleInput,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.permission_contoller.actions.assign_role import (
    AssignRoleAction,
    AssignRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import (
    CreateRoleAction,
    CreateRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.delete_role import (
    DeleteRoleAction,
    DeleteRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    GetEntityTypesAction,
    GetEntityTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
    GetRoleDetailActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesAction,
    GetScopeTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.object_permission import (
    CreateObjectPermissionAction,
    CreateObjectPermissionActionResult,
    DeleteObjectPermissionAction,
    DeleteObjectPermissionActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    CreatePermissionActionResult,
    DeletePermissionAction,
    DeletePermissionActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import (
    PurgeRoleAction,
    PurgeRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.revoke_role import (
    RevokeRoleAction,
    RevokeRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_entities import (
    SearchEntitiesAction,
    SearchEntitiesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_object_permissions import (
    SearchObjectPermissionsAction,
    SearchObjectPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
    SearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_scoped_permissions import (
    SearchScopedPermissionsAction,
    SearchScopedPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesAction,
    SearchScopesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import (
    UpdateRoleAction,
    UpdateRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_role_permissions import (
    UpdateRolePermissionsAction,
    UpdateRolePermissionsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PermissionControllerService:
    _repository: PermissionControllerRepository

    def __init__(self, repository: PermissionControllerRepository) -> None:
        self._repository = repository

    async def create_role(self, action: CreateRoleAction) -> CreateRoleActionResult:
        """
        Creates a new role in the repository.
        """
        input_data = CreateRoleInput(
            creator=action.creator,
            object_permissions=action.object_permissions,
        )
        result = await self._repository.create_role(input_data)
        return CreateRoleActionResult(
            data=result,
        )

    async def create_permission(
        self, action: CreatePermissionAction
    ) -> CreatePermissionActionResult:
        """
        Creates a new permission in the repository.
        """
        result = await self._repository.create_permission(action.creator)
        return CreatePermissionActionResult(data=result)

    async def delete_permission(
        self, action: DeletePermissionAction
    ) -> DeletePermissionActionResult:
        """
        Deletes a permission from the repository.
        """
        result = await self._repository.delete_permission(action.purger)
        return DeletePermissionActionResult(data=result)

    async def create_object_permission(
        self, action: CreateObjectPermissionAction
    ) -> CreateObjectPermissionActionResult:
        """
        Creates a new object permission in the repository.
        """
        result = await self._repository.create_object_permission(action.creator)
        return CreateObjectPermissionActionResult(data=result)

    async def delete_object_permission(
        self, action: DeleteObjectPermissionAction
    ) -> DeleteObjectPermissionActionResult:
        """
        Deletes an object permission from the repository.
        """
        result = await self._repository.delete_object_permission(action.purger)
        return DeleteObjectPermissionActionResult(data=result)

    async def update_role(self, action: UpdateRoleAction) -> UpdateRoleActionResult:
        """
        Updates an existing role in the repository.
        """
        result = await self._repository.update_role(action.updater)
        return UpdateRoleActionResult(data=result)

    async def delete_role(self, action: DeleteRoleAction) -> DeleteRoleActionResult:
        """
        Deletes a role from the repository. It marks the role as deleted (soft delete).
        Raises ObjectNotFound if the role does not exist.
        """
        result = await self._repository.delete_role(action.updater)
        return DeleteRoleActionResult(data=result)

    async def purge_role(self, action: PurgeRoleAction) -> PurgeRoleActionResult:
        """
        Purges a role from the repository. It permanently removes the role (hard delete).
        Raises ObjectNotFound if the role does not exist.
        """
        result = await self._repository.purge_role(action.purger)
        return PurgeRoleActionResult(data=result)

    async def assign_role(self, action: AssignRoleAction) -> AssignRoleActionResult:
        """
        Assigns a role to a user.
        """
        data = await self._repository.assign_role(action.input)

        return AssignRoleActionResult(data=data)

    async def revoke_role(self, action: RevokeRoleAction) -> RevokeRoleActionResult:
        """
        Revokes a role from a user.
        """
        data = await self._repository.revoke_role(action.input)

        return RevokeRoleActionResult(data=data)

    async def get_role_detail(self, action: GetRoleDetailAction) -> GetRoleDetailActionResult:
        """Get role with all permission details and assigned users."""
        role_data = await self._repository.get_role_with_permissions(action.role_id)
        return GetRoleDetailActionResult(role=role_data)

    async def search_roles(self, action: SearchRolesAction) -> SearchRolesActionResult:
        """Search roles with pagination and filtering."""
        result = await self._repository.search_roles(action.querier)
        return SearchRolesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_scoped_permissions(
        self, action: SearchScopedPermissionsAction
    ) -> SearchScopedPermissionsActionResult:
        """Search scoped permissions with pagination and filtering."""
        result = await self._repository.search_scoped_permissions(action.querier)
        return SearchScopedPermissionsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_object_permissions(
        self, action: SearchObjectPermissionsAction
    ) -> SearchObjectPermissionsActionResult:
        """Search object permissions with pagination and filtering."""
        result = await self._repository.search_object_permissions(action.querier)
        return SearchObjectPermissionsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_users_assigned_to_role(
        self, action: SearchUsersAssignedToRoleAction
    ) -> SearchUsersAssignedToRoleActionResult:
        """Search users assigned to a specific role with pagination and filtering."""
        result = await self._repository.search_users_assigned_to_role(
            querier=action.querier,
        )
        return SearchUsersAssignedToRoleActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update_role_permissions(
        self, action: UpdateRolePermissionsAction
    ) -> UpdateRolePermissionsActionResult:
        """Update role permissions using batch update."""
        result = await self._repository.update_role_permissions(
            input_data=action.input_data,
        )
        return UpdateRolePermissionsActionResult(role=result)

    async def search_scopes(self, action: SearchScopesAction) -> SearchScopesActionResult:
        """Search scopes based on scope type."""
        result = await self._repository.search_scopes(action.scope_type, action.querier)
        return SearchScopesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_scope_types(self, _action: GetScopeTypesAction) -> GetScopeTypesActionResult:
        """Get all available scope types."""
        return GetScopeTypesActionResult(scope_types=list(ScopeType))

    async def get_entity_types(self, _action: GetEntityTypesAction) -> GetEntityTypesActionResult:
        """Get all available entity types."""
        return GetEntityTypesActionResult(entity_types=list(EntityType))

    async def search_entities(self, action: SearchEntitiesAction) -> SearchEntitiesActionResult:
        """Search entities within a scope."""
        result = await self._repository.search_entities(action.querier)
        return SearchEntitiesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
