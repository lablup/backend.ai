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
    api_endpoint: Optional[str] = Field(
        default=None,
        description="The API endpoint configuration for the test context.",
        alias="api-endpoint",
    )
    login_endpoint: Optional[str] = Field(
        default=None,
        description="The login endpoint configuration for the test context.",
        alias="login-endpoint",
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


class Image(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="The Docker image to use for the test context.",
        examples=["cr.backend.ai/multiarch/python:3.13-ubuntu24.04"],
    )


class TestContextInjectionModel(BaseModel):
    endpoint: Optional[Endpoint] = Field(
        default=None,
        description="The endpoint configurations for the test context.",
    )
    keypair: Optional[KeyPair] = Field(
        default=None,
        description="The key pair for the test context.",
    )
    login_credential: Optional[LoginCredential] = Field(
        default=None,
        description="The login credentials for the test context.",
        alias="login-credential",
    )
    image: Optional[Image] = Field(
        default=None,
        description="The Docker image context for the test.",
    )


class TesterConfig(BaseModel):
    context: TestContextInjectionModel = Field(
        default_factory=TestContextInjectionModel,
        description="Configurations injected by the tester.",
    )
