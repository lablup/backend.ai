from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.user.types import DomainUserSearchScope
from ai.backend.manager.services.user.actions.base import UserScopeAction, UserScopeActionResult


@dataclass
class SearchUsersByDomainAction(UserScopeAction):
    """Action for searching users within a domain."""

    scope: DomainUserSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.scope.domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.scope.domain_name)


@dataclass
class SearchUsersByDomainActionResult(UserScopeActionResult):
    """Result of searching users within a domain."""

    users: list[UserData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _domain_name: str

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name
