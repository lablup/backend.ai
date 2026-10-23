"""What a vfolder auto-mount search can filter and order by, and how its row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.manager.data.vfolder.types import VFolderMountPermission
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow


class _VFolderAutoMountOwnFields(RowDataConverter[VFolderAutoMountRow, VFolderAutoMountData]):
    """The auto-mount's own columns."""

    id = SearchableField(
        VFolderAutoMountRow.id,
        UUIDConditions(VFolderAutoMountRow.id),
        ColumnOrder(VFolderAutoMountRow.id),
    )
    scope_type = SearchableField(
        VFolderAutoMountRow.scope_type,
        EnumConditions(VFolderAutoMountRow.scope_type, VFolderAutoMountScopeType),
        ColumnOrder(VFolderAutoMountRow.scope_type),
    )
    scope_id = SearchableField(
        VFolderAutoMountRow.scope_id,
        UUIDConditions(VFolderAutoMountRow.scope_id),
        ColumnOrder(VFolderAutoMountRow.scope_id),
    )
    vfolder_id = SearchableField(
        VFolderAutoMountRow.vfolder_id,
        UUIDConditions(VFolderAutoMountRow.vfolder_id),
        ColumnOrder(VFolderAutoMountRow.vfolder_id),
    )
    mount_destination = SearchableField(
        VFolderAutoMountRow.mount_destination,
        StringConditions(VFolderAutoMountRow.mount_destination),
        ColumnOrder(VFolderAutoMountRow.mount_destination),
    )
    subpath = SearchableField(VFolderAutoMountRow.subpath, None, None)
    mount_permission = SearchableField(
        VFolderAutoMountRow.mount_permission,
        EnumConditions(VFolderAutoMountRow.mount_permission, VFolderMountPermission),
        None,
    )
    created_at = SearchableField(
        VFolderAutoMountRow.created_at,
        DateTimeConditions(VFolderAutoMountRow.created_at),
        ColumnOrder(VFolderAutoMountRow.created_at),
    )
    updated_at = SearchableField(
        VFolderAutoMountRow.updated_at,
        DateTimeConditions(VFolderAutoMountRow.updated_at),
        ColumnOrder(VFolderAutoMountRow.updated_at),
    )
    deleted_at = SearchableField(
        VFolderAutoMountRow.deleted_at,
        DateTimeConditions(VFolderAutoMountRow.deleted_at),
        ColumnOrder(VFolderAutoMountRow.deleted_at),
    )

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountData(
            id=self.id.read(row),
            scope=RuntimeEntityID(EntityType(self.scope_type.read(row)), self.scope_id.read(row)),
            vfolder_id=self.vfolder_id.read(row),
            mount_destination=self.mount_destination.read(row),
            subpath=self.subpath.read(row),
            mount_permission=self.mount_permission.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
            deleted_at=self.deleted_at.read(row),
        )


class VFolderAutoMountSearchableFields:
    own = _VFolderAutoMountOwnFields()
