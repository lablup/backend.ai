import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.vfolder.base import VFolderAction


@dataclass
class GetTaskLogsAction(VFolderAction):
    user_id: uuid.UUID
    domain_name: str
    user_role: UserRole
    # TODO: Change this to KernelId
    kernel_id: str
    session_name: str
    owner_access_key: AccessKey

    # TODO: Remove this.
    request: Any

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "get_task_logs"


@dataclass
class GetTaskLogsActionResult(BaseActionResult):
    # TODO: Add proper type
    response: Any
    # vfolder_row: VFolderRow
    vfolder_row: Any

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_row.id)
