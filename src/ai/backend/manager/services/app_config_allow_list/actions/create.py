from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.app_config_allow_list.actions.base import (
    AppConfigAllowListScopeAction,
    AppConfigAllowListScopeActionResult,
)


@dataclass
class CreateAppConfigAllowListAction(AppConfigAllowListScopeAction):
    creator: Creator[AppConfigAllowListRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

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
class CreateAppConfigAllowListActionResult(AppConfigAllowListScopeActionResult):
    allow_list: AppConfigAllowListData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
