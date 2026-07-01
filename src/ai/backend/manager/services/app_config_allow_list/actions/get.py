from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_allow_list.actions.base import (
    AppConfigAllowListSingleEntityAction,
    AppConfigAllowListSingleEntityActionResult,
)


@dataclass
class GetAppConfigAllowListAction(AppConfigAllowListSingleEntityAction):
    allow_list_id: AppConfigAllowListID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.allow_list_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_ALLOW_LIST, str(self.allow_list_id))


@dataclass
class GetAppConfigAllowListActionResult(AppConfigAllowListSingleEntityActionResult):
    allow_list: AppConfigAllowListData

    @override
    def target_entity_id(self) -> str:
        return str(self.allow_list.id)
