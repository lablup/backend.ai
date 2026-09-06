from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class SignoutAction(UserEntityAction):
    domain_name: str
    requester_email: str
    email: str
    password: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "signout"


@dataclass(frozen=True)
class SignoutActionResult:
    success: bool
