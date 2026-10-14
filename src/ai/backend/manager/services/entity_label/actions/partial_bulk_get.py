from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.queriers import BulkEntityLabelQuerier
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
)


@dataclass(frozen=True)
class PartialBulkGetEntityLabelAction(
    PartialBulkGetFieldOpsAction[EntityLabelID, RuntimeEntityID, EntityLabelRow, EntityLabelData]
):
    """Read several labels by id, answering per label through the entity each is on."""

    label_ids: Sequence[EntityLabelID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_get_entity_labels"

    @override
    def field_ids(self) -> Sequence[EntityLabelID]:
        return tuple(self.label_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkEntityLabelOwnerAction:
        return LookupBulkEntityLabelOwnerAction(label_ids=self.label_ids)

    @override
    def to_querier(self) -> BulkEntityLabelQuerier:
        return BulkEntityLabelQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[EntityLabelID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self, label_ids=[label_id for label_id in self.label_ids if label_id in allowed]
        )
