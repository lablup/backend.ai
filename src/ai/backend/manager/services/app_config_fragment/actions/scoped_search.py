"""Scoped app config fragment search action and its searchable targets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.app_config_fragment.types import (
    DomainAppConfigFragmentSearchScope,
    UserAppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass(frozen=True)
class DomainAppConfigFragmentTarget(SearchableActionTarget):
    """Scope item keyed by a domain — the fragments written at that domain scope."""

    domain_id: DomainID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(element_type=RBACElementType.DOMAIN, element_id=str(self.domain_id))

    @override
    def to_search_scope(self) -> SearchScope:
        return DomainAppConfigFragmentSearchScope(domain_id=self.domain_id)


@dataclass(frozen=True)
class UserAppConfigFragmentTarget(SearchableActionTarget):
    """Scope item keyed by a user — the fragments written at that user scope."""

    user_id: UserID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(element_type=RBACElementType.USER, element_id=str(self.user_id))

    @override
    def to_search_scope(self) -> SearchScope:
        return UserAppConfigFragmentSearchScope(user_id=self.user_id)


@dataclass
class ScopedSearchAppConfigFragmentAction(BaseBulkAction[SearchableActionTarget]):
    """Scoped path: search the fragments under the given domain/user scope targets."""

    items: list[SearchableActionTarget]
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_FRAGMENT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def targets(self) -> Sequence[SearchableActionTarget]:
        return list(self.items)


@dataclass
class ScopedSearchAppConfigFragmentActionResult(BaseBulkActionResult):
    items: list[AppConfigFragmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    queried_refs: list[RBACElementRef]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.queried_refs)
