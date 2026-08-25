from dataclasses import dataclass
from typing import override

from aiohttp import web

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class UpdatePasswordAction(UserEntityAction):
    request: web.Request
    domain_name: str
    email: str
    old_password: str
    new_password: str
    new_password_confirm: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_password"

    @property
    def hook_params(self) -> dict[str, str]:
        return {
            "old_password": self.old_password,
            "new_password": self.new_password,
            "new_password2": self.new_password_confirm,
        }


@dataclass(frozen=True)
class UpdatePasswordActionResult:
    success: bool
    message: str
