"""DataQuerier implementations for the resource slot repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ResourceSlotTypeQuerier(DataQuerier[ResourceSlotTypeRow, ResourceSlotTypeData]):
    uuid: ResourceSlotTypeUUID

    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ResourceSlotTypeRow.uuid

    @override
    def entity_id_value(self) -> ResourceSlotTypeUUID:
        return self.uuid

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return row.to_data()
