import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class DownloadFileAction(SessionAction):
    user_id: uuid.UUID
    session_name: str
    file: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "download_file"


@dataclass
class DownloadFileActionResult(BaseActionResult):
    bytes: bytes
    session_data: SessionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
