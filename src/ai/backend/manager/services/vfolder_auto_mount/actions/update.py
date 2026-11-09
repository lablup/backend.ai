from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.updaters import VFolderAutoMountUpdater

__all__ = ("UpdateVFolderAutoMountAction",)


@dataclass(frozen=True)
class UpdateVFolderAutoMountAction(
    UpdateSingleEntityOpsAction[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Change an auto-mount's destination, subpath or permission for the sessions created after it."""

    updater: VFolderAutoMountUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_vfolder_auto_mount"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.vfolder_auto_mount_id

    @override
    def to_updater(self) -> VFolderAutoMountUpdater:
        return self.updater
