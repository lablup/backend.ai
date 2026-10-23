from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.purgers import VFolderAutoMountPurger
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow

__all__ = ("PurgeVFolderAutoMountAction",)


@dataclass(frozen=True)
class PurgeVFolderAutoMountAction(PurgeEntityOpsAction[VFolderAutoMountRow, VFolderAutoMountData]):
    """Remove an auto-mount with its virtual entity and every edge naming it."""

    purger: VFolderAutoMountPurger

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_vfolder_auto_mount"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.purger.entity_id()

    @override
    def to_purger(self) -> VFolderAutoMountPurger:
        return self.purger
