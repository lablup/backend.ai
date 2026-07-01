from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.app_config_allow_list.actions.base import (
    AppConfigAllowListScopeAction,
    AppConfigAllowListScopeActionResult,
)


@dataclass
class SearchAppConfigAllowListAction(AppConfigAllowListScopeAction):
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_ALLOW_LIST, "")


@dataclass
class SearchAppConfigAllowListActionResult(AppConfigAllowListScopeActionResult):
    data: list[AppConfigAllowListData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
