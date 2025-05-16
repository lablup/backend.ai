import enum
from typing import Any

from pydantic import BaseModel, ValidationError


class AuthTokenTypes(enum.Enum):
    KEYPAIR = "keypair"
    JWT = "jwt"


class AuthSuccessResponseData(BaseModel):
    access_key: str
    secret_key: str
    role: str
    status: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class RequireTOTPRegistrationResponseData(BaseModel):
    token: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class AuthResponse(BaseModel):
    data: AuthSuccessResponseData | RequireTOTPRegistrationResponseData
    type: AuthTokenTypes = AuthTokenTypes.KEYPAIR

    @classmethod
    def from_auth_response(cls, response: dict[str, Any]) -> "AuthResponse":
        data: AuthSuccessResponseData | RequireTOTPRegistrationResponseData
        try:
            data = AuthSuccessResponseData(**response)
        except ValidationError:
            data = RequireTOTPRegistrationResponseData(**response)
        return AuthResponse(data=data)
