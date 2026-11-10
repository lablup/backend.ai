import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.file_base import SessionFileAction


@dataclass
class DownloadFileAction(SessionFileAction):
    user_id: uuid.UUID
    session_name: str
    file: str
    owner_access_key: AccessKey

    @override
    @classmethod
    def action_name(cls) -> str:
        return "download_file"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class DownloadFileActionResult:
    bytes: bytes
    session_data: SessionData
