from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.services.app_config_allow_list.actions.base import (
    AppConfigAllowListSingleEntityAction,
    AppConfigAllowListSingleEntityActionResult,
)


@dataclass
class UpdateAppConfigAllowListAction(AppConfigAllowListSingleEntityAction):
    """Update an allow-list entry's ``rank`` (admin-only re-ordering of the merge).

    The identity pair (``config_name``, ``scope_type``) is immutable — changing it
    means purging the entry (which cascades to its fragments) and creating a new one.
    """

    updater: Updater[AppConfigAllowListRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_ALLOW_LIST, str(self.updater.pk_value))


@dataclass
class UpdateAppConfigAllowListActionResult(AppConfigAllowListSingleEntityActionResult):
    allow_list: AppConfigAllowListData

    @override
    def target_entity_id(self) -> str:
        return str(self.allow_list.id)
