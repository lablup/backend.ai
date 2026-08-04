from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_ALLOW_LIST_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.app_config_allow_list.queriers import (
    AppConfigAllowListQuerier,
)


@dataclass
class GetAppConfigAllowListAction(
    GetSingleEntityOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    querier: AppConfigAllowListQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_ALLOW_LIST_ENTITY_TYPE

    @override
    def entity_id(self) -> EntityID:
        return self.querier.allow_list_id

    @override
    def to_querier(self) -> AppConfigAllowListQuerier:
        return self.querier
