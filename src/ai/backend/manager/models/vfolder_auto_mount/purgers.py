from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.specs.purger import EntityBatchPurger, EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.searchable_fields import (
    VFolderAutoMountSearchableFields,
)


@dataclass
class VFolderAutoMountPurger(EntityPurger[VFolderAutoMountRow, VFolderAutoMountData]):
    """Remove one auto-mount, soft-deleted or not, with what it left in the graph."""

    auto_mount_id: VFolderAutoMountID

    @override
    def row_class(self) -> type[VFolderAutoMountRow]:
        return VFolderAutoMountRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderAutoMountRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.auto_mount_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountSearchableFields.own.to_data(row)


@dataclass
class VFolderAutoMountVFolderBatchPurger(
    EntityBatchPurger[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Remove every auto-mount of one vfolder, each with its graph.

    Runs before the vfolder's own purge: the FK cascade would take the rows first and
    leave their nodes behind.
    """

    vfolder_id: VFolderUUID

    @override
    def entity_id(self, row: VFolderAutoMountRow) -> VFolderAutoMountID:
        return row.id

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderAutoMountRow]]:
        return sa.select(VFolderAutoMountRow).where(
            VFolderAutoMountRow.vfolder_id == self.vfolder_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountSearchableFields.own.to_data(row)
