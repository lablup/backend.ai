from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier, RuntimeEntityID
from ai.backend.manager.actions.v2.ops.base import PartialBulkUpsertFieldOpsAction
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_label.upserters import EntityLabelUpserter


@dataclass(frozen=True)
class EntityLabelToUpsert:
    """One key to put on one entity, as a bulk upsert names it."""

    owner: RuntimeEntityID
    upserter: EntityLabelUpserter


@dataclass(frozen=True)
class PartialBulkUpsertEntityLabelAction(
    PartialBulkUpsertFieldOpsAction[RuntimeEntityID, EntityLabelRow, EntityLabelData]
):
    """Set keys on the entities the caller named, answering per entity: an entity's
    keys are written together, so what fails a key is the entity it goes on."""

    items: Sequence[EntityLabelToUpsert]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_upsert_entity_labels"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(dict.fromkeys(item.owner for item in self.items))

    @override
    def to_upserters(self) -> Mapping[RuntimeEntityID, Sequence[EntityLabelUpserter]]:
        grouped: dict[RuntimeEntityID, list[EntityLabelUpserter]] = {}
        for item in self.items:
            grouped.setdefault(item.owner, []).append(item.upserter)
        return grouped

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, items=[item for item in self.items if item.owner in allowed])
