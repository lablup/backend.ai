"""DataQuerier implementations for the object storage repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ObjectStorageQuerier(DataQuerier[ObjectStorageRow, ObjectStorageData]):
    storage_id: ObjectStorageID

    @override
    def row_class(self) -> type[ObjectStorageRow]:
        return ObjectStorageRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ObjectStorageRow.id

    @override
    def entity_id_value(self) -> ObjectStorageID:
        return self.storage_id

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return row.to_dataclass()
