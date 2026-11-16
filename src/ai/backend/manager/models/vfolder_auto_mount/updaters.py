"""DataUpdater implementations for the vfolder auto-mount."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.manager.data.vfolder.types import VFolderMountPermission
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.vfolder_auto_mount import VFolderAutoMountDestinationInUse
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.searchable_fields import (
    VFolderAutoMountSearchableFields,
)
from ai.backend.manager.types import OptionalState

__all__ = ("VFolderAutoMountUpdater",)


@dataclass
class VFolderAutoMountUpdater(DataUpdater[VFolderAutoMountRow, VFolderAutoMountData]):
    """Changes where and how an auto-mounted vfolder is mounted."""

    vfolder_auto_mount_id: VFolderAutoMountID
    mount_destination: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    subpath: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    mount_permission: OptionalState[VFolderMountPermission] = field(
        default_factory=OptionalState[VFolderMountPermission].nop
    )

    @property
    @override
    def row_class(self) -> type[VFolderAutoMountRow]:
        return VFolderAutoMountRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderAutoMountRow.id

    @override
    def target_id_value(self) -> VFolderAutoMountID:
        return self.vfolder_auto_mount_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=VFolderAutoMountDestinationInUse(),
                constraint_name="uq_vfolder_auto_mounts_live_destination",
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.mount_destination.update_dict(to_update, "mount_destination")
        self.subpath.update_dict(to_update, "subpath")
        self.mount_permission.update_dict(to_update, "mount_permission")
        return to_update

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountSearchableFields.own.to_data(row)
