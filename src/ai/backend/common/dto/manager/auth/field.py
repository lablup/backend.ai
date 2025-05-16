from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel


class AuthTokenTypes(enum.Enum):
    KEYPAIR = "keypair"
    JWT = "jwt"


class AuthResponseType(enum.StrEnum):
    SUCCESS = "success"
    REQUIRE_TOTP = "REQUIRE_TOTP"


class AuthResponse(BaseModel):
    response_type: AuthResponseType

    @classmethod
    def from_auth_response_data(cls, data: dict[str, Any]) -> AuthAuthResponseType:
        raw_response_type = data.get("response_type")
        respones_type = (
            AuthResponseType(raw_response_type)
            if raw_response_type is not None
            else AuthResponseType.SUCCESS
        )
        match respones_type:
            case AuthResponseType.SUCCESS:
                return AuthSuccessResponse.model_validate(data)
            case AuthResponseType.REQUIRE_TOTP:
                return RequireTOTPRegistrationResponse.model_validate(data)
            case _:
                return AuthSuccessResponse.model_validate(data)


class AuthSuccessResponse(AuthResponse):
    access_key: str
    secret_key: str
    role: str
    status: str
    type: AuthTokenTypes = AuthTokenTypes.KEYPAIR

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class RequireTOTPRegistrationResponse(AuthResponse):
    token: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


AuthAuthResponseType = AuthSuccessResponse | RequireTOTPRegistrationResponse
