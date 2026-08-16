from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
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
    def action_name(cls) -> str:
        return "get_app_config_allow_list"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.querier.allow_list_id

    @override
    def to_querier(self) -> AppConfigAllowListQuerier:
        return self.querier
