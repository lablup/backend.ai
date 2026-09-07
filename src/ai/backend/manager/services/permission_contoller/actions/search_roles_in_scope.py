from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.rbac_models.role.scopes import ScopedRoleOperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import (
    RoleScopeAction,
    RoleScopeActionResult,
)


@dataclass
class SearchRolesInScopeAction(RoleScopeAction):
    """Read the roles a scope owns, along ``scope -> virtual entity -> entity``.

    A role created before the v2 write path has no virtual entity node yet and is
    absent from this answer until BA-7571 backfills one.
    """

    scope: ScopedRoleOperationScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType(self.scope.scope.entity_type())

    @override
    def scope_id(self) -> str:
        return str(self.scope.scope)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType(self.scope.scope.entity_type()),
            element_id=str(self.scope.scope),
        )


@dataclass
class SearchRolesInScopeActionResult(RoleScopeActionResult):
    result: SearchResult[RoleData]
    _scope_type: ScopeType
    _scope_id: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id
