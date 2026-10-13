from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.vfs_storage.searchable_fields import (
    VFSStorageSearchableFields,
)

__all__ = ("VFSStorageUpserter",)


@dataclass
class VFSStorageUpserter(
    CreatedInGlobal[VFSStorageRow], EntityUpserter[VFSStorageRow, VFSStorageData]
):
    """Write a VFS storage under its stated id. Conflict key: id.
    ``name`` is written on insert only: configs and artifact handlers look the storage
    up by it."""

    id: VFSStorageID
    name: str
    host: str
    base_path: str

    @override
    def entity_id(self, row: VFSStorageRow) -> VFSStorageID:
        return VFSStorageID(row.id)

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, **self.build_update_values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"host": self.host, "base_path": self.base_path}

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return VFSStorageSearchableFields.own.to_data(row)
