from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, RuntimeEntityID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder_auto_mount.types import (
    VFolderAutoMountData,
    VFolderAutoMountSpec,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.errors.vfolder_auto_mount import (
    VFolderAutoMountAlreadyExists,
    VFolderAutoMountVFolderOutsideScope,
)
from ai.backend.manager.models.specs.creator import GuardedEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.searchable_fields import (
    VFolderAutoMountSearchableFields,
)


@dataclass(frozen=True)
class VFolderAutoMountCreator(GuardedEntityCreator[VFolderAutoMountRow, VFolderAutoMountData]):
    """Add one vfolder to the auto-mounts of a project or a user; the vfolder must belong to it.

    The row carries the scope; the own and govern edges are derived from it.
    """

    scope: EntityIdentifier
    spec: VFolderAutoMountSpec

    @override
    def entity_id(self, row: VFolderAutoMountRow) -> VFolderAutoMountID:
        return row.id

    @override
    def created_in(self, row: VFolderAutoMountRow) -> Collection[EntityIdentifier]:
        return (RuntimeEntityID(EntityType(row.scope_type), row.scope_id),)

    def _vfolder_outside_scope(self) -> sa.ColumnElement[bool]:
        match VFolderAutoMountScopeType.of_owner(self.scope):
            case VFolderAutoMountScopeType.PROJECT:
                return VFolderRow.group.is_distinct_from(self.scope)
            case VFolderAutoMountScopeType.USER:
                return VFolderRow.user.is_distinct_from(self.scope)

    @override
    def precondition_checks(self) -> Sequence[PreconditionCheck]:
        return (
            PreconditionCheck(
                finder=sa.select(VFolderRow.id).where(
                    VFolderRow.id == self.spec.vfolder_id,
                    self._vfolder_outside_scope(),
                ),
                error=VFolderAutoMountVFolderOutsideScope(),
            ),
        )

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        already_exists = VFolderAutoMountAlreadyExists()
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=already_exists,
                constraint_name="uq_vfolder_auto_mounts_live_vfolder",
            ),
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=already_exists,
                constraint_name="uq_vfolder_auto_mounts_live_destination",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=VFolderNotFound(),
                constraint_name="fk_vfolder_auto_mounts_vfolder_id_vfolders",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=EntityNotFoundError(
                    entity_type=self.scope.entity_type(), operation=ActionOperationType.CREATE
                ),
                constraint_name="fk_vfolder_auto_mounts_scope_type_virtual_entities",
            ),
        )

    @override
    def build_row(self) -> VFolderAutoMountRow:
        return VFolderAutoMountRow(
            scope_type=VFolderAutoMountScopeType.of_owner(self.scope),
            scope_id=self.scope,
            vfolder_id=self.spec.vfolder_id,
            mount_destination=self.spec.mount_destination,
            subpath=self.spec.subpath,
            mount_permission=self.spec.mount_permission,
        )

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountSearchableFields.own.to_data(row)
