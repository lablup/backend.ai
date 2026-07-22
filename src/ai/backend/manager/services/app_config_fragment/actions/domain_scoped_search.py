from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import (
    DomainAppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentScopeAction,
    AppConfigFragmentScopeActionResult,
)


@dataclass
class DomainScopedSearchAppConfigFragmentAction(AppConfigFragmentScopeAction):
    """Search the fragments written at one domain scope.

    RBAC validation checks that the caller holds READ permission in that DOMAIN scope.
    """

    scope: DomainAppConfigFragmentSearchScope
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
        return str(self.scope.domain_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.DOMAIN,
            element_id=str(self.scope.domain_id),
        )


@dataclass
class DomainScopedSearchAppConfigFragmentActionResult(AppConfigFragmentScopeActionResult):
    domain_id: DomainID
    data: list[AppConfigFragmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return str(self.domain_id)
