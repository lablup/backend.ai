from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountEntityType
from ai.backend.manager.actions.v2.ops.base import CreateEntityOpsAction
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.creators import VFolderAutoMountCreator
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow

__all__ = ("CreateVFolderAutoMountAction",)


@dataclass(frozen=True)
class CreateVFolderAutoMountAction(
    CreateEntityOpsAction[VFolderAutoMountRow, VFolderAutoMountData]
):
    """Add a vfolder to the auto-mounts of a project."""

    creator: VFolderAutoMountCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderAutoMountEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.creator.scope,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_auto_mount"

    @override
    def to_creator(self) -> VFolderAutoMountCreator:
        return self.creator
