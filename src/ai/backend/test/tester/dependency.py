from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai.backend.common.types import ClusterMode, RuntimeVariant


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


class UserResourcePolicyDep(BaseDependencyModel):
    name: str = Field(
        description="The name of the user resource policy.",
        examples=["default"],
    )


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


class DomainDep(BaseDependencyModel):
    name: str = Field(
        description="The domain name for the test context.",
        examples=["default"],
    )


class GroupDep(BaseDependencyModel):
    name: str = Field(
        description="The group name for the test context.",
        examples=["default"],
    )


class ScalingGroupDep(BaseDependencyModel):
    name: str = Field(
        description="The scaling group for the test context.",
        examples=["default"],
    )


class ImageDep(BaseDependencyModel):
    name: str = Field(
        description="The Docker image to use for the test context.",
        examples=["cr.backend.ai/multiarch/python:3.13-ubuntu24.04"],
    )
    architecture: str = Field(
        description="The architecture of the session.",
        examples=["x86_64"],
    )


class BatchSessionDep(BaseDependencyModel):
    startup_command: str = Field(
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
    cluster_mode: ClusterMode = Field(
        description="The cluster mode for the session.",
        examples=["single-node", "multi-node"],
    )
    cluster_size: int = Field(
        description="The size of the cluster for the session.",
        examples=[1, 2, 3],
    )


class BootstrapScriptDep(BaseDependencyModel):
    bootstrap_script: str = Field(
        description="The bootstrap script to run before the session starts. Used as an argument when creating a compute session.",
        examples=["echo 'Bootstrapping...'"],
    )


class SessionDep(BaseDependencyModel):
    resources: Optional[dict[str, Any]] = Field(
        default=None,
        description="The resources to allocate for the session.",
        examples=[{"cpu": 2, "mem": "4gb"}],
    )


class SessionImagifyDep(BaseDependencyModel):
    new_image_name: str = Field(
        description="The name of the new image to create from the session.",
        examples=["my-custom-image"],
    )


class ModelServiceDep(BaseDependencyModel):
    model_vfolder_name: str = Field(
        description="The model VFolder name to use for the model service.",
        examples=["vfolder-name"],
    )
    replicas: int = Field(
        description="The number of replicas for the model service.",
        examples=[1, 2, 3],
    )
    runtime_variant: RuntimeVariant = Field(
        default=RuntimeVariant.CUSTOM,
        description="The runtime variant for the model service.",
        examples=[v.name for v in RuntimeVariant],
    )
    # Separate group is required for the model service, so we placed this independently from the group context.
    group_name: str = Field(
        description="The group name for the model service.",
        examples=["model-store"],
    )
    model_mount_destination: str = Field(
        default="models",
        description="The destination path for the model mount in the model service.",
        examples=["models"],
    )
    model_definition_path: str = Field(
        default="./model-definition.yaml",
        description="The path to the model definition file in the model service.",
        examples=["./model-definition.yaml"],
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
    share_permission: str = Field(
        default="ro",
        description="The share permission for the vfolder.",
        examples=["ro", "rw"],
    )

    @model_validator(mode="after")
    def validate(self):
        if self.permission == self.share_permission:
            raise ValueError("permission and share_permission must be different")
        return self


class UploadFileDep(BaseDependencyModel):
    path: str = Field(
        description="The name of the file to upload.",
        examples=["test_file.txt", "nested/inner_file.txt"],
    )
    content: str = Field(
        description="The content of the file to upload.",
        examples=["This is a test file content."],
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
    )
    domain: Optional[DomainDep] = Field(
        default=None,
        description="The domain configuration for the test context.",
    )
    group: Optional[GroupDep] = Field(
        default=None,
        description="The group configuration for the test context.",
    )
    scaling_group: Optional[ScalingGroupDep] = Field(
        default=None,
        description="The scaling group configuration for the test context.",
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
    )
    batch_session: Optional[BatchSessionDep] = Field(
        default=None,
        description="The batch session configuration for the test context.",
    )
    session: Optional[SessionDep] = Field(
        default=None,
        description="The session configuration for the test context.",
    )
    session_imagify: Optional[SessionImagifyDep] = Field(
        default=None,
        description="The session imagify configuration for the test context.",
    )
    model_service: Optional[ModelServiceDep] = Field(
        default=None,
        description="The model service configuration for the test context.",
    )
    vfolder: Optional[VFolderDep] = Field(
        default=None,
        description="The vfolder configuration for the test context.",
    )
    user_resource_policy: Optional[UserResourcePolicyDep] = Field(
        default=None,
        description="The user resource policy configuration for the test context.",
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
