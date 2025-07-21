import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ListFilesAction(SessionAction):
    user_id: uuid.UUID
    path: str
    session_name: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_files"


@dataclass
class ListFilesActionResult(BaseActionResult):
    result: Mapping[str, Any]
    session_data: SessionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
