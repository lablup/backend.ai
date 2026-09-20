from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow


@dataclass(frozen=True)
class AdminSearchAppConfigAllowListAction(
    GlobalSearcherOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Super-admin path: search every allow-list entry, across all scope types."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AppConfigAllowListEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_search_app_config_allow_lists"
