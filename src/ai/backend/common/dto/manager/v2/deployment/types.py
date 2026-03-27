"""
Common types for Deployment DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.fair_share.types import ResourceSlotInfo
from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceOptsInfoDTO
from ai.backend.common.types import ClusterMode, RuntimeVariant

__all__ = (
    "AccessTokenOrderField",
    "AutoScalingRuleOrderField",
    "BlueGreenConfigInfo",
    "BlueGreenStrategySpecInfo",
    "ClusterConfigInfoDTO",
    "ClusterMode",
    "DeploymentBasicInfo",
    "DeploymentMetadataInfoDTO",
    "DeploymentNetworkAccessInfoDTO",
    "DeploymentOrderField",
    "DeploymentPolicyInfo",
    "DeploymentRevisionInfo",
    "DeploymentStrategy",
    "DeploymentStrategyInfoDTO",
    "DeploymentStrategySpecInfo",
    "EndpointLifecycle",
    "EnvironmentVariableEntryInfoDTO",
    "EnvironmentVariablesInfoDTO",
    "ExtraVFolderMountGQLDTO",
    "ModelConfigInfoDTO",
    "ModelDeploymentStatus",
    "ModelDefinitionInfoDTO",
    "ModelHealthCheckInfoDTO",
    "ModelMountConfigInfoDTO",
    "ModelMetadataInfoDTO",
    "ModelRuntimeConfigInfoDTO",
    "ModelServiceConfigInfoDTO",
    "NetworkConfigInfo",
    "OrderDirection",
    "PreStartActionInfoDTO",
    "ReplicaOrderField",
    "ReplicaStateInfo",
    "ResourceConfigInfoDTO",
    "RevisionOrderField",
    "RollingUpdateConfigInfo",
    "RollingUpdateStrategySpecInfo",
    "RouteOrderField",
    "RouteStatus",
    "RouteTrafficStatus",
    "RuntimeVariant",
    "IntOrPercent",
)


class DeploymentOrderField(StrEnum):
    """Fields available for ordering deployments."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RevisionOrderField(StrEnum):
    """Fields available for ordering deployment revisions."""

    NAME = "name"
    CREATED_AT = "created_at"


class RouteOrderField(StrEnum):
    """Fields available for ordering deployment routes."""

    CREATED_AT = "created_at"
    STATUS = "status"
    TRAFFIC_RATIO = "traffic_ratio"


class IntOrPercent(BaseModel):
    """A rolling-update budget value: either an absolute count or a percentage.

    Exactly one of ``count`` or ``percent`` must be provided (oneOf semantics).

    - ``{"count": 2}``        — absolute replica count
    - ``{"percent": 0.25}``   — fraction of desired replicas (0.0-1.0)
    """

    count: int | None = Field(default=None, ge=0)
    percent: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_one_of(self) -> IntOrPercent:
        has_count = self.count is not None
        has_percent = self.percent is not None
        if has_count == has_percent:
            raise ValueError("Exactly one of 'count' or 'percent' must be provided.")
        return self

    @property
    def is_count(self) -> bool:
        return self.count is not None

    @property
    def is_percent(self) -> bool:
        return self.percent is not None

    @property
    def is_zero(self) -> bool:
        if self.count is not None:
            return self.count == 0
        return self.percent == 0.0


class DeploymentBasicInfo(BaseResponseModel):
    """Basic identifying information for a deployment."""

    name: str
    status: ModelDeploymentStatus
    tags: list[str]
    project_id: UUID
    domain_name: str
    created_user_id: UUID


class DeploymentRevisionInfo(BaseResponseModel):
    """Revision configuration details for a deployment."""

    cluster_mode: ClusterMode
    cluster_size: int
    resource_group: str
    resource_slots: dict[str, Any]
    resource_opts: dict[str, Any] | None = None
    image_id: UUID
    runtime_variant: RuntimeVariant
    inference_runtime_config: dict[str, Any] | None = None
    environ: dict[str, str] | None = None
    model_vfolder_id: UUID | None
    model_mount_destination: str | None
    model_definition_path: str | None


