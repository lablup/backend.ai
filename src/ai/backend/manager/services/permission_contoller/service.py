import logging
from collections.abc import Sequence

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
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
from ai.backend.manager.services.permission_contoller.actions.replace_role_permissions import (
    ReplaceRolePermissionsAction,
    ReplaceRolePermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    SearchPermissionsAction,
    SearchPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
    SearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles_in_scope import (
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Grant operations are declared in the RBAC action registry as placeholders for a future
# entity-delegation feature, but no executable action can request them yet
# (``ActionOperationType`` has no GRANT member). Exclude them from the permission matrix so
# it only exposes (scope, entity, operation) combinations that are actually enforced.
_GRANT_OPERATIONS: frozenset[OperationType] = frozenset({
    OperationType.GRANT_ALL,
    OperationType.GRANT_READ,
    OperationType.GRANT_UPDATE,
    OperationType.GRANT_SOFT_DELETE,
    OperationType.GRANT_HARD_DELETE,
})


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

    async def create_permission(
        self, action: CreatePermissionAction
    ) -> CreatePermissionActionResult:
        """
        Creates a new permission in the repository.
        """
        result = await self._repository.create_permission(action.role_id, action.creator)
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

    async def get_role_detail(self, action: GetRoleDetailAction) -> GetRoleDetailActionResult:
        """Get role with all permission details and assigned users."""
        role_data = await self._repository.get_role_with_permissions(action.role_id)
        return GetRoleDetailActionResult(role=role_data)

    async def search_roles(self, action: SearchRolesAction) -> SearchRolesActionResult:
        """Search roles with pagination and filtering."""
        result = await self._repository.search_roles(action.querier)
        return SearchRolesActionResult(result=result)

    async def search_roles_in_scope(
        self, action: SearchRolesInScopeAction
    ) -> SearchRolesInScopeActionResult:
        """Search roles registered in a given scope."""
        result = await self._repository.search_roles_in_scope(action.querier, action.scope)
        return SearchRolesInScopeActionResult(result=result)

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

    async def replace_role_permissions(
        self, action: ReplaceRolePermissionsAction
    ) -> ReplaceRolePermissionsActionResult:
        """Replace the role's entire scoped-permission set."""
        result = await self._repository.replace_role_permissions(
            role_id=action.role_id,
            entries=action.entries,
        )
        return ReplaceRolePermissionsActionResult(data=result)

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
        the (scope, entity, operation) mapping. Grant operations are skipped because
        they are not yet enforceable at runtime (see ``_GRANT_OPERATIONS``).
        """
        result: dict[
            RBACElementType, dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]]
        ] = {}
        for action_cls in self._rbac_action_registry:
            perm = action_cls.required_permission()
            if perm.operation in _GRANT_OPERATIONS:
                continue
            scope = action_cls.permission_scope()
            entity_map = result.setdefault(scope, {})
            actions = entity_map.setdefault(perm.element_type, {})
            actions[action_cls.action_name()] = perm
        return GetPermissionMatrixActionResult(matrix=result)
