from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.queriers import (
    BulkAppConfigFragmentQuerier,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow


@dataclass
class BulkGetAppConfigFragmentsAction(
    PartialBulkGetEntityOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Read the config fragments the caller named, answering for each id."""

    ids: Sequence[AppConfigFragmentID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_app_config_fragments"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkAppConfigFragmentQuerier:
        return BulkAppConfigFragmentQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
