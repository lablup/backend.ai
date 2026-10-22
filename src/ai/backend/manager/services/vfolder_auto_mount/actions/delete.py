from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.updaters import VFolderAutoMountSoftDeleteUpdater

__all__ = ("DeleteVFolderAutoMountAction",)


@dataclass(frozen=True)
class DeleteVFolderAutoMountAction(
    DeleteSingleEntityOpsAction[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Soft-delete an auto-mount; its graph stays so it can be restored."""

    updater: VFolderAutoMountSoftDeleteUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.auto_mount_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_vfolder_auto_mount"

    @override
    def to_updater(self) -> VFolderAutoMountSoftDeleteUpdater:
        return self.updater
