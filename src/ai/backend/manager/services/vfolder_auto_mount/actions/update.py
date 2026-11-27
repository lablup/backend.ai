from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.updaters import VFolderAutoMountUpdater

__all__ = (
    "UpdateVFolderAutoMountAction",
    "UpdateVFolderAutoMountActionResult",
)


@dataclass(frozen=True)
class UpdateVFolderAutoMountAction(BaseSingleEntityAction):
    """Change an auto-mount's destination, subpath or permission for the sessions created after it."""

    updater: VFolderAutoMountUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_vfolder_auto_mount"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.vfolder_auto_mount_id


@dataclass(frozen=True)
class UpdateVFolderAutoMountActionResult:
    data: VFolderAutoMountData
