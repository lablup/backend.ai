"""DataLookup implementations for the VFS storage repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class VFSStorageByName(DataLookup[VFSStorageRow, VFSStorageData]):
    """Resolves a VFS storage's name into the row it names."""

    name: str

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: VFSStorageRow.name == self.name]

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return row.to_dataclass()
