import enum

from pydantic import BaseModel


class AuthTokenTypes(enum.Enum):
    KEYPAIR = "keypair"
    JWT = "jwt"


class AuthResponseData(BaseModel):
    access_key: str
    secret_key: str
    role: str
    status: str


class RedirectAuthResponseData(BaseModel):
    redirect_url: str
    token: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump()


class AuthResponse(BaseModel):
    status: int
    data: AuthResponseData | RedirectAuthResponseData
    type: AuthTokenTypes = AuthTokenTypes.KEYPAIR
