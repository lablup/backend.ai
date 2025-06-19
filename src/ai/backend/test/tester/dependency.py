from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseDependencyModel(BaseModel):
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


class KeyPairDep(BaseDependencyModel):
    access_key: str = Field(description="The access key for the API.", examples=["some-access-key"])
    secret_key: str = Field(description="The secret key for the API.", examples=["some-secret-key"])


class EndpointDep(BaseDependencyModel):
    api_endpoint: Optional[str] = Field(
        default=None,
        description="The API endpoint configuration for the test context.",
    )
    login_endpoint: Optional[str] = Field(
        default=None,
        description="The login endpoint configuration for the test context.",
    )


class LoginCredentialDep(BaseDependencyModel):
    user_id: str = Field(description="The user ID for login.", examples=["user@example.com"])
    password: str = Field(description="The password for login.", examples=["password123"])
    otp: Optional[str] = Field(
        default=None,
        description="The one-time password for login, if required.",
        examples=["123456"],
    )


class ImageDep(BaseDependencyModel):
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


class BatchSessionDep(BaseDependencyModel):
    startup_command: Optional[str] = Field(
        default=None,
        description="The startup command to run in the batch session.",
        examples=["ls -la"],
    )
    batch_timeout: Optional[float] = Field(
        default=None,
        description="The timeout for the batch session in seconds.",
        examples=[10.0],
    )


class SSEDep(BaseDependencyModel):
    timeout: float = Field(
        default=60.0,
        description="The timeout for the session creation in seconds.",
        examples=[60.0],
    )


class ClusterDep(BaseDependencyModel):
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


class BootstrapScriptDep(BaseDependencyModel):
    bootstrap_script: Optional[str] = Field(
        default=None,
        description="The bootstrap script to run before the session starts. Used as an argument when creating a compute session.",
        examples=["echo 'Bootstrapping...'"],
    )


class SessionDep(BaseDependencyModel):
    resources: Optional[dict] = Field(
        default=None,
        description="The resources to allocate for the session.",
        examples=[{"cpu": 2, "mem": "4gb"}],
    )


class VFolderDep(BaseDependencyModel):
    group: Optional[str] = Field(
        default=None,
        description="The group name for the vfolder.",
    )
    unmanaged_path: Optional[str] = Field(
        default=None, description="The unmanaged path for the vfolder."
    )
    permission: str = Field(
        description="The permission for the vfolder.",
    )
    cloneable: bool = Field(
        description="Whether the vfolder is cloneable.",
    )


class ScalingGroupDep(BaseDependencyModel):
    name: Optional[str] = Field(
        default=None,
        description="The name of the scaling group for the test context.",
        examples=["default", "custom-scaling-group"],
    )


class TestContextInjectionModel(BaseDependencyModel):
    endpoint: Optional[EndpointDep] = Field(
        default=None,
        description="The endpoint configurations for the test context.",
    )
    keypair: Optional[KeyPairDep] = Field(
        default=None,
        description="The key pair for the test context.",
    )
    login_credential: Optional[LoginCredentialDep] = Field(
        default=None,
        description="The login credentials for the test context.",
        alias="login-credential",
    )
    image: Optional[ImageDep] = Field(
        default=None,
        description="The Docker image context for the test.",
    )
    sse: Optional[SSEDep] = Field(
        default=None,
        description="The Server-Sent Events configuration for the test context.",
    )
    cluster_config: Optional[ClusterDep] = Field(
        default=None,
        description="The cluster configuration for the test context.",
        alias="cluster-config",
    )
    batch_session: Optional[BatchSessionDep] = Field(
        default=None,
        description="The batch session configuration for the test context.",
        alias="batch-session",
    )
    session: Optional[SessionDep] = Field(
        default=None,
        description="The session configuration for the test context.",
    )
    vfolder: Optional[VFolderDep] = Field(
        default=None,
        description="The vfolder configuration for the test context.",
    )
    scaling_group: Optional[ScalingGroupDep] = Field(
        default=None,
        description="The scaling group configuration for the test context.",
        alias="scaling-group",
    )


class CodeExecutionDep(BaseDependencyModel):
    code: str = Field(
        description="The code to execute in the test.",
        examples=["print('Hello, World!')"],
    )
    expected_result: str = Field(
        description="The expected result of the code execution.",
        examples=["Hello, World!"],
    )
