from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_ALLOW_LIST_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.app_config_allow_list.searchers import (
    AppConfigAllowListSearcher,
)


@dataclass
class AdminSearchAppConfigAllowListAction(
    SearchGlobalOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Super-admin path: search every allow-list entry, across all scope types."""

    searcher: AppConfigAllowListSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_ALLOW_LIST_ENTITY_TYPE

    @override
    def to_searcher(self) -> AppConfigAllowListSearcher:
        return self.searcher
