import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.file_base import SessionFileAction


@dataclass
class ListFilesAction(SessionFileAction):
    user_id: uuid.UUID
    path: str
    session_name: str
    owner_access_key: AccessKey

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_files"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListFilesActionResult:
    result: Mapping[str, Any]
    session_data: SessionData
