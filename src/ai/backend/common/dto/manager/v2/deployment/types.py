"""
Common types for Deployment DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

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
    "ModelDeploymentStatus",
    "ModelMountConfigInfoDTO",
    "ModelRuntimeConfigInfoDTO",
    "NetworkConfigInfo",
    "OrderDirection",
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

    max_surge: int
    max_unavailable: int


class BlueGreenConfigInfo(BaseResponseModel):
    """Blue/green deployment policy configuration."""

    auto_promote: bool
    promote_delay_seconds: int


class DeploymentPolicyInfo(BaseResponseModel):
    """Deployment update policy information."""

    strategy: DeploymentStrategy
    rollback_on_failure: bool
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

    max_surge: int
    max_unavailable: int


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
