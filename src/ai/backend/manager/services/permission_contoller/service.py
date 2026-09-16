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
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    PublicGetEntityTypesAction,
    PublicGetEntityTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_held_permissions import (
    ScopedGetHeldPermissionsAction,
    ScopedGetHeldPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_permission_matrix import (
    PublicGetPermissionMatrixAction,
    PublicGetPermissionMatrixActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
    GetRoleDetailActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    PublicGetScopeTypesAction,
    PublicGetScopeTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.replace_role_permissions import (
    ReplaceRolePermissionsAction,
    ReplaceRolePermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_my_role_assignments import (
    ScopedSearchRoleAssignmentsAction,
    ScopedSearchRoleAssignmentsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    GlobalSearchPermissionsAction,
    GlobalSearchPermissionsActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    GlobalSearchRolesAction,
    GlobalSearchRolesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles_in_scope import (
    SearchRolesInScopeAction,
    SearchRolesInScopeActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    GlobalSearchScopesAction,
    GlobalSearchScopesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    GlobalSearchRoleAssignmentsAction,
    GlobalSearchRoleAssignmentsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PermissionControllerService:
    _repository: PermissionControllerRepository
    _permission_check: RbacPermissionCheckRepository
    _action_registry: ProcessorRegistry[Any]

    def __init__(
        self,
        repository: PermissionControllerRepository,
        permission_check: RbacPermissionCheckRepository,
        action_registry: ProcessorRegistry[Any],
    ) -> None:
        self._repository = repository
        self._permission_check = permission_check
        self._action_registry = action_registry

    async def get_held_permissions(
        self, action: ScopedGetHeldPermissionsAction
    ) -> ScopedGetHeldPermissionsActionResult:
        """The bits each key's user holds, through every scope governing the named one."""
        granted = await self._permission_check.governed_permissions(action.keys)
        return ScopedGetHeldPermissionsActionResult(granted=granted)

    async def get_role_detail(self, action: GetRoleDetailAction) -> GetRoleDetailActionResult:
        """Get role with all permission details and assigned users."""
        role_data = await self._repository.get_role_with_permissions(action.role_id)
        return GetRoleDetailActionResult(role=role_data)

    async def search_roles(self, action: GlobalSearchRolesAction) -> GlobalSearchRolesActionResult:
        """Search roles with pagination and filtering."""
        result = await self._repository.search_roles(action.querier)
        return GlobalSearchRolesActionResult(result=result)

    async def search_roles_in_scope(
        self, action: SearchRolesInScopeAction
    ) -> SearchRolesInScopeActionResult:
        """Search the roles the named scopes reach."""
        result = await self._repository.search_roles_in_scope(
            action.querier, action.operation_scopes()
        )
        return SearchRolesInScopeActionResult(result=result)

    async def scoped_search_role_assignments(
        self, action: ScopedSearchRoleAssignmentsAction
    ) -> ScopedSearchRoleAssignmentsActionResult:
        """Search the assignment rows the named scopes reach."""
        result = await self._repository.search_role_assignments_in_scope(
            scopes=action.operation_scopes(), searcher=action.searcher
        )
        return ScopedSearchRoleAssignmentsActionResult(result=result)

    async def search_permissions(
        self, action: GlobalSearchPermissionsAction
    ) -> GlobalSearchPermissionsActionResult:
        """Search scoped permissions with pagination and filtering."""
        result = await self._repository.search_permissions(action.querier)
        return GlobalSearchPermissionsActionResult(result=result)

    async def search_users_assigned_to_role(
        self, action: GlobalSearchRoleAssignmentsAction
    ) -> GlobalSearchRoleAssignmentsActionResult:
        """Search users assigned to a specific role with pagination and filtering."""
        result = await self._repository.search_role_assignments_in_global(action.searcher)
        return GlobalSearchRoleAssignmentsActionResult(result=result)

    async def replace_role_permissions(
        self, action: ReplaceRolePermissionsAction
    ) -> ReplaceRolePermissionsActionResult:
        """Replace the role's entire scoped-permission set."""
        result = await self._repository.replace_role_permissions(
            role_id=action.role_id,
            entries=action.entries,
        )
        return ReplaceRolePermissionsActionResult(data=result)

    async def search_scopes(
        self, action: GlobalSearchScopesAction
    ) -> GlobalSearchScopesActionResult:
        """Search scopes of the given type."""
        result = await self._repository.search_scopes(action.scope_type, action.querier)
        return GlobalSearchScopesActionResult(result=result)

    async def get_scope_types(
        self, _action: PublicGetScopeTypesAction
    ) -> PublicGetScopeTypesActionResult:
        """The scopes a role is created in."""
        return PublicGetScopeTypesActionResult(entity_types=list(role_scope_types()))

    async def get_entity_types(
        self, _action: PublicGetEntityTypesAction
    ) -> PublicGetEntityTypesActionResult:
        """The entities a role may permit, as the ops wiring declares them."""
        return PublicGetEntityTypesActionResult(entity_types=sorted(self._grantable_operations()))

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
        self, _action: PublicGetPermissionMatrixAction
    ) -> PublicGetPermissionMatrixActionResult:
        """The scope-entity-operation matrix a role editor offers.

        A permission row names an entity type and no scope, so every scope carries the
        same entities; the scope axis is there because a role sits in one.
        """
        operations = self._grantable_operations()
        return PublicGetPermissionMatrixActionResult(
            matrix=dict.fromkeys(role_scope_types(), operations)
        )
