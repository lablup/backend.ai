"""Delete specs for the rows a vfolder leaves behind."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.models.specs.purger import FieldBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfolder.row import (
    VFolderInvitationRow,
    VFolderPermissionRow,
)


@dataclass
class VFolderInvitationBatchPurger(FieldBatchPurger[VFolderInvitationRow, VFolderUUID]):
    """Clears the invitations of the vfolders going away.

    Invitations stand outside the RBAC graph, so nothing is torn down with them.
    """

    vfolder_ids: Sequence[UUID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderInvitationRow]]:
        return sa.select(VFolderInvitationRow).where(
            VFolderInvitationRow.vfolder.in_(self.vfolder_ids)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderInvitationRow) -> VFolderUUID:
        return row.id


@dataclass
class VFolderPermissionBatchPurger(FieldBatchPurger[VFolderPermissionRow, VFolderUUID]):
    """Clears the per-user permission rows of the vfolders going away.

    Permission rows stand outside the RBAC graph, so nothing is torn down with them.
    """

    vfolder_ids: Sequence[UUID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderPermissionRow]]:
        return sa.select(VFolderPermissionRow).where(
            VFolderPermissionRow.vfolder.in_(self.vfolder_ids)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderPermissionRow) -> VFolderUUID:
        return row.id


@dataclass
class VFolderUserPermissionBatchPurger(FieldBatchPurger[VFolderPermissionRow, VFolderUUID]):
    """Clears one user's mount permission on one vfolder."""

    vfolder_id: UUID
    user_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderPermissionRow]]:
        return sa.select(VFolderPermissionRow).where(
            (VFolderPermissionRow.vfolder == self.vfolder_id)
            & (VFolderPermissionRow.user == self.user_id)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderPermissionRow) -> VFolderUUID:
        return row.id
