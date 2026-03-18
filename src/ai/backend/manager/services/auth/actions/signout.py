import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class SignoutAction(AuthAction):
    user_id: uuid.UUID
    domain_name: str
    requester_email: str
    email: str
    password: str

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class SignoutActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
