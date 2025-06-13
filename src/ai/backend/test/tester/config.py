from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseConfigModel(BaseModel):
    @staticmethod
    def snake_to_kebab_case(string: str) -> str:
        return string.replace("_", "-")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
        extra="allow",
        alias_generator=snake_to_kebab_case,
    )


class KeyPairConfig(BaseConfigModel):
    access_key: str = Field(description="The access key for the API.", examples=["some-access-key"])
    secret_key: str = Field(description="The secret key for the API.", examples=["some-secret-key"])


class EndpointConfig(BaseConfigModel):
    api_endpoint: Optional[str] = Field(
        default=None,
        description="The API endpoint configuration for the test context.",
    )
    login_endpoint: Optional[str] = Field(
        default=None,
        description="The login endpoint configuration for the test context.",
    )


class LoginCredentialConfig(BaseConfigModel):
    user_id: str = Field(description="The user ID for login.", examples=["user@example.com"])
    password: str = Field(description="The password for login.", examples=["password123"])
    otp: Optional[str] = Field(
        default=None,
        description="The one-time password for login, if required.",
        examples=["123456"],
    )


class ImageConfig(BaseConfigModel):
    name: Optional[str] = Field(
        default=None,
        description="The Docker image to use for the test context.",
        examples=["cr.backend.ai/multiarch/python:3.13-ubuntu24.04"],
    )
    architecture: Optional[str] = Field(
        default=None,
        description="The architecture of the session.",
        examples=["x86_64"],
    )


class BatchSessionConfig(BaseConfigModel):
    startup_command: Optional[str] = Field(
        default=None,
        description="The startup command to run in the batch session.",
        examples=["ls -la"],
    )


class SSEConfig(BaseConfigModel):
    timeout: float = Field(
        default=60.0,
        description="The timeout for the session creation in seconds.",
        examples=[60.0],
    )


class ClusterConfig(BaseConfigModel):
    # By default, testing is conducted for both single-node and multi-node setups through parametrization,
    # But we'd like to have left room for manually injecting values.
    cluster_mode: Optional[str] = Field(
        default=None,
        description="The cluster mode for the session.",
        examples=["single_node", "multi_node"],
    )
    cluster_size: Optional[int] = Field(
        default=None,
        description="The size of the cluster for the session.",
        examples=[1, 2, 3],
    )


class SessionConfig(BaseConfigModel):
    resources: Optional[dict] = Field(
        default=None,
        description="The resources to allocate for the session.",
        examples=[{"cpu": 2, "mem": "4gb"}],
    )


class SessionTemplateConfig(BaseConfigModel):
    content: str = Field(
        description="The content of the session template.",
        # examples=[""],  # Skip template since it's too long
    )


class TestContextInjectionModel(BaseConfigModel):
    endpoint: Optional[EndpointConfig] = Field(
        default=None,
        description="The endpoint configurations for the test context.",
    )
    keypair: Optional[KeyPairConfig] = Field(
        default=None,
        description="The key pair for the test context.",
    )
    login_credential: Optional[LoginCredentialConfig] = Field(
        default=None,
        description="The login credentials for the test context.",
        alias="login-credential",
    )
    image: Optional[ImageConfig] = Field(
        default=None,
        description="The Docker image context for the test.",
    )
    sse: Optional[SSEConfig] = Field(
        default=None,
        description="The Server-Sent Events configuration for the test context.",
    )
    cluster_config: Optional[ClusterConfig] = Field(
        default=None,
        description="The cluster configuration for the test context.",
        alias="cluster-config",
    )
    batch_session: Optional[BatchSessionConfig] = Field(
        default=None,
        description="The batch session configuration for the test context.",
        alias="batch-session",
    )
    session: Optional[SessionConfig] = Field(
        default=None,
        description="The session configuration for the test context.",
    )
    session_template: Optional[SessionTemplateConfig] = Field(
        default=None,
        description="The session template for the test context.",
        alias="session-template",
    )


class TestRunnerConfig(BaseConfigModel):
    concurrency: int = Field(
        default=10,
        description="The number of concurrent tests to run.",
        examples=[1, 2, 4],
    )


class TesterConfig(BaseConfigModel):
    context: TestContextInjectionModel = Field(
        default_factory=TestContextInjectionModel,
        description="Configurations injected by the tester.",
    )
    runner: TestRunnerConfig = Field(
        default_factory=TestRunnerConfig,
        description="Configurations for the test runner.",
    )
