from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ObjectStoragePurger(GlobalEntityPurger[ObjectStorageRow, ObjectStorageData]):
    """Purger for removing an object storage registration."""

    storage_id: uuid.UUID

    @override
    def row_class(self) -> type[ObjectStorageRow]:
        return ObjectStorageRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.storage_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return row.to_dataclass()
