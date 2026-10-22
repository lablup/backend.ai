from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.queriers import BulkEntityShareQuerier
from ai.backend.manager.models.entity_share.row import EntityShareRow


@dataclass
class BulkGetEntitySharesAction(PartialBulkGetEntityOpsAction[EntityShareRow, EntityShareData]):
    """Read the entity shares the caller named, one permission check per share."""

    ids: Sequence[EntityShareID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_entity_shares"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkEntityShareQuerier:
        return BulkEntityShareQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
