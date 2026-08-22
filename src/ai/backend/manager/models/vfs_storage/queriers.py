"""DataQuerier implementations for the VFS storage repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


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
        return row.to_dataclass()
