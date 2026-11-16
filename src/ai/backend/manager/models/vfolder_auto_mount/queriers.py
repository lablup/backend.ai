from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.specs.querier import BulkEntityQuerier
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.searchable_fields import (
    VFolderAutoMountSearchableFields,
)


class BulkVFolderAutoMountQuerier(BulkEntityQuerier[VFolderAutoMountRow, VFolderAutoMountData]):
    """The auto-mounts the caller named, soft-deleted ones included."""

    @override
    def row_class(self) -> type[VFolderAutoMountRow]:
        return VFolderAutoMountRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderAutoMountRow.id

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountSearchableFields.own.to_data(row)
