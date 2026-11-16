from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class UpdatePasswordAction(UserEntityAction):
    domain_name: str
    email: str
    old_password: str
    new_password: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_password"


@dataclass(frozen=True)
class UpdatePasswordActionResult:
    success: bool
    message: str
