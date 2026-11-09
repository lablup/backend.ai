from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.purgers import ResourceSlotTypePurger
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow


@dataclass(frozen=True)
class PartialBulkPurgeResourceSlotTypesAction(
    PartialBulkPurgeEntityOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]
):
    """Remove the named resource slot types, answering for each one."""

    ids: Sequence[ResourceSlotTypeUUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_resource_slot_types"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, ResourceSlotTypePurger]:
        return {
            slot_type_id: ResourceSlotTypePurger(slot_type_id=slot_type_id)
            for slot_type_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, ids=[slot_type_id for slot_type_id in self.ids if slot_type_id in allowed]
        )
