from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
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
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "execute"


@dataclass
class ExecuteSessionActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
