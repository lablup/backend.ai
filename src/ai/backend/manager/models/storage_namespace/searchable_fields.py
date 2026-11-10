"""What a storage namespace search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


class _StorageNamespaceOwnFields(RowDataConverter[StorageNamespaceRow, StorageNamespaceData]):
    """The storage namespace's own columns."""

    id = SearchableField(
        StorageNamespaceRow.id,
        UUIDConditions(StorageNamespaceRow.id),
        ColumnOrder(StorageNamespaceRow.id),
    )
    storage_id = SearchableField(
        StorageNamespaceRow.storage_id,
        UUIDConditions(StorageNamespaceRow.storage_id),
        ColumnOrder(StorageNamespaceRow.storage_id),
    )
    namespace = SearchableField(
        StorageNamespaceRow.namespace,
        StringConditions(StorageNamespaceRow.namespace),
        ColumnOrder(StorageNamespaceRow.namespace),
    )

    @override
    def to_data(self, row: StorageNamespaceRow) -> StorageNamespaceData:
        return StorageNamespaceData(
            id=StorageNamespaceID(self.id.read(row)),
            storage_id=ObjectStorageID(self.storage_id.read(row)),
            namespace=self.namespace.read(row),
        )


class StorageNamespaceSearchableFields:
    own = _StorageNamespaceOwnFields()
