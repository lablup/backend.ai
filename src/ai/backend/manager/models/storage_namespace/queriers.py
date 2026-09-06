"""Read specs for the storage namespace repository."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.querier import BulkEntityQuerier
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


class BulkStorageNamespaceQuerier(BulkEntityQuerier[StorageNamespaceRow, StorageNamespaceData]):
    """The storage namespaces the caller named."""

    @override
    def row_class(self) -> type[StorageNamespaceRow]:
        return StorageNamespaceRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return StorageNamespaceRow.id

    @override
    def to_data(self, row: StorageNamespaceRow) -> StorageNamespaceData:
        return row.to_dataclass()
