from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class ExecuteSessionActionParams:
    mode: Optional[str]
    # TODO: Add proper type
    options: Optional[Any]
    code: Optional[str]
    run_id: Optional[str]


@dataclass
class ExecuteSessionAction(SessionAction):
    session_name: str
    api_version: tuple[Any, ...]
    owner_access_key: AccessKey
    params: ExecuteSessionActionParams

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "execute"


@dataclass
class ExecuteSessionActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    session_row: SessionRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_row.id)
