from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ExecuteSessionActionParams:
    mode: str | None
    # TODO: Add proper type
    options: Any | None
    code: str | None
    run_id: str | None


@dataclass
class ExecuteSessionAction(SessionAction):
    session_name: str
    api_version: tuple[Any, ...]
    owner_access_key: AccessKey
    params: ExecuteSessionActionParams

    @override
    @classmethod
    def action_name(cls) -> str:
        return "execute_session"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ExecuteSessionActionResult:
    # TODO: Add proper type
    result: Any
    session_data: SessionData