class NetworkConfigInfo(BaseResponseModel):
    """Network configuration for a deployment."""

    open_to_public: bool
    url: str | None
    preferred_domain_name: str | None


class ReplicaStateInfo(BaseResponseModel):
    """Current replica state of a deployment."""

    desired_replica_count: int
    replica_ids: list[UUID]


class RollingUpdateConfigInfo(BaseResponseModel):
    """Rolling update policy configuration."""

    max_surge: IntOrPercent
    max_unavailable: IntOrPercent


class BlueGreenConfigInfo(BaseResponseModel):
    """Blue/green deployment policy configuration."""

    auto_promote: bool
    promote_delay_seconds: int


class DeploymentPolicyInfo(BaseResponseModel):
    """Deployment update policy information."""

    strategy: DeploymentStrategy
    rolling_update: RollingUpdateConfigInfo | None
    blue_green: BlueGreenConfigInfo | None


class DeploymentStrategySpecInfo(BaseResponseModel):
    """Base class for deployment strategy spec sub-types.

    Subclassed by RollingUpdateStrategySpecInfo and BlueGreenStrategySpecInfo so
    that Strawberry's pydantic interface dispatch can resolve the concrete GQL
    type from the concrete DTO type via DeploymentStrategySpecGQL.from_pydantic().
    """

    strategy: DeploymentStrategy


class RollingUpdateStrategySpecInfo(DeploymentStrategySpecInfo):
    """Rolling update strategy spec — matches RollingUpdateStrategySpecGQL structure."""

    max_surge: IntOrPercent
    max_unavailable: IntOrPercent


class BlueGreenStrategySpecInfo(DeploymentStrategySpecInfo):
    """Blue-green strategy spec — matches BlueGreenStrategySpecGQL structure."""

    auto_promote: bool
    promote_delay_seconds: int


class AccessTokenOrderField(StrEnum):
    """Fields available for ordering access tokens."""

    CREATED_AT = "created_at"


class AutoScalingRuleOrderField(StrEnum):
    """Fields available for ordering auto-scaling rules."""

    CREATED_AT = "created_at"


class ReplicaOrderField(StrEnum):
    """Fields available for ordering deployment replicas."""

    CREATED_AT = "created_at"
    ID = "id"


class EnvironmentVariableEntryInfoDTO(BaseResponseModel):
    """A single environment variable entry with name and value."""

    name: str
    value: str


class EnvironmentVariablesInfoDTO(BaseResponseModel):
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryInfoDTO]


class PreStartActionInfoDTO(BaseResponseModel):
    """Output DTO for a pre-start action in model definition."""

    action: str = Field(description="The name of the pre-start action to execute.")
    args: dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the pre-start action."
    )


class ModelHealthCheckInfoDTO(BaseResponseModel):
    """Output DTO for model health check configuration."""

    interval: float = Field(description="Interval in seconds between health checks.")
    path: str = Field(description="Path to check for health status.")
    max_retries: int = Field(description="Maximum number of retries for health check.")
    max_wait_time: float = Field(
        description="Maximum time in seconds to wait for a health check response."
    )
    expected_status_code: int = Field(
        description="Expected HTTP status code for a healthy response."
    )
    initial_delay: float = Field(
        description="Initial delay in seconds before the first health check."
    )


class ModelServiceConfigInfoDTO(BaseResponseModel):
    """Output DTO for model service configuration."""

    pre_start_actions: list[PreStartActionInfoDTO] = Field(
        default_factory=list,
        description="List of pre-start actions to execute before starting the model service.",
    )
    start_command: str | list[str] = Field(description="Command to start the model service.")
    shell: str = Field(
        default="/bin/bash", description="Shell to use if start_command is a string."
    )
    port: int = Field(description="Port number for the model service.")
    health_check: ModelHealthCheckInfoDTO | None = Field(
        default=None, description="Health check configuration for the model service."
    )


