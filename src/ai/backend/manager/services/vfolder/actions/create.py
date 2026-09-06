from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder.creators import VFolderBaseCreator
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderScopeAction,
    VFolderScopeActionResult,
)


@dataclass
class CreateVFolderAction(VFolderScopeAction):
    """Create the vfolder the insert spec describes.

    The spec is built where the request is read, so what the folder becomes — whose it
    is, which project it lands in, what it may not collide with — is settled before this
    runs, and the scope the creation is authorized against comes from the spec too.
    """

    creator: VFolderBaseCreator

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return self.creator.scope_targets()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder"


@dataclass
class CreateVFolderActionResult(VFolderScopeActionResult):
    vfolder: VFolderData
