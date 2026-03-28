from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.user.types import AssignableUserSearchScope
from ai.backend.manager.services.user.actions.base import UserScopeAction


@dataclass
class SearchAssignableUsersAction(UserScopeAction):
    scope: AssignableUserSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.scope.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.scope.project_id))


@dataclass
class SearchAssignableUsersActionResult(BaseActionResult):
    users: list[UserData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
