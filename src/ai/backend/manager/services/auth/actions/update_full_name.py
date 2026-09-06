from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class UpdateFullNameAction(UserEntityAction):
    full_name: str
    domain_name: str
    email: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_full_name"


@dataclass(frozen=True)
class UpdateFullNameActionResult:
    success: bool
