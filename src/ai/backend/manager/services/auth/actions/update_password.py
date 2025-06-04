import uuid
from dataclasses import dataclass
from typing import Optional, override

from aiohttp import web

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class UpdatePasswordAction(AuthAction):
    request: web.Request
    user_id: uuid.UUID
    domain_name: str
    email: str
    old_password: str
    new_password: str
    new_password_confirm: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_password"

    @property
    def hook_params(self) -> dict[str, str]:
        return {
            "old_password": self.old_password,
            "new_password": self.new_password,
            "new_password2": self.new_password_confirm,
        }


@dataclass
class UpdatePasswordActionResult(BaseActionResult):
    success: bool
    message: str

    @override
    def entity_id(self) -> Optional[str]:
        return None
