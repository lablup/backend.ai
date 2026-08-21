"""DataLookup implementations for the resource slot repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ResourceSlotTypeLookup(DataLookup[ResourceSlotTypeRow, ResourceSlotTypeUUID]):
    """Resolves a slot name into the type it names."""

    slot_name: str

    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ResourceSlotTypeRow.slot_name == self.slot_name]

    @override
    def to_entity_id(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeUUID:
        return row.uuid
