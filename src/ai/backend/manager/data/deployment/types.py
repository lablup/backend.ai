from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Any, Optional
from uuid import UUID

import yarl
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    DeploymentStrategy,
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.common.types import (
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    SessionId,
    VFolderMount,
)
from ai.backend.manager.data.deployment.scale import AutoScalingRule
from ai.backend.manager.data.image.types import ImageIdentifier


class ImageEnvironment(BaseModel):
    image: str = Field(
        description="""
        Container image to use for the model service.
        """,
        examples=[
            "myregistry/myimage:latest",
        ],
    )
    architecture: str = Field(
        description="""
        Architecture of the container image.
        """,
        examples=[
            "x86_64",
            "arm64",
        ],
    )


class ModelServiceDefinition(BaseModel):
    environment: Optional[ImageEnvironment] = Field(
        default=None,
        description="""
        Environment in which the model service will run.
        """,
        examples=[
            {
                "image": "myregistry/myimage:latest",
                "architecture": "x86_64",
            }
        ],
    )
    resource_slots: Optional[dict[str, Any]] = Field(
        default=None,
        description="""
        Resource slots used by the model service session.
        """,
        examples=[
            {"cpu": 1, "mem": "2gb"},
        ],
    )
    environ: Optional[dict[str, str]] = Field(
        default=None,
        description="""
        Environment variables to set for the model service.
        """,
        examples=[
            {"MY_ENV_VAR": "value", "ANOTHER_VAR": "another_value"},
        ],
    )


class RouteStatus(enum.Enum):
    PROVISIONING = "provisioning"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED_TO_START = "failed_to_start"

    @classmethod
    @lru_cache(maxsize=1)
    def active_route_statuses(cls) -> set["RouteStatus"]:
        return {RouteStatus.PROVISIONING, RouteStatus.HEALTHY, RouteStatus.UNHEALTHY}

    @classmethod
    @lru_cache(maxsize=1)
    def inactive_route_statuses(cls) -> set["RouteStatus"]:
        return {RouteStatus.TERMINATING, RouteStatus.TERMINATED, RouteStatus.FAILED_TO_START}

    def is_active(self) -> bool:
        return self in self.active_route_statuses()

    def is_inactive(self) -> bool:
        return self in self.inactive_route_statuses()

    def termination_priority(self) -> int:
        priority_map = {
            RouteStatus.UNHEALTHY: 1,
            RouteStatus.PROVISIONING: 2,
            RouteStatus.HEALTHY: 3,
        }
        return priority_map.get(self, 0)


@dataclass
class DeploymentMetadata:
    name: str
    domain: str
    project: UUID
    resource_group: str
    created_user: UUID
    session_owner: UUID
    created_at: Optional[datetime]
    tag: Optional[str] = None


@dataclass
class DeploymentState:
    lifecycle: EndpointLifecycle
    retry_count: int


@dataclass
class MountSpec:
    mounts: list[UUID]
    mount_map: Mapping[UUID, str]
    mount_options: Mapping[UUID, dict[str, Any]]


@dataclass
class MountInfo:
    vfolder_id: UUID
    kernel_path: PurePosixPath


@dataclass
class MountMetadata:
    model_vfolder_id: UUID
    model_definition_path: Optional[str] = None
    model_mount_destination: str = "/models"
    extra_mounts: list[VFolderMount] = field(default_factory=list)

    def to_mount_spec(self) -> MountSpec:
        mounts = [
            self.model_vfolder_id,
            *[m.vfid.folder_id for m in self.extra_mounts],
        ]
        mount_map = {
            self.model_vfolder_id: self.model_mount_destination,
            **{m.vfid.folder_id: m.kernel_path.as_posix() for m in self.extra_mounts},
        }
        mount_options = {m.vfid.folder_id: {"permission": m.mount_perm} for m in self.extra_mounts}
        return MountSpec(mounts=mounts, mount_map=mount_map, mount_options=mount_options)


@dataclass
class ReplicaSpec:
    replica_count: int
    desired_replica_count: Optional[int] = None

    @property
    def target_replica_count(self) -> int:
        if self.desired_replica_count is not None:
            return self.desired_replica_count
        return self.replica_count


class ConfiguredModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ResourceSpec(ConfiguredModel):
    """
    Resource specification with required resource_slots.

    Used in final ModelRevisionSpec after merging with service definition.
    """

    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: Mapping[str, Any]
    resource_opts: Optional[Mapping[str, Any]] = None


class ExecutionSpec(ConfiguredModel):
    """Execution specification for model service."""

    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    environ: Optional[dict[str, str]] = None
    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    callback_url: Optional[yarl.URL] = None
    inference_runtime_config: Optional[Mapping[str, Any]] = None


class ModelRevisionSpec(ConfiguredModel):
    """
    Final model revision specification after merging request with service definition.

    All required fields must be present. Pydantic validates this automatically.
    """

    image_identifier: ImageIdentifier
    resource_spec: ResourceSpec
    mounts: MountMetadata
    execution: ExecutionSpec

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("image_identifier")
    @classmethod
    def validate_image_identifier(cls, v: ImageIdentifier) -> ImageIdentifier:
        """Validate image identifier fields are not empty."""
        if not v.canonical or v.canonical.strip() == "":
            raise ValueError("Image canonical must be specified")
        if not v.architecture or v.architecture.strip() == "":
            raise ValueError("Image architecture must be specified")
        return v


