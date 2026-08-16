from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_allow_list.updaters import (
    AppConfigAllowListUpdater,
)


@dataclass
class UpdateAppConfigAllowListAction(
    UpdateSingleEntityOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Update an allow-list entry's ``rank`` (admin-only re-ordering of the merge).

    The identity pair (``config_name``, ``scope_type``) is immutable — changing it
    means purging the entry (which cascades to its fragments) and creating a new one.
    """

    updater: AppConfigAllowListUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_app_config_allow_list"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.allow_list_id

    @override
    def to_updater(self) -> AppConfigAllowListUpdater:
        return self.updater
