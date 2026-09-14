from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.app_config.types import AppConfigAllowListData


@dataclass(frozen=True)
class PurgeAppConfigAllowListAction(BaseSingleEntityAction):
    """Remove a write gate from the global catalog. The fragments the database cascades
    to are cleared in the same transaction, which is why this does not run straight
    against ops."""

    allow_list_id: AppConfigAllowListID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.allow_list_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_app_config_allow_list"


@dataclass(frozen=True)
class PurgeAppConfigAllowListActionResult:
    allow_list_data: AppConfigAllowListData
