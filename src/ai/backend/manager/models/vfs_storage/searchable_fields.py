"""What a VFS storage search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from pathlib import Path
from typing import override

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


class _VFSStorageOwnFields(RowDataConverter[VFSStorageRow, VFSStorageData]):
    """The VFS storage's own columns."""

    id = SearchableField(
        VFSStorageRow.id, UUIDConditions(VFSStorageRow.id), ColumnOrder(VFSStorageRow.id)
    )
    name = SearchableField(
        VFSStorageRow.name, StringConditions(VFSStorageRow.name), ColumnOrder(VFSStorageRow.name)
    )
    host = SearchableField(
        VFSStorageRow.host, StringConditions(VFSStorageRow.host), ColumnOrder(VFSStorageRow.host)
    )
    base_path = SearchableField(
        VFSStorageRow.base_path,
        StringConditions(VFSStorageRow.base_path),
        ColumnOrder(VFSStorageRow.base_path),
    )

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return VFSStorageData(
            id=VFSStorageID(self.id.read(row)),
            name=self.name.read(row),
            host=self.host.read(row),
            base_path=Path(self.base_path.read(row)),
        )


class VFSStorageSearchableFields:
    own = _VFSStorageOwnFields()
