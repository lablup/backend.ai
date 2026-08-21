from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ObjectStoragePurger(EntityPurger[ObjectStorageRow, ObjectStorageData]):
    """Purger for removing an object storage registration."""

    storage_id: ObjectStorageID

    @override
    def row_class(self) -> type[ObjectStorageRow]:
        return ObjectStorageRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ObjectStorageRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.storage_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return row.to_dataclass()
