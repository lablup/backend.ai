import enum
from typing import Any, Optional

from pydantic import BaseModel


class AuthTokenTypes(enum.Enum):
    KEYPAIR = "keypair"
    JWT = "jwt"


class AuthResponseData(BaseModel):
    access_key: str
    secret_key: str
    role: str
    status: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class RedirectAuthResponseData(BaseModel):
    redirect_url: Optional[str]
    token: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="json")


class AuthResponse(BaseModel):
    data: AuthResponseData | RedirectAuthResponseData
    type: AuthTokenTypes = AuthTokenTypes.KEYPAIR

    @classmethod
    def from_auth_response(cls, response: dict[str, Any]) -> "AuthResponse":
        if "redirect_url" in response:
            return AuthResponse(
                data=RedirectAuthResponseData(**response),
            )
        else:
            return AuthResponse(
                data=AuthResponseData(**response),
            )
