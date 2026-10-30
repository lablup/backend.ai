"""Insert specs for the kernel_group_vfolder_mounts table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.kernel_group_vfolder_mount import KernelGroupVFolderMountID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import VFolderMount
from ai.backend.manager.data.kernel_group.types import KernelGroupVFolderMountData
from ai.backend.manager.errors.kernel import InvalidKernelConfig
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.kernel_group_vfolder_mount.row import KernelGroupVFolderMountRow
from ai.backend.manager.models.specs.creator import NestedFieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = ("KernelGroupVFolderMountCreator",)


@dataclass(frozen=True)
class KernelGroupVFolderMountCreator(
    NestedFieldCreator[KernelGroupID, KernelGroupVFolderMountRow, KernelGroupVFolderMountData]
):
    """Record one resolved vfolder mount of a kernel group."""

    mount: VFolderMount

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=InvalidKernelConfig(
                    "Two vfolder mounts of a kernel group share a destination."
                ),
                constraint_name="uq_kernel_group_vfolder_mounts_kernel_group_id",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=VFolderNotFound(),
                constraint_name="fk_kernel_group_vfolder_mounts_vfolder_id_vfolders",
            ),
        )

    @override
    def build_row(self, owner_id: KernelGroupID) -> KernelGroupVFolderMountRow:
        return KernelGroupVFolderMountRow(
            kernel_group_id=owner_id,
            vfolder_id=VFolderUUID(self.mount.vfid.folder_id),
            vfsubpath=str(self.mount.vfsubpath),
            mount_destination=str(self.mount.kernel_path),
            mount_perm=self.mount.mount_perm,
        )

    @override
    def to_data(self, row: KernelGroupVFolderMountRow) -> KernelGroupVFolderMountData:
        return KernelGroupVFolderMountData(
            id=KernelGroupVFolderMountID(row.id),
            kernel_group_id=row.kernel_group_id,
            vfolder_id=row.vfolder_id,
            vfsubpath=row.vfsubpath,
            mount_destination=row.mount_destination,
            mount_perm=row.mount_perm,
        )
