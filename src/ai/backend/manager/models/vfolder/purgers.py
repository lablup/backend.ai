"""Delete specs for the rows a vfolder leaves behind."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_mount_policy import VFolderMountPolicyID
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.specs.purger import (
    EntityPurger,
    FieldBatchPurger,
)
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfolder.row import (
    VFolderRow,
    VFolderUserMountPolicyRow,
)
from ai.backend.manager.models.vfolder.searchable_fields import (
    VFolderSearchableFields,
)


@dataclass
class VFolderPurger(EntityPurger[VFolderRow, VFolderData]):
    """Deletes one vfolder row and the RBAC graph it left.

    ``reference_checks`` carry the in-use guard (built from the purge-guard
    registry) so the guard and the delete share one statement sequence; a forced
    purge passes none.
    """

    vfolder_id: VFolderUUID
    reference_checks: Sequence[ConflictCheck] = ()

    @override
    def entity_id(self) -> VFolderUUID:
        return self.vfolder_id

    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return self.reference_checks

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return VFolderSearchableFields.own.to_data(row)


@dataclass
class VFolderUserMountPolicyBatchPurger(
    FieldBatchPurger[VFolderUUID, VFolderUserMountPolicyRow, VFolderMountPolicyID]
):
    """Unset the mount level one user was given on one vfolder."""

    user_id: UUID

    @override
    def build_subquery(
        self, owner_id: VFolderUUID
    ) -> sa.sql.Select[tuple[VFolderUserMountPolicyRow]]:
        return sa.select(VFolderUserMountPolicyRow).where(
            VFolderUserMountPolicyRow.vfolder_id == owner_id,
            VFolderUserMountPolicyRow.user_id == self.user_id,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderUserMountPolicyRow) -> VFolderMountPolicyID:
        return VFolderMountPolicyID(row.id)
