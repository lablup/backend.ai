"""
Common types for auth system.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel

__all__ = (
    "AuthTokenType",
    "AuthResponseType",
    "TwoFactorType",
    "AuthResponse",
    "AuthSuccessResponse",
    "RequireTwoFactorRegistrationResponse",
    "RequireTwoFactorAuthResponse",
    "parse_auth_response",
)


class AuthTokenType(StrEnum):
    KEYPAIR = "keypair"
    JWT = "jwt"


class AuthResponseType(StrEnum):
    SUCCESS = "success"
    REQUIRE_TWO_FACTOR_REGISTRATION = "REQUIRE_TWO_FACTOR_REGISTRATION"
    REQUIRE_TWO_FACTOR_AUTH = "REQUIRE_TWO_FACTOR_AUTH"


class TwoFactorType(StrEnum):
    TOTP = "TOTP"


class AuthResponse(BaseModel):
    """Base class for all authorization responses. The response_type discriminator
    determines which subclass the response should be deserialized into."""

    response_type: AuthResponseType

    @classmethod
    def parse(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)


class AuthSuccessResponse(AuthResponse):
    """Returned when authorization succeeds without requiring 2FA."""

    access_key: str
    secret_key: str
    role: str
    status: str
    type: AuthTokenType = AuthTokenType.KEYPAIR

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class RequireTwoFactorRegistrationResponse(AuthResponse):
    """Returned when the user needs to register a 2FA device before completing authorization."""

    token: str
    type: TwoFactorType

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class RequireTwoFactorAuthResponse(AuthResponse):
    """Returned when the user has 2FA enabled and must provide a TOTP code to complete authorization."""

    type: TwoFactorType

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


def parse_auth_response(data: dict[str, Any]) -> AuthResponse:
    raw_response_type = data.get("response_type")
    response_type = (
        AuthResponseType(raw_response_type)
        if raw_response_type is not None
        else AuthResponseType.SUCCESS
    )
    match response_type:
        case AuthResponseType.SUCCESS:
            return AuthSuccessResponse.model_validate(data)
        case AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION:
            return RequireTwoFactorRegistrationResponse.model_validate(data)
        case AuthResponseType.REQUIRE_TWO_FACTOR_AUTH:
            return RequireTwoFactorAuthResponse.model_validate(data)
