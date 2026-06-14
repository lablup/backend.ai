"""Scoped app-config-policy search action and its searchable targets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_policy.types import (
    ConfigNameAppConfigPolicySearchScope,
)
from ai.backend.manager.repositories.base import BatchQuerier, SearchScope


@dataclass(frozen=True)
class ConfigNameAppConfigPolicyTarget(SearchableActionTarget):
    """Scope item keyed by a policy ``config_name``."""

    config_name: str

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG_POLICY,
            element_id=self.config_name,
        )

    @override
    def to_search_scope(self) -> SearchScope:
        return ConfigNameAppConfigPolicySearchScope(config_name=self.config_name)


@dataclass
class ScopedSearchAppConfigPoliciesAction(BaseBulkAction[SearchableActionTarget]):
    items: list[SearchableActionTarget]
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def targets(self) -> Sequence[SearchableActionTarget]:
        return list(self.items)


@dataclass
class ScopedSearchAppConfigPoliciesActionResult(BaseBulkActionResult):
    items: list[AppConfigPolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    queried_refs: list[RBACElementRef]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.queried_refs)
