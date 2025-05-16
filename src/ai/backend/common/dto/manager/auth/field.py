import enum

from pydantic import BaseModel


class AuthTokenTypes(enum.Enum):
    KEYPAIR = "keypair"
    JWT = "jwt"


class AuthSuccessResponseData(BaseModel):
    access_key: str
    secret_key: str
    role: str
    status: str


class RequireTOTPRegistrationResponseData(BaseModel):
    token: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump()


class AuthResponse(BaseModel):
    http_status: int
    data: AuthSuccessResponseData | RequireTOTPRegistrationResponseData
    type: AuthTokenTypes = AuthTokenTypes.KEYPAIR
