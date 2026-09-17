"""Upsert specs for the vfolder repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from asyncpg.exceptions import ForeignKeyViolationError

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.data.vfolder.types import VFolderMountPolicyData
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter
from ai.backend.manager.models.vfolder.row import VFolderUserMountPolicyRow

__all__ = ("VFolderUserMountPolicyUpserter",)


@dataclass
class VFolderUserMountPolicyUpserter(
    FieldUpserter[VFolderUUID, VFolderUserMountPolicyRow, VFolderMountPolicyData]
):
    """Set the mount level one user gets on the folder, replacing what stood.

    An upsert because a user holds one level on a folder: naming a user again restates
    it rather than adding a second row.
    """

    user_id: UserID
    permission: VFolderMountPolicy

    @override
    def row_class(self) -> type[VFolderUserMountPolicyRow]:
        return VFolderUserMountPolicyRow

    @override
    def index_elements(self) -> list[str]:
        return ["vfolder_id", "user_id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=VFolderNotFound(),
            ),
        )

    @override
    def build_insert_values(self, owner_id: VFolderUUID) -> dict[str, Any]:
        return {
            "vfolder_id": owner_id,
            "user_id": self.user_id,
            "permission": self.permission,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"permission": self.permission, "updated_at": sa.func.now()}

    @override
    def to_data(self, row: VFolderUserMountPolicyRow) -> VFolderMountPolicyData:
        return row.to_data()
