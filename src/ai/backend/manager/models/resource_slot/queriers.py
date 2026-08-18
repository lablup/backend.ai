"""DataQuerier implementations for the resource slot repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ResourceSlotTypeQuerier(DataQuerier[ResourceSlotTypeRow, ResourceSlotTypeData]):
    slot_name: str

    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    def pk_value(self) -> str:
        return self.slot_name

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return row.to_data()
