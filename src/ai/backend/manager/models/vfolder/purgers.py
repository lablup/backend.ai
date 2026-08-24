"""Delete specs for the rows a vfolder leaves behind."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_invitation import VFolderInvitationID
from ai.backend.common.data.entity.vfolder_permission import VFolderPermissionID
from ai.backend.manager.models.specs.purger import EntityBatchPurger, FieldBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfolder.row import (
    VFolderInvitationRow,
    VFolderPermissionRow,
)


@dataclass
class VFolderInvitationBatchPurger(EntityBatchPurger[VFolderInvitationRow, VFolderInvitationID]):
    """Clears the invitations of the vfolders going away, each with its graph.

    An invitation is an entity of its own — the invitee acts on it while holding no
    permission on the folder — so what it left in the graph goes with it.
    """

    vfolder_ids: Sequence[UUID]

    @override
    def entity_id(self, row: VFolderInvitationRow) -> VFolderInvitationID:
        return VFolderInvitationID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderInvitationRow]]:
        return sa.select(VFolderInvitationRow).where(
            VFolderInvitationRow.vfolder.in_(self.vfolder_ids)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderInvitationRow) -> VFolderInvitationID:
        return VFolderInvitationID(row.id)


@dataclass
class VFolderPermissionBatchPurger(
    FieldBatchPurger[VFolderUUID, VFolderPermissionRow, VFolderPermissionID]
):
    """Clears the per-user permission rows of the vfolders going away.

    Permission rows stand outside the RBAC graph, so nothing is torn down with them.
    """

    @override
    def build_subquery(self, owner_id: VFolderUUID) -> sa.sql.Select[tuple[VFolderPermissionRow]]:
        return sa.select(VFolderPermissionRow).where(VFolderPermissionRow.vfolder == owner_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderPermissionRow) -> VFolderPermissionID:
        return VFolderPermissionID(row.id)


@dataclass
class VFolderUserPermissionBatchPurger(
    FieldBatchPurger[VFolderUUID, VFolderPermissionRow, VFolderPermissionID]
):
    """Clears one user's mount permission on one vfolder."""

    user_id: UUID

    @override
    def build_subquery(self, owner_id: VFolderUUID) -> sa.sql.Select[tuple[VFolderPermissionRow]]:
        return sa.select(VFolderPermissionRow).where(
            (VFolderPermissionRow.vfolder == owner_id) & (VFolderPermissionRow.user == self.user_id)
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderPermissionRow) -> VFolderPermissionID:
        return VFolderPermissionID(row.id)
