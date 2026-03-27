from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class AdminRevokeLoginSessionAction(AuthAction):
    session_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class MyRevokeLoginSessionAction(AuthAction):
    session_id: UUID
    user_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.session_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class RevokeLoginSessionActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
