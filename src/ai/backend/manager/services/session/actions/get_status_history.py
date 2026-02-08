import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class GetStatusHistoryAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetStatusHistoryActionResult(BaseActionResult):
    status_history: dict[str, Any]
    session_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)
