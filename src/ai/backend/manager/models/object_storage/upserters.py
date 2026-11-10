from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.object_storage.searchable_fields import (
    ObjectStorageSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("ObjectStorageUpserter",)


@dataclass
class ObjectStorageUpserter(
    CreatedInGlobal[ObjectStorageRow], EntityUpserter[ObjectStorageRow, ObjectStorageData]
):
    """Write an object storage under its stated id.

    Conflict key: id. ``name`` is written on insert only; the reservoir config refers to it.
    """

    id: ObjectStorageID
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str | None

    @override
    def entity_id(self, row: ObjectStorageRow) -> ObjectStorageID:
        return ObjectStorageID(row.id)

    @override
    def row_class(self) -> type[ObjectStorageRow]:
        return ObjectStorageRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, **self.build_update_values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "endpoint": self.endpoint,
            "region": self.region,
        }

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return ObjectStorageSearchableFields.own.to_data(row)
