"""Lookup implementations for vfolders and the vfolder_permissions table."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType, FieldType
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.entity.vfolder_permission import VFolderPermissionID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.lookup import DataLookup, FieldKeyLookup
from ai.backend.manager.models.vfolder.row import (
    VFolderPermissionRow,
    VFolderRow,
    VFolderStatusSet,
    vfolder_status_map,
)

__all__ = (
    "VFolderMountPermissionLookup",
    "VFolderNameLookup",
)


@dataclass
class VFolderNameLookup(DataLookup[VFolderRow, VFolderUUID]):
    """Resolves a folder name within one scope into the folder it names.

    Inaccessible folders are left out, so a name freed by a deleted folder resolves to
    the live one.
    """

    name: str
    scope: OperationScope

    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def entity_type(self) -> EntityType:
        return VFolderEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: VFolderRow.name == self.name,
            lambda: VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE]),
            self.scope.to_condition(),
        ]

    @override
    def to_entity_id(self, row: VFolderRow) -> VFolderUUID:
        return VFolderUUID(row.id)


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
