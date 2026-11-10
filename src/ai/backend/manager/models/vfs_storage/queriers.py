"""DataQuerier implementations for the VFS storage repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.querier import BulkEntityQuerier, DataQuerier
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.vfs_storage.searchable_fields import (
    VFSStorageSearchableFields,
)


@dataclass
class VFSStorageQuerier(DataQuerier[VFSStorageRow, VFSStorageData]):
    storage_id: VFSStorageID

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return VFSStorageRow.id

    @override
    def entity_id_value(self) -> VFSStorageID:
        return self.storage_id

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return VFSStorageSearchableFields.own.to_data(row)


class BulkVFSStorageQuerier(BulkEntityQuerier[VFSStorageRow, VFSStorageData]):
    """The VFS storages the caller named."""

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return VFSStorageRow.id

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return VFSStorageSearchableFields.own.to_data(row)
