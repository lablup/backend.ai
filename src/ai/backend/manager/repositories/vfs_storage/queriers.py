"""DataQuerier implementations for the VFS storage repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class VFSStorageQuerier(DataQuerier[VFSStorageRow, VFSStorageData]):
    storage_id: uuid.UUID

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.storage_id

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return row.to_dataclass()
