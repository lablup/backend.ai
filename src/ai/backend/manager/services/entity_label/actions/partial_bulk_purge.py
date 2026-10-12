from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.actions.v2.field.ops import PartialBulkPurgeFieldOpsAction
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.purgers import EntityLabelPurger
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.services.entity_label.actions.lookup_owner import (
    LookupBulkEntityLabelOwnerAction,
)


@dataclass(frozen=True)
class PartialBulkPurgeEntityLabelAction(
    PartialBulkPurgeFieldOpsAction[EntityLabelID, RuntimeEntityID, EntityLabelRow, EntityLabelData]
):
    """Take several labels off, each named by its own id and answered for on its own.

    Which entity answers for each is what the bulk owner lookup reads first; a label
    whose entity the caller may not write is one failed item, not a failed run.
    """

    label_ids: Sequence[EntityLabelID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_entity_labels"

    @override
    def field_ids(self) -> Sequence[EntityLabelID]:
        return tuple(self.label_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkEntityLabelOwnerAction:
        return LookupBulkEntityLabelOwnerAction(label_ids=self.label_ids)

    @override
    def to_purgers(self) -> Mapping[EntityLabelID, EntityLabelPurger]:
        return {label_id: EntityLabelPurger(label_id=label_id) for label_id in self.label_ids}

    @override
    def narrowed_to(self, field_ids: Sequence[EntityLabelID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self, label_ids=[label_id for label_id in self.label_ids if label_id in allowed]
        )
