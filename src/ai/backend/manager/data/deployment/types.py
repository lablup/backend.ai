from __future__ import annotations

import dataclasses
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

from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    DeploymentStrategy,
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.manager.errors.deployment import DeploymentRevisionNotFound

if TYPE_CHECKING:
    from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
    from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec

from ai.backend.common.types import (
    AutoScalingMetricSource,
    ClusterMode,
    MountPermission,
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


class DeploymentConfig(BaseModel):
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
    resource_opts: dict[str, Any] | None = Field(
        default=None,
        description="""
        Resource options for the model service session (e.g., shmem).
        """,
        examples=[
            {"shmem": "16g"},
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
    """Lifecycle status of a route (independent of health)."""

    PROVISIONING = "provisioning"
    RUNNING = "running"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED_TO_START = "failed_to_start"

    @classmethod
    @lru_cache(maxsize=1)
    def active_route_statuses(cls) -> set[RouteStatus]:
        return {
            RouteStatus.PROVISIONING,
            RouteStatus.RUNNING,
        }

    @classmethod
    @lru_cache(maxsize=1)
    def inactive_route_statuses(cls) -> set[RouteStatus]:
        return {RouteStatus.TERMINATING, RouteStatus.TERMINATED, RouteStatus.FAILED_TO_START}

    def is_active(self) -> bool:
        return self in self.active_route_statuses()

    def is_inactive(self) -> bool:
        return self in self.inactive_route_statuses()


class RouteHealthStatus(enum.Enum):
    """Health check status of a route (independent of lifecycle)."""

    NOT_CHECKED = "not_checked"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class RouteHandlerCategory(enum.StrEnum):
    """Category of route handler for history separation."""

    LIFECYCLE = "lifecycle"
    HEALTH = "health"


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


class DeploymentLifecycleSubStep(enum.StrEnum):
    """Sub-steps within deployment lifecycle phases.

    Member names are prefixed with the lifecycle phase they belong to
    (e.g. ``DEPLOYING_``).  String values are stored in the database as-is.
    """

    # -- DEPLOYING phase --
    DEPLOYING_PROVISIONING = "deploying_provisioning"
    """New revision routes are being provisioned and old routes are being drained."""
    DEPLOYING_ROLLING_BACK = "deploying_rolling_back"
    """Clearing deploying_revision and transitioning to READY."""
    DEPLOYING_COMPLETED = "deploying_completed"
    """All strategy conditions satisfied; triggers revision swap."""

    @classmethod
    def deploying_handler_sub_steps(cls) -> tuple[DeploymentLifecycleSubStep, ...]:
        """Sub-steps that have their own deploying handler (excludes COMPLETED, which is an evaluator outcome)."""
        return (cls.DEPLOYING_PROVISIONING, cls.DEPLOYING_ROLLING_BACK)


@dataclass(frozen=True)
class DeploymentLifecycleStatus:
    """Target lifecycle state for a deployment status transition.

    Pairs an EndpointLifecycle with an optional sub-step to provide
    context about which sub-step led to this transition.

    Attributes:
        lifecycle: The target endpoint lifecycle state
        sub_step: Optional sub-step indicating what determined this
            transition (e.g. DEPLOYING_* members for DEPLOYING handlers).
    """

    lifecycle: EndpointLifecycle
    sub_step: DeploymentLifecycleSubStep | None = None


@dataclass(frozen=True)
class DeploymentStatusTransitions:
    """Status transitions for deployment handlers.

    Attributes:
        success: Target lifecycle when handler succeeds, None means no change
        need_retry: Target lifecycle when handler fails but can retry, or when
            route mutations were executed but the deployment stays in the same
            sub-step (e.g. PROVISIONING → PROVISIONING after create/drain).
            Items explicitly returned as need_retry by handlers are never
            escalated to give_up — they represent normal progress.
        expired: Target lifecycle when time elapsed in current state
        give_up: Target lifecycle when retry count exceeded
    """

    success: DeploymentLifecycleStatus | None = None
    need_retry: DeploymentLifecycleStatus | None = None
    expired: DeploymentLifecycleStatus | None = None
    give_up: DeploymentLifecycleStatus | None = None


@dataclass(frozen=True)
class RouteTargetStatuses:
    """Target statuses for route handler filtering (lifecycle x health)."""

    lifecycle: list[RouteStatus]
    health: list[RouteHealthStatus]


@dataclass(frozen=True)
class RouteTransitionTarget:
    """Target state for a route transition (lifecycle + health)."""

    status: RouteStatus | None = None
    health_status: RouteHealthStatus | None = None


@dataclass(frozen=True)
class RouteStatusTransitions:
    """Status transitions for route handlers.

    Route handlers have success/failure/stale outcomes (no expired/give_up).
    Each outcome can change lifecycle status, health status, or both.

    Attributes:
        success: Target state when handler succeeds, None means no change
        failure: Target state when handler fails, None means no change
        stale: Target state when route becomes stale, None means no change
    """

    success: RouteTransitionTarget | None = None
    failure: RouteTransitionTarget | None = None
    stale: RouteTransitionTarget | None = None


@dataclass
class ScalingGroupCleanupConfig:
    """Cleanup configuration for a scaling group."""

    scaling_group_name: str
    cleanup_target_statuses: list[RouteHealthStatus]


@dataclass
class DeploymentMetadata:
    name: str
    domain: str
    project: UUID
    resource_group: str
    created_user: UUID
    session_owner: UUID
    created_at: datetime | None
    # `None` means "caller did not specify"; the service resolves it against
    # the revision preset default (if any) and ultimately the system default.
    revision_history_limit: int | None = None
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
    kernel_path: PurePosixPath | None = None


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
        mount_options: dict[UUID, dict[str, MountPermission]] = {
            self.model_vfolder_id: {"permission": MountPermission.READ_ONLY},
            **{m.vfid.folder_id: {"permission": m.mount_perm} for m in self.extra_mounts},
        }
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
    runtime_variant: RuntimeVariant
    callback_url: yarl.URL | None = None
    inference_runtime_config: Mapping[str, Any] | None = None


class PresetValueSpec(ConfiguredModel):
    """A runtime variant preset value binding stored in a deployment revision."""

    preset_id: UUID
    value: str


class ModelRevisionSpec(ConfiguredModel):
    revision_id: UUID | None = None
    image_id: UUID | None = None
    image_identifier: ImageIdentifier
    resource_spec: ResourceSpec
    mounts: MountMetadata
    execution: ExecutionSpec
    model_definition: ModelDefinition | None = None
    preset_values: list[PresetValueSpec] = Field(default_factory=list)

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
class RevisionDraft:
    """Intermediate representation for revision creation with all fields optional.

    Three drafts are created from different sources and merged with priority:
    model_definition (base) → preset (override) → request (highest priority).
    Only non-None fields participate in the merge.
    """

    image_id: UUID | None = None
    resource_slots: Mapping[str, Any] | None = None
    resource_opts: Mapping[str, Any] | None = None
    cluster_mode: ClusterMode | None = None
    cluster_size: int | None = None
    startup_command: str | None = None
    bootstrap_script: str | None = None
    environ: dict[str, str] | None = None
    runtime_variant: RuntimeVariant | None = None
    model_definition: ModelDefinition | None = None


def merge_revision_drafts(*drafts: RevisionDraft) -> RevisionDraft:
    """Merge multiple RevisionDrafts with later drafts taking priority.

    For most fields: later non-None value overwrites earlier.
    For environ: dict merge (later keys overwrite earlier keys).
    """
    result = RevisionDraft()
    merged_environ: dict[str, str] = {}
    merged_resource_slots: dict[str, Any] = {}
    merged_resource_opts: dict[str, Any] = {}

    for draft in drafts:
        if draft.image_id is not None:
            result = dataclasses.replace(result, image_id=draft.image_id)
        if draft.resource_slots is not None:
            merged_resource_slots.update(draft.resource_slots)
        if draft.resource_opts is not None:
            merged_resource_opts.update(draft.resource_opts)
        if draft.cluster_mode is not None:
            result = dataclasses.replace(result, cluster_mode=draft.cluster_mode)
        if draft.cluster_size is not None:
            result = dataclasses.replace(result, cluster_size=draft.cluster_size)
        if draft.startup_command is not None:
            result = dataclasses.replace(result, startup_command=draft.startup_command)
        if draft.bootstrap_script is not None:
            result = dataclasses.replace(result, bootstrap_script=draft.bootstrap_script)
        if draft.environ is not None:
            merged_environ.update(draft.environ)
        if draft.runtime_variant is not None:
            result = dataclasses.replace(result, runtime_variant=draft.runtime_variant)
        if draft.model_definition is not None:
            result = dataclasses.replace(result, model_definition=draft.model_definition)

    if merged_resource_slots:
        result = dataclasses.replace(result, resource_slots=merged_resource_slots)
    if merged_resource_opts:
        result = dataclasses.replace(result, resource_opts=merged_resource_opts)
    if merged_environ:
        result = dataclasses.replace(result, environ=merged_environ)

    return result


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
    policy: DeploymentPolicyData | None = None
    deploying_revision_id: UUID | None = None
    sub_step: DeploymentLifecycleSubStep | None = None

    def resolve_revision_spec(self, revision_id: UUID) -> ModelRevisionSpec:
        """Find a ModelRevisionSpec by revision_id from model_revisions.

        Raises:
            DeploymentRevisionNotFound: If the revision is not found.
        """
        for revision in self.model_revisions:
            if revision.revision_id == revision_id:
                return revision
        raise DeploymentRevisionNotFound(
            f"Revision {revision_id} not found in model_revisions of deployment {self.id}"
        )


@dataclass
class DeploymentWithHistory:
    """Bundles a deployment with its scheduling history context.

    This is the primary data unit for deployment coordinator operations,
    analogous to SessionWithKernels for session scheduling.

    Attributes:
        deployment_info: Deployment information including lifecycle data
        phase_attempts: Number of attempts for current phase from scheduling history
                       (used for failure classification: give_up when >= max_retries)
        phase_started_at: When the current phase started from scheduling history
                         (used for failure classification: expired when timeout exceeded)
    """

    deployment_info: DeploymentInfo
    phase_attempts: int = 0
    phase_started_at: datetime | None = None


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
    deployment_config: dict[str, Any] | None
    model_definition: dict[str, Any]


_HEALTH_TERMINATION_PRIORITY: dict[RouteHealthStatus, int] = {
    RouteHealthStatus.UNHEALTHY: 1,
    RouteHealthStatus.DEGRADED: 2,
    RouteHealthStatus.NOT_CHECKED: 3,
    RouteHealthStatus.HEALTHY: 4,
}


@dataclass
class RouteInfo:
    """Route information for deployment."""

    route_id: UUID
    endpoint_id: UUID
    session_id: SessionId | None
    status: RouteStatus
    health_status: RouteHealthStatus
    traffic_ratio: float
    created_at: datetime
    revision_id: UUID
    traffic_status: RouteTrafficStatus
    error_data: dict[str, Any] = field(default_factory=dict)

    @property
    def termination_priority(self) -> int:
        """Priority for scale-in termination (lower = terminated first).

        Non-RUNNING routes are terminated first (0).
        Among RUNNING routes: UNHEALTHY(1) > DEGRADED(2) > NOT_CHECKED(3) > HEALTHY(4).
        """
        if self.status != RouteStatus.RUNNING:
            return 0
        return _HEALTH_TERMINATION_PRIORITY.get(self.health_status, 0)


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
    prometheus_query_preset_id: UUID | None = None


@dataclass
class ModelDeploymentAccessTokenData:
    id: UUID
    token: str
    expires_at: datetime | None
    created_at: datetime


@dataclass
class ModelReplicaData:
    id: UUID
    revision_id: UUID
    session_id: UUID
    readiness_status: ReadinessStatus
    liveness_status: LivenessStatus
    activeness_status: ActivenessStatus
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
    model_definition: ModelDefinition | None = None
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
    policy: DeploymentPolicyData | None = None
    access_token_ids: list[UUID] | None = None
    sub_step: DeploymentLifecycleSubStep | None = None


@dataclass(frozen=True)
class DeploymentSummaryData:
    id: UUID
    name: str
    created_user: UUID
    session_owner: UUID
    domain: str
    project: UUID
    resource_group: str
    lifecycle_stage: EndpointLifecycle
    tag: str | None
    open_to_public: bool
    url: str | None
    current_revision: UUID | None
    deploying_revision: UUID | None
    replicas: int
    desired_replicas: int | None
    created_at: datetime | None
    destroyed_at: datetime | None
    sub_step: DeploymentLifecycleSubStep | None


@dataclass
class DeploymentSummarySearchResult:
    items: list[DeploymentSummaryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


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
    """Domain model for route history.

    from_status/to_status contain the relevant status for the category:
    - category=lifecycle: lifecycle status values (provisioning, running, etc.)
    - category=health: health status values (healthy, unhealthy, etc.)
    """

    id: UUID
    route_id: UUID
    deployment_id: UUID

    category: str  # RouteHandlerCategory value
    phase: str  # RouteLifecycleType value
    from_status: str | None
    to_status: str | None

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
    created_at: datetime
    updated_at: datetime


@dataclass
class DeploymentPolicyUpsertResult:
    """Result of upserting a deployment policy."""

    data: DeploymentPolicyData
    created: bool


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


# ---------------------------------------------------------------------------
# Search scope types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RouteSearchScope:
    """Scope for searching routes within a specific deployment."""

    deployment_id: UUID


@dataclass(frozen=True)
class ReplicaSearchScope:
    """Scope for searching replicas within a specific deployment."""

    deployment_id: UUID


@dataclass(frozen=True)
class AccessTokenSearchScope:
    """Scope for searching access tokens within a specific deployment."""

    deployment_id: UUID


@dataclass(frozen=True)
class AutoScalingRuleSearchScope:
    """Scope for searching auto-scaling rules within a specific deployment."""

    deployment_id: UUID


@dataclass(frozen=True)
class RevisionSearchScope:
    """Scope for searching revisions within a specific deployment."""

    deployment_id: UUID
