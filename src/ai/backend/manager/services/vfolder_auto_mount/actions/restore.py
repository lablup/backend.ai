from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.updaters import VFolderAutoMountRestoreUpdater

__all__ = ("RestoreVFolderAutoMountAction",)


@dataclass(frozen=True)
class RestoreVFolderAutoMountAction(
    RestoreSingleEntityOpsAction[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Bring a soft-deleted auto-mount back."""

    updater: VFolderAutoMountRestoreUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.auto_mount_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_vfolder_auto_mount"

    @override
    def to_updater(self) -> VFolderAutoMountRestoreUpdater:
        return self.updater
