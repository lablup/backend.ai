from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_ALLOW_LIST_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.app_config_allow_list.creators import (
    AppConfigAllowListCreator,
)


@dataclass
class CreateAppConfigAllowListAction(
    CreateGlobalOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Register a write gate for one ``(config_name, scope_type)`` pair."""

    creator: AppConfigAllowListCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_ALLOW_LIST_ENTITY_TYPE

    @override
    def to_creator(self) -> AppConfigAllowListCreator:
        return self.creator
