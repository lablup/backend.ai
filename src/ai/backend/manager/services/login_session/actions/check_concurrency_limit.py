from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.login_session.actions.base import LoginSessionAction


@dataclass
class CheckConcurrencyLimitAction(LoginSessionAction):
    user_uuid: UUID
    max_concurrent_logins: int | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class CheckConcurrencyLimitActionResult(BaseActionResult):
    active_sessions: int
    limit_exceeded: bool

    @override
    def entity_id(self) -> str | None:
        return None
