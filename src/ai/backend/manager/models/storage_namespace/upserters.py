from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.models.storage_namespace.searchable_fields import (
    StorageNamespaceSearchableFields,
)

__all__ = ("StorageNamespaceUpserter",)


@dataclass
class StorageNamespaceUpserter(
    CreatedInGlobal[StorageNamespaceRow], EntityUpserter[StorageNamespaceRow, StorageNamespaceData]
):
    """Write a storage namespace under its stated id. Conflict key: id.
    ``storage_id`` and ``namespace`` are written on insert only: the reservoir config
    looks the namespace up by its storage and bucket name."""

    id: StorageNamespaceID
    storage_id: ObjectStorageID
    namespace: str

    @override
    def entity_id(self, row: StorageNamespaceRow) -> StorageNamespaceID:
        return StorageNamespaceID(row.id)

    @override
    def row_class(self) -> type[StorageNamespaceRow]:
        return StorageNamespaceRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "storage_id": self.storage_id, "namespace": self.namespace}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {}

    @override
    def to_data(self, row: StorageNamespaceRow) -> StorageNamespaceData:
        return StorageNamespaceSearchableFields.own.to_data(row)
