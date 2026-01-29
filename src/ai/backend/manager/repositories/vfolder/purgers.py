from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.models.vfolder.row import VFolderInvitationRow, VFolderPermissionRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec


@dataclass
class VFolderInvitationBatchPurgerSpec(BatchPurgerSpec[VFolderInvitationRow]):
    """PurgerSpec for deleting vfolder invitation rows."""

    vfolder_ids: Sequence[UUID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderInvitationRow]]:
        return sa.select(VFolderInvitationRow).where(
            VFolderInvitationRow.vfolder.in_(self.vfolder_ids)
        )


@dataclass
class VFolderPermissionBatchPurgerSpec(BatchPurgerSpec[VFolderPermissionRow]):
    """PurgerSpec for deleting vfolder permission rows."""

    vfolder_ids: Sequence[UUID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderPermissionRow]]:
        return sa.select(VFolderPermissionRow).where(
            VFolderPermissionRow.vfolder.in_(self.vfolder_ids)
        )
