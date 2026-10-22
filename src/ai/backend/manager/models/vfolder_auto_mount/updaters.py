"""Update specs for vfolder auto-mounts."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.searchable_fields import (
    VFolderAutoMountSearchableFields,
)

__all__ = (
    "VFolderAutoMountRestoreUpdater",
    "VFolderAutoMountSoftDeleteUpdater",
)


@dataclass
class _VFolderAutoMountDeletedAtUpdater(
    DataUpdater[VFolderAutoMountRow, VFolderAutoMountData], ABC
):
    auto_mount_id: VFolderAutoMountID

    @property
    @override
    def row_class(self) -> type[VFolderAutoMountRow]:
        return VFolderAutoMountRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderAutoMountRow.id

    @override
    def target_id_value(self) -> VFolderAutoMountID:
        return self.auto_mount_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountSearchableFields.own.to_data(row)


@dataclass
class VFolderAutoMountSoftDeleteUpdater(_VFolderAutoMountDeletedAtUpdater):
    """Soft-delete an auto-mount; its graph stays so it can be restored."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted_at": sa.func.now()}


@dataclass
class VFolderAutoMountRestoreUpdater(_VFolderAutoMountDeletedAtUpdater):
    """Bring a soft-deleted auto-mount back."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"deleted_at": None}
