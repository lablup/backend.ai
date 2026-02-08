from dataclasses import dataclass
from typing import override

from aiohttp import web

from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.auth.types import AuthorizationResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class AuthorizeAction(AuthAction):
    request: web.Request
    type: AuthTokenType
    domain_name: str
    email: str
    password: str
    stoken: str | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @property
    def hook_params(self) -> dict[str, str]:
        return {
            "type": self.type.value,
            "domain": self.domain_name,
            "username": self.email,
            "password": self.password,
            "stoken": self.stoken or "",
            "sToken": self.stoken or "",
        }


@dataclass
class AuthorizeActionResult(BaseActionResult):
    stream_response: web.StreamResponse | None
    authorization_result: AuthorizationResult | None

    @override
    def entity_id(self) -> str | None:
        return str(self.authorization_result.user_id) if self.authorization_result else None
