import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.session.base import SessionAction


# TODO: Change this to BatchAction
@dataclass
class DownloadFilesAction(SessionAction):
    user_id: uuid.UUID
    session_name: str
    files: list[str]
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "download_file_multi"


@dataclass
class DownloadFilesActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any

    @override
    def entity_id(self) -> Optional[str]:
        return ""