class ModelMetadataInfoDTO(BaseResponseModel):
    """Output DTO for model metadata."""

    author: str | None = Field(default=None, description="Author of the model.")
    title: str | None = Field(default=None, description="Title of the model.")
    version: int | str | None = Field(default=None, description="Version identifier of the model.")
    created: str | None = Field(default=None, description="Creation date of the model.")
    last_modified: str | None = Field(
        default=None, description="Last modification date of the model."
    )
    description: str | None = Field(default=None, description="Description of the model.")
    task: str | None = Field(default=None, description="Task type of the model.")
    category: str | None = Field(default=None, description="Category of the model.")
    architecture: str | None = Field(
        default=None, description="Architecture metadata for the model."
    )
    framework: list[str] | None = Field(default=None, description="Frameworks used by the model.")
    label: list[str] | None = Field(default=None, description="Labels attached to the model.")
    license: str | None = Field(default=None, description="License of the model.")
    min_resource: dict[str, Any] | None = Field(
        default=None, description="Minimum resource requirements for the model."
    )


class ModelConfigInfoDTO(BaseResponseModel):
    """Output DTO for a single model entry in model definition."""

    name: str = Field(description="Name of the model.")
    model_path: str = Field(description="Path to the model file.")
    service: ModelServiceConfigInfoDTO | None = Field(
        default=None, description="Configuration for the model service."
    )
    metadata: ModelMetadataInfoDTO | None = Field(
        default=None, description="Metadata about the model."
    )


class ModelDefinitionInfoDTO(BaseResponseModel):
    """Output DTO for model definition."""

    models: list[ModelConfigInfoDTO] = Field(description="List of models in the model definition.")


class ClusterConfigInfoDTO(BaseResponseModel):
    """Cluster configuration backing DTO for ClusterConfig GQL type.

    mode stores the GQL-compatible string value (e.g. "SINGLE_NODE", "MULTI_NODE")
    matching ClusterModeGQL enum values so Strawberry can auto-convert str→enum.
    """

    mode: str
    size: int


class ResourceConfigInfoDTO(BaseResponseModel):
    """Resource configuration backing DTO for ResourceConfig GQL type."""

    resource_group_name: str
    resource_slots: ResourceSlotInfo
    resource_opts: ResourceOptsInfoDTO | None = None


class ModelRuntimeConfigInfoDTO(BaseResponseModel):
    """Runtime configuration backing DTO for ModelRuntimeConfig GQL type."""

    runtime_variant: str
    inference_runtime_config: dict[str, Any] | None = None
    environ: EnvironmentVariablesInfoDTO | None = None


class ModelMountConfigInfoDTO(BaseResponseModel):
    """Model mount configuration backing DTO for ModelMountConfig GQL type.

    vfolder_id is stored as str (UUID serialised to string) for Strawberry ID
    scalar compatibility so Strawberry can store the value in an ID-typed field
    without additional conversion.
    """

    vfolder_id: str
    mount_destination: str
    definition_path: str


class ExtraVFolderMountGQLDTO(BaseResponseModel):
    """Backing DTO for ExtraVFolderMountInfoGQL type.

    vfolder_id is stored as str (UUID serialised to string) for Strawberry ID
    scalar compatibility.
    """

    vfolder_id: str
    mount_destination: str | None = None


class DeploymentMetadataInfoDTO(BaseResponseModel):
    """Metadata backing DTO for ModelDeploymentMetadata GQL type.

    project_id is stored as str (UUID serialised to string) for Strawberry ID
    scalar compatibility.  status uses ModelDeploymentStatus directly since
    DeploymentStatusGQL is the same object after strawberry.enum registration.
    """

    project_id: str
    domain_name: str
    name: str
    status: ModelDeploymentStatus
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class DeploymentNetworkAccessInfoDTO(BaseResponseModel):
    """Network access backing DTO for ModelDeploymentNetworkAccess GQL type."""

    endpoint_url: str | None = None
    preferred_domain_name: str | None = None
    open_to_public: bool = False


class DeploymentStrategyInfoDTO(BaseResponseModel):
    """Deployment strategy backing DTO for DeploymentStrategyGQL type.

    type uses DeploymentStrategy directly since DeploymentStrategyTypeGQL is the
    same object after strawberry.enum registration.
    """

    type: DeploymentStrategy
