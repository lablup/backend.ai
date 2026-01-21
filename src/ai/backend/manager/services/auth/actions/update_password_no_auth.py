import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, override

from aiohttp import web

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class UpdatePasswordNoAuthAction(AuthAction):
    request: web.Request
    domain_name: str
    email: str
    current_password: str
    new_password: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_password_no_auth"

    @property
    def hook_params(self) -> dict[str, str]:
        return {
            "domain": self.domain_name,
            "username": self.email,
            "current_password": self.current_password,
            "new_password": self.new_password,
        }


@dataclass
class UpdatePasswordNoAuthActionResult(BaseActionResult):
    user_id: uuid.UUID
    password_changed_at: datetime

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)
