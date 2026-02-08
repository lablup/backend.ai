import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class DownloadFilesAction(SessionAction):
    user_id: uuid.UUID
    session_name: str
    files: list[str]
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class DownloadFilesActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
