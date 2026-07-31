from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base import Purger
from ai.backend.manager.services.app_config_allow_list.actions.base import (
    AppConfigAllowListSingleEntityAction,
    AppConfigAllowListSingleEntityActionResult,
)


@dataclass
class PurgeAppConfigAllowListAction(AppConfigAllowListSingleEntityAction):
    purger: Purger[AppConfigAllowListRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        return str(self.purger.spec.pk_value())

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            RBACElementType.APP_CONFIG_ALLOW_LIST, str(self.purger.spec.pk_value())
        )


@dataclass
class PurgeAppConfigAllowListActionResult(AppConfigAllowListSingleEntityActionResult):
    allow_list: AppConfigAllowListData

    @override
    def target_entity_id(self) -> str:
        return str(self.allow_list.id)
