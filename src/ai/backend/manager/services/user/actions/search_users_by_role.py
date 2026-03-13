from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.user.types import RoleUserSearchScope
from ai.backend.manager.services.user.actions.base import UserScopeAction, UserScopeActionResult


@dataclass
class SearchUsersByRoleAction(UserScopeAction):
    """Action for searching users assigned to a role."""

    scope: RoleUserSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.ROLE

    @override
    def scope_id(self) -> str:
        return str(self.scope.role_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ROLE, str(self.scope.role_id))


@dataclass
class SearchUsersByRoleActionResult(UserScopeActionResult):
    """Result of searching users assigned to a role."""

    users: list[UserData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _scope_type: ScopeType
    _scope_id: str

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id
