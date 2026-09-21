"""What an object storage search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ObjectStorageOwnFields(RowDataConverter[ObjectStorageRow, ObjectStorageData]):
    """The object storage's own columns."""

    id = SearchableField(
        ObjectStorageRow.id,
        UUIDConditions(ObjectStorageRow.id),
        ColumnOrder(ObjectStorageRow.id),
    )
    name = SearchableField(
        ObjectStorageRow.name,
        StringConditions(ObjectStorageRow.name),
        ColumnOrder(ObjectStorageRow.name),
    )
    host = SearchableField(
        ObjectStorageRow.host,
        StringConditions(ObjectStorageRow.host),
        ColumnOrder(ObjectStorageRow.host),
    )
    access_key = SearchableField(
        ObjectStorageRow.access_key,
        StringConditions(ObjectStorageRow.access_key),
        ColumnOrder(ObjectStorageRow.access_key),
    )
    secret_key = SearchableField(ObjectStorageRow.secret_key, None, None)
    """Sensitive: the plaintext secret the manager authenticates to the storage with."""
    endpoint = SearchableField(
        ObjectStorageRow.endpoint,
        StringConditions(ObjectStorageRow.endpoint),
        ColumnOrder(ObjectStorageRow.endpoint),
    )
    region = SearchableField(
        ObjectStorageRow.region,
        StringConditions(ObjectStorageRow.region),
        ColumnOrder(ObjectStorageRow.region),
    )

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return ObjectStorageData(
            id=ObjectStorageID(self.id.read(row)),
            name=self.name.read(row),
            host=self.host.read(row),
            access_key=self.access_key.read(row),
            secret_key=self.secret_key.read(row),
            endpoint=self.endpoint.read(row),
            region=self.region.read(row),
        )


class ObjectStorageSearchableFields:
    own = _ObjectStorageOwnFields()
