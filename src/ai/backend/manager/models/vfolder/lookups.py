"""Lookup implementations for the vfolder_permissions table, a field of its vfolder."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import FieldType
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_permission import VFolderPermissionID
from ai.backend.manager.models.specs.lookup import FieldKeyLookup
from ai.backend.manager.models.vfolder.row import VFolderPermissionRow

__all__ = ("VFolderMountPermissionLookup",)


@dataclass
class VFolderMountPermissionLookup(FieldKeyLookup[VFolderPermissionID, VFolderUUID]):
    """Reads the mount permission one user holds on a vfolder, and the folder owning it.

    Callers hold the pair, never the row's id, so the pair has to become one before an
    update can name the row.
    """

    vfolder_id: VFolderUUID
    user_id: uuid.UUID

    @override
    def field_type(self) -> FieldType:
        return VFolderPermissionID.field_type()

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderPermissionRow.id, VFolderPermissionRow.vfolder).where(
            VFolderPermissionRow.vfolder == self.vfolder_id,
            VFolderPermissionRow.user == self.user_id,
        )

    @override
    def to_field_id(self, value: UUID) -> VFolderPermissionID:
        return VFolderPermissionID(value)

    @override
    def to_entity_id(self, value: UUID) -> VFolderUUID:
        return VFolderUUID(value)
