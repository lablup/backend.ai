import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import VFolderFileAction


@dataclass
class CreateUploadSessionV2Action(VFolderFileAction):
    """Create an upload session for a vfolder. Policy is resolved internally from user_id."""

    user_id: uuid.UUID
    path: str
    size: int

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_upload_session_v2"


@dataclass
class CreateUploadSessionV2ActionResult:
    token: str
    url: str
