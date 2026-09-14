import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import role_scope_types
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action.rbac import build_operation_description
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.data.permission.types import GrantableOperation
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


class PermissionControllerService:
    _repository: PermissionControllerRepository
    _action_registry: ProcessorRegistry[Any]

    def __init__(
        self,
        repository: PermissionControllerRepository,
        action_registry: ProcessorRegistry[Any],
    ) -> None:
        self._repository = repository
        self._action_registry = action_registry

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
        """Search scopes of the given type."""
        result = await self._repository.search_scopes(action.scope_type, action.querier)
        return SearchScopesActionResult(result=result)

    async def get_scope_types(self, _action: GetScopeTypesAction) -> GetScopeTypesActionResult:
        """The scopes a role is created in."""
        return GetScopeTypesActionResult(entity_types=list(role_scope_types()))

    async def get_entity_types(self, _action: GetEntityTypesAction) -> GetEntityTypesActionResult:
        """The entities a role may permit, as the ops wiring declares them."""
        return GetEntityTypesActionResult(entity_types=sorted(self._grantable_operations()))

    def _grantable_operations(self) -> Mapping[EntityType, Sequence[GrantableOperation]]:
        """Every operation a role may permit, grouped by the entity answering for it.

        One action class may be wired more than once — an owner lookup is built by every
        field operation running it first — so the operations are keyed by name.
        """
        by_entity: dict[EntityType, dict[str, GrantableOperation]] = defaultdict(dict)
        for wiring in self._action_registry.role_grantable_wirings():
            entity_type = wiring.entity_type
            if entity_type is None:
                continue
            operation = wiring.action_cls.operation_type()
            name = str(wiring.action_cls.action_name())
            by_entity[entity_type][name] = GrantableOperation(
                name=name,
                description=build_operation_description(operation, entity_type),
                permission=operation.to_permission_bit(),
            )
        return {
            entity_type: sorted(operations.values(), key=lambda op: op.name)
            for entity_type, operations in by_entity.items()
        }

    async def get_permission_matrix(
        self, _action: GetPermissionMatrixAction
    ) -> GetPermissionMatrixActionResult:
        """The scope-entity-operation matrix a role editor offers.

        A permission row names an entity type and no scope, so every scope carries the
        same entities; the scope axis is there because a role sits in one.
        """
        operations = self._grantable_operations()
        return GetPermissionMatrixActionResult(matrix=dict.fromkeys(role_scope_types(), operations))
