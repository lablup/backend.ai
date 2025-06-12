from __future__ import annotations

import enum
from typing import Any, Self

from pydantic import BaseModel


class AuthTokenType(enum.StrEnum):
    KEYPAIR = "keypair"
    JWT = "jwt"


class AuthResponseType(enum.StrEnum):
    SUCCESS = "success"
    REQUIRE_TWO_FACTOR_REGISTRATION = "REQUIRE_TWO_FACTOR_REGISTRATION"
    REQUIRE_TWO_FACTOR_AUTH = "REQUIRE_TWO_FACTOR_AUTH"


class TwoFactorType(enum.StrEnum):
    TOTP = "TOTP"


class AuthResponse(BaseModel):
    response_type: AuthResponseType

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)


class AuthSuccessResponse(AuthResponse):
    access_key: str
    secret_key: str
    role: str
    status: str
    type: AuthTokenType = AuthTokenType.KEYPAIR

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class RequireTwoFactorRegistrationResponse(AuthResponse):
    token: str
    type: TwoFactorType

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class RequireTwoFactorAuthResponse(AuthResponse):
    type: TwoFactorType

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


def parse_auth_response(data: dict[str, Any]) -> AuthResponse:
    raw_response_type = data.get("response_type")
    respones_type = (
        AuthResponseType(raw_response_type)
        if raw_response_type is not None
        else AuthResponseType.SUCCESS
    )
    match respones_type:
        case AuthResponseType.SUCCESS:
            return AuthSuccessResponse.model_validate(data)
        case AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION:
            return RequireTwoFactorRegistrationResponse.model_validate(data)
        case AuthResponseType.REQUIRE_TWO_FACTOR_AUTH:
            return RequireTwoFactorAuthResponse.model_validate(data)
