"""V2 get vfolder action — vfolder_uuid only, RBAC validated at processor level."""

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class GetVFolderV2Action(VFolderAction):
    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfolder_v2"


@dataclass
class GetVFolderV2ActionResult:
    vfolder: VFolderData
