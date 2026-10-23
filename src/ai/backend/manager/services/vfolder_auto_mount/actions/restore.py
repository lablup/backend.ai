from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.specs.soft_delete import RestoreUpdater
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow

__all__ = ("RestoreVFolderAutoMountAction",)


@dataclass(frozen=True)
class RestoreVFolderAutoMountAction(
    RestoreSingleEntityOpsAction[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Bring a soft-deleted auto-mount back."""

    updater: RestoreUpdater[VFolderAutoMountRow, VFolderAutoMountData]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.target_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_vfolder_auto_mount"

    @override
    def to_updater(self) -> RestoreUpdater[VFolderAutoMountRow, VFolderAutoMountData]:
        return self.updater
