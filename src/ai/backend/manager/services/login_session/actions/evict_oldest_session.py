from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.login_session.actions.base import LoginSessionAction


@dataclass
class EvictOldestSessionAction(LoginSessionAction):
    user_uuid: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class EvictOldestSessionActionResult(BaseActionResult):
    evicted_session_token: str | None

    @override
    def entity_id(self) -> str | None:
        return self.evicted_session_token
