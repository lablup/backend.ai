from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.permission_controller.types import ScopedRoleSearchScope
from ai.backend.manager.services.permission_contoller.actions.base import (
    RoleScopeAction,
    RoleScopeActionResult,
)


@dataclass
class SearchRolesInScopeAction(RoleScopeAction):
    scope: ScopedRoleSearchScope
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
        return self.scope.element_type.to_scope_type()

    @override
    def scope_id(self) -> str:
        return self.scope.scope_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=self.scope.element_type,
            element_id=self.scope.scope_id,
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
