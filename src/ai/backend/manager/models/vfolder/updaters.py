"""Update specs for vfolders."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.session import DEAD_SESSION_STATUSES, SessionRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater, GuardedDataUpdater
from ai.backend.manager.models.vfolder.conditions import VFolderConditions
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.types import OptionalState


@dataclass
class VFolderAttributeUpdater(GuardedDataUpdater[VFolderRow, VFolderData]):
    """Edit a vfolder's name, cloneable flag and mount permission; refuses while a
    purge is working through it."""

    vfolder_id: VFolderUUID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    cloneable: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    mount_permission: OptionalState[VFolderMountPermission] = field(
        default_factory=OptionalState[VFolderMountPermission].nop
    )

    @property
    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def target_id_value(self) -> VFolderUUID:
        return self.vfolder_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [VFolderConditions.not_being_purged()]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.cloneable.update_dict(to_update, "cloneable")
        self.mount_permission.update_dict(to_update, "permission")
        return to_update

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()


@dataclass
class VFolderSoftDeleteUpdater(DataUpdater[VFolderRow, VFolderData]):
    """Moves a vfolder to the trash by setting its status to DELETE_PENDING."""

    vfolder_id: VFolderUUID

    @property
    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def target_id_value(self) -> VFolderUUID:
        return self.vfolder_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": VFolderOperationStatus.DELETE_PENDING}

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()


@dataclass
class VFolderTrashUpdater(GuardedDataUpdater[VFolderRow, VFolderData]):
    """Moves a vfolder to the trash unless a live session still mounts it.

    ``mount_key`` is the folder's mount identifier as sessions record it, which pairs
    the quota scope with the folder id and so is read off the row rather than derived
    from its id.
    """

    vfolder_id: VFolderUUID
    mount_key: str

    @property
    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def target_id_value(self) -> VFolderUUID:
        return self.vfolder_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        def not_mounted() -> sa.sql.expression.ColumnElement[bool]:
            return sa.not_(
                sa.exists(
                    sa.select(sa.literal(1))
                    .select_from(SessionRow)
                    .where(
                        SessionRow.status.not_in(DEAD_SESSION_STATUSES),
                        SessionRow.vfolder_mounts.contains([{"vfid": self.mount_key}]),
                    )
                )
            )

        return [VFolderConditions.not_being_purged(), not_mounted]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": VFolderOperationStatus.DELETE_PENDING}

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()