class RequestedImageIdentifier(ConfiguredModel):
    """
    Requested image identifier with optional fields.

    Fields are optional to allow service definition to provide them.
    """

    canonical: Optional[str]
    architecture: Optional[str]


class RequestedResourceSpec(ConfiguredModel):
    """
    Requested resource specification with optional resource_slots.

    resource_slots is optional to allow service definition to provide it.
    """

    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: Optional[Mapping[str, Any]]
    resource_opts: Optional[Mapping[str, Any]] = None


class RequestedModelRevisionSpec(ConfiguredModel):
    """
    Requested model revision specification from API.
    """

    image_identifier: RequestedImageIdentifier
    resource_spec: RequestedResourceSpec
    mounts: MountMetadata
    execution: ExecutionSpec


@dataclass
class DeploymentNetworkSpec:
    open_to_public: bool
    access_token_ids: Optional[list[UUID]] = None
    url: Optional[str] = None
    preferred_domain_name: Optional[str] = None


@dataclass
class DeploymentInfo:
    id: UUID
    metadata: DeploymentMetadata
    state: DeploymentState
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revisions: list[ModelRevisionSpec]

    def target_revision(self) -> Optional[ModelRevisionSpec]:
        if self.model_revisions:
            return self.model_revisions[0]
        return None


@dataclass
class DeploymentSessionSpec:
    id: UUID
    metadata: DeploymentMetadata


@dataclass
class ScaleOutDecision:
    deployment_info: DeploymentInfo
    new_replica_count: int


@dataclass
class DefinitionFiles:
    service_definition: Optional[dict[str, Any]]
    model_definition: dict[str, Any]


@dataclass
class RouteInfo:
    """Route information for deployment."""

    route_id: UUID
    endpoint_id: UUID
    session_id: Optional[SessionId]
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime
    error_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentInfoWithRoutes:
    """DeploymentInfo with its routes."""

    deployment_info: DeploymentInfo
    routes: list[RouteInfo] = field(default_factory=list)


@dataclass
class DeploymentInfoWithAutoScalingRules:
    """DeploymentInfo with its autoscaling rules."""

    deployment_info: DeploymentInfo
    rules: list[AutoScalingRule] = field(default_factory=list)


@dataclass
class ModelDeploymentAutoScalingRuleData:
    id: UUID
    model_deployment_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Optional[Decimal]
    max_threshold: Optional[Decimal]
    step_size: int
    time_window: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]
    created_at: datetime
    last_triggered_at: datetime


@dataclass
class ModelDeploymentAccessTokenData:
    id: UUID
    token: str
    valid_until: datetime
    created_at: datetime


@dataclass
class ModelReplicaData:
    id: UUID
    revision_id: UUID
    session_id: UUID
    readiness_status: ReadinessStatus
    liveness_status: LivenessStatus
    activeness_status: ActivenessStatus
    weight: int
    detail: dict[str, Any]
    created_at: datetime
    live_stat: dict[str, Any]


@dataclass
class ClusterConfigData:
    mode: ClusterMode
    size: int


@dataclass
class ResourceConfigData:
    resource_group_name: str
    resource_slot: ResourceSlot
    resource_opts: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class ModelRuntimeConfigData:
    runtime_variant: RuntimeVariant
    inference_runtime_config: Optional[Mapping[str, Any]] = None
    environ: Optional[dict[str, Any]] = None


@dataclass
class ModelMountConfigData:
    vfolder_id: UUID
    mount_destination: str
    definition_path: str


@dataclass
class ExtraVFolderMountData:
    vfolder_id: UUID
    mount_destination: str


@dataclass
class ModelRevisionData:
    id: UUID
    name: str
    cluster_config: ClusterConfigData
    resource_config: ResourceConfigData
    model_runtime_config: ModelRuntimeConfigData
    model_mount_config: ModelMountConfigData
    created_at: datetime
    image_id: UUID
    extra_vfolder_mounts: list[ExtraVFolderMountData] = field(default_factory=list)


@dataclass
class ModelDeploymentMetadataInfo:
    name: str
    status: ModelDeploymentStatus
    tags: list[str]
    project_id: UUID
    domain_name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ReplicaStateData:
    desired_replica_count: int
    replica_ids: list[UUID]


@dataclass
class ModelDeploymentData:
    id: UUID
    metadata: ModelDeploymentMetadataInfo
    network_access: DeploymentNetworkSpec
    revision: Optional[ModelRevisionData]
    revision_history_ids: list[UUID]
    scaling_rule_ids: list[UUID]
    replica_state: ReplicaStateData
    default_deployment_strategy: DeploymentStrategy
    created_user_id: UUID
    access_token_ids: Optional[UUID] = None


class DeploymentOrderField(enum.StrEnum):
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    NAME = "NAME"


class ModelRevisionOrderField(enum.StrEnum):
    CREATED_AT = "CREATED_AT"
    NAME = "NAME"


class ReplicaOrderField(enum.StrEnum):
    CREATED_AT = "CREATED_AT"
    ID = "ID"


class AccessTokenOrderField(enum.StrEnum):
    CREATED_AT = "CREATED_AT"
