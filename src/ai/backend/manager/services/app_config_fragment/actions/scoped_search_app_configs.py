"""Scoped merged-view (AppConfig) search action and its searchable targets."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import UserAppConfigSearchScope
from ai.backend.manager.repositories.base import BatchQuerier, SearchScope


@dataclass(frozen=True)
class UserAppConfigTarget(SearchableActionTarget):
    """Scope item keyed by a target ``user_id`` in the merged view."""

    user_id: uuid.UUID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.user_id),
        )

    @override
    def to_search_scope(self) -> SearchScope:
        return UserAppConfigSearchScope(user_id=self.user_id)


@dataclass
class ScopedSearchAppConfigsAction(BaseBulkAction[SearchableActionTarget]):
    """Scoped merged-view search; targets are OR'd and RBAC-gated per target."""

    items: list[SearchableActionTarget]
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def targets(self) -> Sequence[SearchableActionTarget]:
        return list(self.items)


@dataclass
class ScopedSearchAppConfigsActionResult(BaseBulkActionResult):
    items: list[AppConfigData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    queried_refs: list[RBACElementRef]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.queried_refs)
