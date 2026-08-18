"""DataLookup implementations for the resource slot repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ResourceSlotTypeLookup(DataLookup[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """Resolves a slot name into the type it names."""

    slot_name: str

    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ResourceSlotTypeRow.slot_name == self.slot_name]

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return row.to_data()
