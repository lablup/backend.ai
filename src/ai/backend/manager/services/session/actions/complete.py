from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


# TODO: Rename this?
@dataclass
class CompleteAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey
    code: str
    # TODO: Add type
    options: Mapping[str, Any] | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "complete"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class CompleteActionResult:
    session_data: SessionData

    result: CodeCompletionResp
