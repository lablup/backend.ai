from dataclasses import dataclass
from typing import override
from uuid import UUID

from aiohttp import web

from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.auth.types import AuthorizationResult
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction


@dataclass(frozen=True)
class AuthorizeAction(AuthGlobalAction):
    request: web.Request
    type: AuthTokenType
    domain_name: str
    email: str
    password: str
    stoken: str | None
    otp: str | None
    client_type_id: UUID | None
    force: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "authorize"

    @property
    def hook_params(self) -> dict[str, str]:
        return {
            "type": self.type.value,
            "domain": self.domain_name,
            "username": self.email,
            "password": self.password,
            "stoken": self.stoken or "",
            "sToken": self.stoken or "",
            "otp": self.otp or "",
        }


@dataclass(frozen=True)
class AuthorizeActionResult:
    stream_response: web.StreamResponse | None
    authorization_result: AuthorizationResult | None
