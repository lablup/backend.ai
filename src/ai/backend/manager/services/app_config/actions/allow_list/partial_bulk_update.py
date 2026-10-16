from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_allow_list.updaters import (
    AppConfigAllowListUpdater,
)


@dataclass(frozen=True)
class PartialBulkUpdateAppConfigAllowListsAction(
    UpdatePartialBulkOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Re-rank the named allow-list entries, answering for each one."""

    updaters: Sequence[AppConfigAllowListUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_app_config_allow_lists"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.allow_list_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, AppConfigAllowListUpdater]:
        return {updater.allow_list_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            updaters=[updater for updater in self.updaters if updater.allow_list_id in allowed],
        )
