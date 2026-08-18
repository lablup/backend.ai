from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.purgers import (
    AppConfigAllowListPurger,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow


@dataclass
class PurgeAppConfigAllowListAction(
    PurgeEntityOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Remove a write gate from the global catalog.

    Global-shaped like the create: the allow list is superadmin-managed global
    state, so the SUPERADMIN gate answers for the purge as it does for the create.
    """

    purger: AppConfigAllowListPurger

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_app_config_allow_list"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> AppConfigAllowListPurger:
        return self.purger
