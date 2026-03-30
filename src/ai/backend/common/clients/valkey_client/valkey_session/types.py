from pydantic import BaseModel


class LoginSessionTokenData(BaseModel):
    type: str
    access_key: str
    secret_key: str
    role: str
    status: str


class LoginSessionInner(BaseModel):
    authenticated: bool
    token: LoginSessionTokenData


class LoginSessionData(BaseModel):
    created: int
    expiration_dt: int
    session: LoginSessionInner
