"""DataLookup implementations for the VFS storage repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class VFSStorageLookup(DataLookup[VFSStorageRow, VFSStorageID]):
    """Resolves a VFS storage's name into the row it names."""

    name: str

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: VFSStorageRow.name == self.name]

    @override
    def to_entity_id(self, row: VFSStorageRow) -> VFSStorageID:
        return row.id
