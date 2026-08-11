"""DataQuerier implementations for the object storage repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ObjectStorageQuerier(DataQuerier[ObjectStorageRow, ObjectStorageData]):
    storage_id: uuid.UUID

    @override
    def row_class(self) -> type[ObjectStorageRow]:
        return ObjectStorageRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.storage_id

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return row.to_dataclass()
