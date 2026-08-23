from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.queriers import (
    BulkAppConfigAllowListQuerier,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow


@dataclass
class BulkGetAppConfigAllowListsAction(
    PartialBulkGetEntityOpsAction[AppConfigAllowListRow, AppConfigAllowListData]
):
    """Read the allow-list entries the caller named, answering for each id."""

    ids: Sequence[AppConfigAllowListID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_app_config_allow_lists"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkAppConfigAllowListQuerier:
        return BulkAppConfigAllowListQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
