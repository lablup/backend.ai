"""Read specs for vfolders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.vfolder.types import VFolderData, VFolderMountPolicyData
from ai.backend.manager.models.specs.querier import (
    BulkEntityQuerier,
    DataQuerier,
    OwnedFieldQuerier,
)
from ai.backend.manager.models.vfolder.row import VFolderRow, VFolderUserMountPolicyRow
from ai.backend.manager.models.vfolder.searchable_fields import (
    VFolderMountPolicySearchableFields,
    VFolderSearchableFields,
)


@dataclass
class VFolderQuerier(DataQuerier[VFolderRow, VFolderData]):
    """Reads one vfolder by id."""

    vfolder_id: VFolderUUID

    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def entity_id_value(self) -> VFolderUUID:
        return self.vfolder_id

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return VFolderSearchableFields.own.to_data(row)


class BulkVFolderQuerier(BulkEntityQuerier[VFolderRow, VFolderData]):
    """The vfolders the caller named, keyed by the id column."""

    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()


@dataclass
class VFolderUserMountPolicyQuerier(
    OwnedFieldQuerier[VFolderUUID, VFolderUserMountPolicyRow, VFolderMountPolicyData]
):
    """The mount policy row one user holds on each named folder."""

    user_id: UserID

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderUserMountPolicyRow).where(
            VFolderUserMountPolicyRow.user_id == self.user_id
        )

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderUserMountPolicyRow.vfolder_id

    @override
    def to_data(self, row: VFolderUserMountPolicyRow) -> VFolderMountPolicyData:
        return VFolderMountPolicySearchableFields.own.to_data(row)
