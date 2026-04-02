import logging
from collections.abc import Sequence

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)
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
from ai.backend.manager.services.permission_contoller.actions.bulk_assign_role import (
    BulkAssignRoleAction,
    BulkAssignRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_revoke_role import (
    BulkRevokeRoleAction,
    BulkRevokeRoleActionResult,
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
from ai.backend.manager.services.permission_contoller.actions.get_permission_matrix import (
    GetPermissionMatrixAction,
    GetPermissionMatrixActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
    GetRoleDetailActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesAction,
    GetScopeTypesActionResult,
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
from ai.backend.manager.services.permission_contoller.actions.search_element_associations import (
    SearchElementAssociationsAction,
    SearchElementAssociationsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_entities import (
    SearchEntitiesAction,
    SearchEntitiesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    SearchPermissionsAction,
    SearchPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
    SearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesAction,
    SearchScopesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
    SearchUsersAssignedToRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
    UpdatePermissionActionResult,
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
    _rbac_action_registry: Sequence[type[BaseRBACAction]]

    def __init__(
        self,
        repository: PermissionControllerRepository,
        rbac_action_registry: Sequence[type[BaseRBACAction]],
    ) -> None:
        self._repository = repository
        self._rbac_action_registry = rbac_action_registry

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

    async def update_permission(
        self, action: UpdatePermissionAction
    ) -> UpdatePermissionActionResult:
        """
        Updates an existing permission in the repository.
        """
        result = await self._repository.update_permission(action.updater)
        return UpdatePermissionActionResult(data=result)

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

    async def bulk_assign_role(self, action: BulkAssignRoleAction) -> BulkAssignRoleActionResult:
        """Assigns a role to multiple users with partial failure support."""
        data = await self._repository.bulk_assign_role(action.bulk_creator)
        return BulkAssignRoleActionResult(data=data)

    async def bulk_revoke_role(self, action: BulkRevokeRoleAction) -> BulkRevokeRoleActionResult:
        """Revokes a role from multiple users with partial failure support."""
        data = await self._repository.bulk_revoke_role(action.input)
        return BulkRevokeRoleActionResult(data=data)

    async def get_role_detail(self, action: GetRoleDetailAction) -> GetRoleDetailActionResult:
        """Get role with all permission details and assigned users."""
        role_data = await self._repository.get_role_with_permissions(action.role_id)
        return GetRoleDetailActionResult(role=role_data)

    async def search_roles(self, action: SearchRolesAction) -> SearchRolesActionResult:
        """Search roles with pagination and filtering."""
        result = await self._repository.search_roles(action.querier)
        return SearchRolesActionResult(result=result)

    async def search_permissions(
        self, action: SearchPermissionsAction
    ) -> SearchPermissionsActionResult:
        """Search scoped permissions with pagination and filtering."""
        result = await self._repository.search_permissions(action.querier)
        return SearchPermissionsActionResult(result=result)

    async def search_users_assigned_to_role(
        self, action: SearchUsersAssignedToRoleAction
    ) -> SearchUsersAssignedToRoleActionResult:
        """Search users assigned to a specific role with pagination and filtering."""
        result = await self._repository.search_users_assigned_to_role(
            querier=action.querier,
        )
        return SearchUsersAssignedToRoleActionResult(result=result)

    async def update_role_permissions(
        self, action: UpdateRolePermissionsAction
    ) -> UpdateRolePermissionsActionResult:
        """Update role permissions using batch update."""
        result = await self._repository.update_role_permissions(
            input_data=action.input_data,
        )
        return UpdateRolePermissionsActionResult(role=result)

    async def search_scopes(self, action: SearchScopesAction) -> SearchScopesActionResult:
        """Search scopes based on element type."""
        result = await self._repository.search_scopes(action.element_type, action.querier)
        return SearchScopesActionResult(result=result)

    async def get_scope_types(self, _action: GetScopeTypesAction) -> GetScopeTypesActionResult:
        """Get all available scope types."""
        return GetScopeTypesActionResult(element_types=list(RBACElementType))

    async def get_entity_types(self, _action: GetEntityTypesAction) -> GetEntityTypesActionResult:
        """Get all available entity types."""
        return GetEntityTypesActionResult(element_types=list(RBACElementType))

    async def search_entities(self, action: SearchEntitiesAction) -> SearchEntitiesActionResult:
        """Search entities within a scope."""
        result = await self._repository.search_entities(action.querier)
        return SearchEntitiesActionResult(result=result)

    async def search_element_associations(
        self, action: SearchElementAssociationsAction
    ) -> SearchElementAssociationsActionResult:
        """Search element associations (full association rows) within a scope."""
        result = await self._repository.search_element_associations(action.querier)
        return SearchElementAssociationsActionResult(result=result)

    def get_entity_valid_operations(
        self,
    ) -> dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]]:
        """
        Get valid operations for all registered RBAC element types.

        Aggregates required permissions from all registered action classes,
        grouping them by element type. Each entry maps action name to its
        required permission.
        """
        result: dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]] = {}
        for action_cls in self._rbac_action_registry:
            perm = action_cls.required_permission()
            actions = result.setdefault(perm.element_type, {})
            actions[action_cls.action_name()] = perm
        return result

    async def get_permission_matrix(
        self, _action: GetPermissionMatrixAction
    ) -> GetPermissionMatrixActionResult:
        """
        Build the RBAC permission matrix: scope -> entity -> action_name -> permission.

        Reads ``permission_scope()`` from each registered RBAC action to produce
        the full (scope, entity, operation) mapping.
        """
        result: dict[
            RBACElementType, dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]]
        ] = {}
        for action_cls in self._rbac_action_registry:
            scope = action_cls.permission_scope()
            perm = action_cls.required_permission()
            entity_map = result.setdefault(scope, {})
            actions = entity_map.setdefault(perm.element_type, {})
            actions[action_cls.action_name()] = perm
        return GetPermissionMatrixActionResult(matrix=result)
