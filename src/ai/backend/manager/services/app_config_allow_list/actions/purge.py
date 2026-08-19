from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_ALLOW_LIST_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeGlobalOpsAction
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.purgers import (
    AppConfigAllowListPurger,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow


@dataclass
class PurgeAppConfigAllowListAction(
    PurgeGlobalOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Remove a write gate from the global catalog.

    Global-shaped like the create: the allow list is superadmin-managed global
    state, so the SUPERADMIN gate answers for the purge as it does for the create.
    """

    purger: AppConfigAllowListPurger

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_ALLOW_LIST_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_app_config_allow_list"

    @override
    def to_purger(self) -> AppConfigAllowListPurger:
        return self.purger
