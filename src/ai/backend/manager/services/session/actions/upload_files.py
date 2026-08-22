from dataclasses import dataclass
from typing import Any, override

from aiohttp import MultipartReader

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.file_base import SessionFileAction


@dataclass
class UploadFilesAction(SessionFileAction):
    session_name: str
    owner_access_key: AccessKey
    # TODO: Refactor this.
    reader: MultipartReader

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upload_files"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UploadFilesActionResult:
    # TODO: Add proper type
    result: Any
    session_data: SessionData
