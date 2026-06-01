from ai.backend.common.types import BackendAISchema


class LoginSessionTokenData(BackendAISchema):
    type: str
    access_key: str
    secret_key: str
    role: str
    status: str


class LoginSessionInner(BackendAISchema):
    authenticated: bool
    token: LoginSessionTokenData


class LoginSessionData(BackendAISchema):
    created: int
    expiration_dt: int
    session: LoginSessionInner
