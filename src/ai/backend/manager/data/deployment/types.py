from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any
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

if TYPE_CHECKING:
    from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
    from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec

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
    environment: ImageEnvironment | None = Field(
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
    resource_slots: dict[str, Any] | None = Field(
        default=None,
        description="""
        Resource slots used by the model service session.
        """,
        examples=[
            {"cpu": 1, "mem": "2gb"},
        ],
    )
    environ: dict[str, str] | None = Field(
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
    DEGRADED = "degraded"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED_TO_START = "failed_to_start"

    @classmethod
    @lru_cache(maxsize=1)
    def active_route_statuses(cls) -> set[RouteStatus]:
        return {
            RouteStatus.PROVISIONING,
            RouteStatus.HEALTHY,
            RouteStatus.UNHEALTHY,
            RouteStatus.DEGRADED,
        }

    @classmethod
    @lru_cache(maxsize=1)
    def inactive_route_statuses(cls) -> set[RouteStatus]:
        return {RouteStatus.TERMINATING, RouteStatus.TERMINATED, RouteStatus.FAILED_TO_START}

    def is_active(self) -> bool:
        return self in self.active_route_statuses()

    def is_inactive(self) -> bool:
        return self in self.inactive_route_statuses()

    def termination_priority(self) -> int:
        priority_map = {
            RouteStatus.UNHEALTHY: 1,
            RouteStatus.DEGRADED: 2,
            RouteStatus.PROVISIONING: 3,
            RouteStatus.HEALTHY: 4,
        }
        return priority_map.get(self, 0)


class RouteTrafficStatus(enum.StrEnum):
    """Traffic routing status for a route.

    Controls whether traffic should be sent to this route.
    Actual traffic delivery depends on RouteStatus being HEALTHY.

    - ACTIVE: Traffic enabled (will receive traffic when RouteStatus is HEALTHY)
    - INACTIVE: Traffic disabled (will not receive traffic regardless of RouteStatus)
    """

    ACTIVE = "active"
    INACTIVE = "inactive"


# ========== Status Transition Types (BEP-1030) ==========


@dataclass(frozen=True)
class DeploymentStatusTransitions:
    """Status transitions for deployment handlers.

    Deployment handlers only have success/failure outcomes (no expired/give_up).

    Attributes:
        success: Target lifecycle when handler succeeds, None means no change
        failure: Target lifecycle when handler fails, None means no change
    """

    success: EndpointLifecycle | None = None
    failure: EndpointLifecycle | None = None


@dataclass(frozen=True)
class RouteStatusTransitions:
    """Status transitions for route handlers.

    Route handlers have success/failure/stale outcomes (no expired/give_up).

    Attributes:
        success: Target status when handler succeeds, None means no change
        failure: Target status when handler fails, None means no change
        stale: Target status when route becomes stale, None means no change
    """

    success: RouteStatus | None = None
    failure: RouteStatus | None = None
    stale: RouteStatus | None = None


@dataclass
class ScalingGroupCleanupConfig:
    """Cleanup configuration for a scaling group."""

    scaling_group_name: str
    cleanup_target_statuses: list[RouteStatus]


@dataclass
class DeploymentMetadata:
    name: str
    domain: str
    project: UUID
    resource_group: str
    created_user: UUID
    session_owner: UUID
    created_at: datetime | None
    revision_history_limit: int
    tag: str | None = None


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
    model_definition_path: str | None = None
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
    desired_replica_count: int | None = None

    @property
    def target_replica_count(self) -> int:
        if self.desired_replica_count is not None:
            return self.desired_replica_count
        return self.replica_count


class ConfiguredModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ResourceSpec(ConfiguredModel):
    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: Mapping[str, Any]
    resource_opts: Mapping[str, Any] | None = None


class ExecutionSpec(ConfiguredModel):
    startup_command: str | None = None
    bootstrap_script: str | None = None
    environ: dict[str, str] | None = None
    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    callback_url: yarl.URL | None = None
    inference_runtime_config: Mapping[str, Any] | None = None


class ModelRevisionSpec(ConfiguredModel):
    image_identifier: ImageIdentifier
    resource_spec: ResourceSpec
    mounts: MountMetadata
    execution: ExecutionSpec

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("image_identifier")
    @classmethod
    def validate_image_identifier(cls, v: ImageIdentifier) -> ImageIdentifier:
        if not v.canonical or v.canonical.strip() == "":
            raise ValueError("Image canonical must be specified")
        if not v.architecture or v.architecture.strip() == "":
            raise ValueError("Image architecture must be specified")
        return v


class ImageIdentifierDraft(ConfiguredModel):
    canonical: str | None
    architecture: str | None


class ResourceSpecDraft(ConfiguredModel):
    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: Mapping[str, Any] | None
    resource_opts: Mapping[str, Any] | None = None


class ModelRevisionSpecDraft(ConfiguredModel):
    image_identifier: ImageIdentifierDraft
    resource_spec: ResourceSpecDraft
    mounts: MountMetadata
    execution: ExecutionSpec


@dataclass
class DeploymentNetworkSpec:
    open_to_public: bool
    access_token_ids: list[UUID] | None = None
    url: str | None = None
    preferred_domain_name: str | None = None


@dataclass
class DeploymentInfo:
    id: UUID
    metadata: DeploymentMetadata
    state: DeploymentState
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revisions: list[ModelRevisionSpec]
    current_revision_id: UUID | None = None

    def target_revision(self) -> ModelRevisionSpec | None:
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
    target_revision_id: UUID | None = None


@dataclass
class DefinitionFiles:
    service_definition: dict[str, Any] | None
    model_definition: dict[str, Any]


@dataclass
class RouteInfo:
    """Route information for deployment."""

    route_id: UUID
    endpoint_id: UUID
    session_id: SessionId | None
    status: RouteStatus
    traffic_ratio: float
    created_at: datetime | None
    revision_id: UUID | None
    traffic_status: RouteTrafficStatus
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
    min_threshold: Decimal | None
    max_threshold: Decimal | None
    step_size: int
    time_window: int
    min_replicas: int | None
    max_replicas: int | None
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
    inference_runtime_config: Mapping[str, Any] | None = None
    environ: dict[str, Any] | None = None


@dataclass
class ModelMountConfigData:
    vfolder_id: UUID | None
    mount_destination: str | None
    definition_path: str


@dataclass
class ExtraVFolderMountData:
    vfolder_id: UUID
    mount_destination: str  # PurePosixPath should be converted to str


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
    revision: ModelRevisionData | None
    revision_history_ids: list[UUID]
    scaling_rule_ids: list[UUID]
    replica_state: ReplicaStateData
    default_deployment_strategy: DeploymentStrategy
    created_user_id: UUID
    access_token_ids: UUID | None = None


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


class AutoScalingRuleOrderField(enum.StrEnum):
    CREATED_AT = "CREATED_AT"


# ========== Scheduling History Types ==========


@dataclass
class DeploymentHistoryData:
    """Domain model for deployment history."""

    id: UUID
    deployment_id: UUID

    phase: str  # DeploymentLifecycleType value
    from_status: ModelDeploymentStatus | None
    to_status: ModelDeploymentStatus | None

    result: SchedulingResult
    error_code: str | None
    message: str

    sub_steps: list[SubStepResult]

    attempts: int
    created_at: datetime
    updated_at: datetime


@dataclass
class RouteHistoryData:
    """Domain model for route history."""

    id: UUID
    route_id: UUID
    deployment_id: UUID

    phase: str  # RouteLifecycleType value
    from_status: RouteStatus | None
    to_status: RouteStatus | None

    result: SchedulingResult
    error_code: str | None
    message: str

    sub_steps: list[SubStepResult]

    attempts: int
    created_at: datetime
    updated_at: datetime


@dataclass
class DeploymentHistoryListResult:
    """Search result with pagination for deployment history."""

    items: list[DeploymentHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class RouteHistoryListResult:
    """Search result with pagination for route history."""

    items: list[RouteHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class RevisionSearchResult:
    """Search result with pagination for deployment revisions."""

    items: list[ModelRevisionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class RouteSearchResult:
    """Search result with pagination for routes."""

    items: list[RouteInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class DeploymentSearchResult:
    """Search result with pagination for deployments."""

    items: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class DeploymentInfoSearchResult:
    """Search result with pagination for deployment info."""

    items: list[DeploymentInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class AutoScalingRuleSearchResult:
    """Search result with pagination for auto-scaling rules."""

    items: list[ModelDeploymentAutoScalingRuleData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class DeploymentPolicyData:
    """Data class for DeploymentPolicyRow."""

    id: UUID
    endpoint: UUID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    rollback_on_failure: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class DeploymentPolicySearchResult:
    """Search result with pagination for deployment policies."""

    items: list[DeploymentPolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class AccessTokenSearchResult:
    """Search result with pagination for access tokens."""

    items: list[ModelDeploymentAccessTokenData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
