from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class VFSStorageCreator(GlobalEntityCreator[VFSStorageRow, VFSStorageData]):
    """Creator for a VFS storage registration."""

    name: str
    host: str
    base_path: str

    @override
    def entity_id(self, row: VFSStorageRow) -> VFSStorageID:
        return VFSStorageID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> VFSStorageRow:
        return VFSStorageRow(name=self.name, host=self.host, base_path=self.base_path)

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return row.to_dataclass()
