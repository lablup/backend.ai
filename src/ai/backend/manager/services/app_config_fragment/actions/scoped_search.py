"""Scoped app config fragment search action and its searchable targets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import ConfigNameSearchScope
from ai.backend.manager.repositories.base import BatchQuerier, SearchScope


@dataclass(frozen=True)
class ConfigNameTarget(SearchableActionTarget):
    """Scope item keyed by a single ``config_name`` — all of its fragments."""

    config_name: str

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG_FRAGMENT,
            element_id=self.config_name,
        )

    @override
    def to_search_scope(self) -> SearchScope:
        return ConfigNameSearchScope(config_name=self.config_name)


@dataclass
class ScopedSearchAppConfigFragmentAction(BaseBulkAction[SearchableActionTarget]):
    """Scoped path: search the fragments of the given ``config_name`` targets."""

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
    data: list[AppConfigFragmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    queried_refs: list[RBACElementRef]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.queried_refs)
