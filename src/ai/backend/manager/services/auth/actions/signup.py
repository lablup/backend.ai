import uuid
from dataclasses import dataclass
from typing import Optional, override

from aiohttp import web

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class SignupAction(AuthAction):
    request: web.Request
    domain_name: str
    email: str
    password: str
    username: Optional[str]
    full_name: Optional[str]
    description: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "signup"

    @property
    def hook_params(self) -> dict[str, str]:
        params = {
            "domain": self.domain_name,
            "email": self.email,
            "password": self.password,
        }
        if self.username:
            params["username"] = self.username
        if self.full_name:
            params["full_name"] = self.full_name
        if self.description:
            params["description"] = self.description
        return params


@dataclass
class SignupActionResult(BaseActionResult):
    user_id: uuid.UUID
    access_key: str
    secret_key: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)
