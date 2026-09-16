"""Lookup implementations for vfolders and their mount policy rows."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType, FieldType
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.entity.vfolder_mount_policy import VFolderMountPolicyID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.lookup import DataLookup, FieldKeyLookup
from ai.backend.manager.models.vfolder.row import (
    VFolderRow,
    VFolderStatusSet,
    VFolderUserMountPolicyRow,
    vfolder_status_map,
)

__all__ = (
    "VFolderMountPolicyLookup",
    "VFolderNameLookup",
)


@dataclass
class VFolderNameLookup(DataLookup[VFolderRow, VFolderUUID]):
    """Resolves a folder name within the scopes, combined with OR, into the folder it names.

    Inaccessible folders are left out, so a name freed by a deleted folder resolves to
    the live one.
    """

    scopes: Sequence[OperationScope]
    name: str

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
            lambda: sa.or_(*(scope.to_condition()() for scope in self.scopes)),
        ]

    @override
    def to_entity_id(self, row: VFolderRow) -> VFolderUUID:
        return VFolderUUID(row.id)


@dataclass
class VFolderMountPolicyLookup(FieldKeyLookup[VFolderMountPolicyID, VFolderUUID]):
    """Resolves a folder and a user into the mount policy row standing between them."""

    vfolder_id: VFolderUUID
    user_id: uuid.UUID

    @override
    def field_type(self) -> FieldType:
        return VFolderMountPolicyID.field_type()

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderUserMountPolicyRow.id, VFolderUserMountPolicyRow.vfolder_id).where(
            VFolderUserMountPolicyRow.vfolder_id == self.vfolder_id,
            VFolderUserMountPolicyRow.user_id == self.user_id,
        )

    @override
    def to_field_id(self, value: UUID) -> VFolderMountPolicyID:
        return VFolderMountPolicyID(value)

    @override
    def to_entity_id(self, value: UUID) -> VFolderUUID:
        return VFolderUUID(value)
