import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import override

from aiohttp import web

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction


@dataclass(frozen=True)
class UpdatePasswordNoAuthAction(AuthGlobalAction):
    request: web.Request
    domain_name: str
    email: str
    current_password: str
    new_password: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_password_no_auth"

    @property
    def hook_params(self) -> dict[str, str]:
        return {
            "domain": self.domain_name,
            "username": self.email,
            "current_password": self.current_password,
            "new_password": self.new_password,
        }


@dataclass(frozen=True)
class UpdatePasswordNoAuthActionResult:
    user_id: uuid.UUID
    password_changed_at: datetime
