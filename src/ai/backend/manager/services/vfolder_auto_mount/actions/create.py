from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.creators import VFolderAutoMountCreator

__all__ = (
    "CreateVFolderAutoMountAction",
    "CreateVFolderAutoMountActionResult",
)


@dataclass(frozen=True)
class CreateVFolderAutoMountAction(BaseScopeAction):
    """Add a vfolder to the auto-mounts of a project or a user."""

    creator: VFolderAutoMountCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderAutoMountEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_auto_mount"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.creator.scope,)


@dataclass(frozen=True)
class CreateVFolderAutoMountActionResult(BaseScopeActionResult):
    data: VFolderAutoMountData

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.data.entity_id(),)
