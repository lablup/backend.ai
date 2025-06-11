from typing import Optional

from pydantic import BaseModel, Field


class KeyPair(BaseModel):
    access_key: str = Field(
        description="The access key for the API.", examples=["some-access-key"], alias="access-key"
    )
    secret_key: str = Field(
        description="The secret key for the API.", examples=["some-secret-key"], alias="secret-key"
    )


class Endpoint(BaseModel):
    endpoint: str = Field(
        description="The API endpoint.",
        examples=["http://127.0.0.1:8090/", "http://127.0.0.1:8091/"],
    )


class LoginCredential(BaseModel):
    user_id: str = Field(
        description="The user ID for login.", examples=["user@example.com"], alias="user-id"
    )
    password: str = Field(description="The password for login.", examples=["password123"])
    otp: Optional[str] = Field(
        default=None,
        description="The one-time password for login, if required.",
        examples=["123456"],
    )


class TestContextInjectionModel(BaseModel):
    keypair_endpoint: Optional[Endpoint] = Field(
        default=None,
        description="The endpoint configuration for the test context.",
    )
    keypair: Optional[KeyPair] = Field(
        default=None,
        description="The key pair for the test context.",
    )
    login_endpoint: Optional[Endpoint] = Field(
        default=None,
        description="The endpoint configuration for the test context.",
    )
    login_credential: Optional[LoginCredential] = Field(
        default=None,
        description="The login credentials for the test context.",
        alias="login-credential",
    )


class TesterConfig(BaseModel):
    context: TestContextInjectionModel = Field(
        default_factory=TestContextInjectionModel,
        description="Configurations injected by the tester.",
    )
