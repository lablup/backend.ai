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


class SessionCreation(BaseModel):
    image: Optional[str] = Field(
        default=None,
        description="The Docker image to use for the test context.",
        examples=["cr.backend.ai/multiarch/python:3.13-ubuntu24.04"],
    )
    architecture: Optional[str] = Field(
        default=None,
        description="The architecture of the session.",
        examples=["x86_64"],
    )
    template: Optional[str] = Field(
        default=None,
        description="The session template to use for the test context.",
        # examples=[""],  # Skip template since it's too long
    )
    resources: Optional[dict] = Field(
        default=None,
        description="The resources to allocate for the session.",
        examples=[{"cpu": 2, "mem": "4gb"}],
    )
    startup_command: Optional[str] = Field(
        default=None,
        description="The startup command to run in the batch session.",
        examples=["ls -la"],
        alias="startup-command",
    )
    # By default, testing is conducted for both single-node and multi-node setups through parametrization,
    # But we'd like to have left room for manually injecting values.
    cluster_mode: Optional[str] = Field(
        default=None,
        description="The cluster mode for the session.",
        examples=["single_node", "multi_node"],
        alias="cluster-mode",
    )
    cluster_size: Optional[int] = Field(
        default=None,
        description="The size of the cluster for the session.",
        examples=[1, 2, 3],
        alias="cluster-size",
    )


class SessionTemplate(BaseModel):
    content: str = Field(
        description="The content of the session template.",
        # examples=[""],  # Skip template since it's too long
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
    session_creation: Optional[SessionCreation] = Field(
        default=None,
        description="The session creation parameters for the test context.",
        alias="session-creation",
    )
    session_template: Optional[SessionTemplate] = Field(
        default=None,
        description="The session template for the test context.",
        alias="session-template",
    )


class TesterConfig(BaseModel):
    context: TestContextInjectionModel = Field(
        default_factory=TestContextInjectionModel,
        description="Configurations injected by the tester.",
    )
