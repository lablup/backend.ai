"""Update specs for vfolders."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.types import OptionalState


@dataclass
class VFolderAttributeUpdater(DataUpdater[VFolderRow, VFolderData]):
    """Edit a vfolder's name, cloneable flag and mount permission."""

    vfolder_id: VFolderUUID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    cloneable: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    mount_permission: OptionalState[VFolderMountPermission] = field(
        default_factory=OptionalState[VFolderMountPermission].nop
    )

    @property
    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def target_id_value(self) -> VFolderUUID:
        return self.vfolder_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.cloneable.update_dict(to_update, "cloneable")
        self.mount_permission.update_dict(to_update, "permission")
        return to_update

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()


@dataclass
class VFolderSoftDeleteUpdater(DataUpdater[VFolderRow, VFolderData]):
    """Moves a vfolder to the trash by setting its status to DELETE_PENDING."""

    vfolder_id: VFolderUUID

    @property
    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def target_id_value(self) -> VFolderUUID:
        return self.vfolder_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": VFolderOperationStatus.DELETE_PENDING}

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()
