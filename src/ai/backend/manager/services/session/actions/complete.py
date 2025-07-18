from dataclasses import dataclass
from typing import Any, Mapping, Optional, override

from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


# TODO: Rename this?
@dataclass
class CompleteAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey
    code: str
    # TODO: Add type
    options: Optional[Mapping[str, Any]]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "complete"


@dataclass
class CompleteActionResult(BaseActionResult):
    session_data: SessionData

    result: CodeCompletionResp

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)
