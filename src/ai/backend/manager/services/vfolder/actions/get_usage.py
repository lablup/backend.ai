"""V2 live-usage action — fetches usage statistics through the storage proxy on demand."""

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderUsageData
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class GetVFolderUsageAction(VFolderAction):
    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfolder_usage"


@dataclass
class GetVFolderUsageActionResult:
    vfolder_uuid: uuid.UUID
    usage: VFolderUsageData | None
