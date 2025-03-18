import uuid
from typing import Any, Mapping, Self

from aiohttp import web

from ai.backend.common.api_handlers import MiddlewareParam


class UserIdentityCtx(MiddlewareParam):
    user_uuid: uuid.UUID
    user_role: str
    user_email: str
    domain_name: str

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(
            user_uuid=request["user"]["uuid"],
            user_role=request["user"]["role"],
            user_email=request["user"]["email"],
            domain_name=request["user"]["domain_name"],
        )


class KeypairCtx(MiddlewareParam):
    access_key: str
    resource_policy: Mapping[str, Any]

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(
            access_key=request["keypair"]["access_key"],
            resource_policy=request["keypair"]["resource_policy"],
        )
