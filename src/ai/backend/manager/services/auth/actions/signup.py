import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserGlobalAction


@dataclass(frozen=True)
class SignupAction(UserGlobalAction):
    domain_name: str
    email: str
    password: str
    username: str | None
    full_name: str | None
    description: str | None
    lang: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "signup"


@dataclass(frozen=True)
class SignupActionResult:
    user_id: uuid.UUID
    access_key: str
    secret_key: str
