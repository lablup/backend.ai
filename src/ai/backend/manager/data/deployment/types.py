from __future__ import annotations

import enum
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING, Any
from uuid import UUID

import yarl
from pydantic import ConfigDict, Field

from ai.backend.common.config import ModelDefinition, ModelDefinitionDraft, ModelHealthCheck
from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    DeploymentStrategy,
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.reconciler.types import BaseReconcilerCategory
from ai.backend.manager.data.session.options import HandlerOptions

if TYPE_CHECKING:
    from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
    from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec

from ai.backend.common.types import (
    AutoScalingMetricSource,
    BackendAISchema,
    ClusterMode,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
    SessionId,
)
from ai.backend.manager.data.deployment.scale import AutoScalingRule
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    PresetValueData,
    ResourceSlotEntryData,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData


class DeploymentConfig(BackendAISchema):
    """``deployment-config.yaml`` payload after repository-side resolution.

    The raw yaml carries ``image`` + ``architecture`` strings; the repository
    resolves that pair to ``image_id`` before constructing this type, so
    downstream code never sees the canonical / architecture tuple.
    """

    image_id: ImageID | None = None
    resource_slots: dict[str, Any] | None = None
    resource_opts: dict[str, Any] | None = None
    environ: dict[str, str] | None = None


@dataclass(frozen=True)
class FetchedModelDefinition:
    """Model definition draft with the vfolder path it was read from.

    ``path`` is the matched candidate path inside the model vfolder.
    """

    path: str
    model_definition: ModelDefinitionDraft


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
    SYNC = "sync"


class DeploymentHandlerCategory(enum.StrEnum):
    """Category of deployment-level handler for history separation.

    Separate from :class:`RouteHandlerCategory` because deployment-level
    handlers operate on the endpoint as a whole (lifecycle, replica
    reconciliation, aggregate health) while route-level handlers act on
    individual routes (provisioning, per-route health). Storing them
    under distinct category sets keeps the history queryable by the
    correct axis.
    """

    LIFECYCLE = "lifecycle"
    """Lifecycle progression (PENDING → DEPLOYING → READY → DESTROYING → DESTROYED)."""
    SCALING = "scaling"
    """Replica reconciliation against ``desired_replica_count`` while the
    endpoint's own lifecycle stays put at READY."""
    HEALTH = "health"
    """Deployment-level health aggregation (e.g. marking an endpoint
    BLOCKED when every route is unhealthy). Reserved — no handler
    currently emits this category; kept so the history axis is symmetric
    with :class:`RouteHandlerCategory` and future aggregate-health
    handlers can file under it without a schema change."""


class RouteTrafficStatus(enum.StrEnum):
    """Traffic routing status for a route.

    Controls whether traffic should be sent to this route.
    Actual traffic delivery depends on RouteStatus being HEALTHY.

    - ACTIVE: Traffic enabled (will receive traffic when RouteStatus is HEALTHY)
    - INACTIVE: Traffic disabled (will not receive traffic regardless of RouteStatus)
    """

    ACTIVE = "active"
    INACTIVE = "inactive"


class RouteSubStatus(enum.StrEnum):
    """Sub-status for routes in the PROVISIONING lifecycle stage.

    Tracks fine-grained progress within the provisioning pipeline:
    - PENDING: session has been enqueued, waiting for scheduler
    - STARTING: session is running, waiting for replica host/port
    - WARMING_UP: replica is up, waiting for health check to pass
    """

    PENDING = "pending"
    STARTING = "starting"
    WARMING_UP = "warming_up"


class ReplicaGroupLifecycle(enum.StrEnum):
    """Lifecycle of a replica group: rollout progress and retirement."""

    ROLLING = "rolling"
    STABLE = "stable"
    FAILED = "failed"
    DRAINING = "draining"
    DRAINED = "drained"


class ReplicaGroupScalingStatus(enum.StrEnum):
    """Whether the group's actual replica count matches its desired count."""

    SCALING = "scaling"
    STABLE = "stable"


class ReplicaGroupHandlerCategory(BaseReconcilerCategory):
    """Category of replica-group handler for history separation; also the reconcile-stage category."""

    SCALING = "scaling"
    LIFECYCLE = "lifecycle"


# ========== Status Transition Types (BEP-1030) ==========


class DeploymentLifecycleSubStep(enum.StrEnum):
    """Sub-steps within deployment lifecycle phases.

    Member names are prefixed with the lifecycle phase they belong to
    (e.g. ``DEPLOYING_``).  String values are stored in the database as-is.
    """

    # -- DEPLOYING phase --
    DEPLOYING_INITIALIZING = "deploying_initializing"
    """Pre-deploy cleanup of stale replica groups and creation of the target
    replica group for the selected revision."""
    DEPLOYING_PROVISIONING = "deploying_provisioning"
    """New revision routes are being provisioned and old routes are being drained."""
    DEPLOYING_PROMOTING = "deploying_promoting"
    """The fully provisioned target replica group is being promoted to primary."""
    DEPLOYING_DRAINING = "deploying_draining"
    """The superseded replica group is being drained and removed."""
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
    """Target state for a deployment status transition.

    All three axes (``lifecycle``, ``scaling_state``, ``sub_step``) are
    independently optional — ``None`` on an axis means "leave this
    dimension unchanged". Pure lifecycle handlers set ``lifecycle`` and
    leave the scaling axis untouched; scaling-category handlers invert
    that relationship so the same endpoint can move on the scaling axis
    while its lifecycle (e.g. ``READY`` or ``DEPLOYING``) is preserved.

    Endpoint-level aggregate health is tracked separately at the route
    layer and is not part of this status — when the HEALTH handler
    category is introduced it will add its own axis alongside a new
    persisted column.

    Attributes:
        lifecycle: Target endpoint lifecycle state; ``None`` means
            "do not touch the lifecycle dimension" (scaling-only
            transitions).
        scaling_state: Target scaling state; ``None`` means
            "do not touch the scaling dimension".
        sub_step: Optional sub-step indicating what determined this
            transition (e.g. DEPLOYING_* members for DEPLOYING handlers).
    """

    lifecycle: EndpointLifecycle | None = None
    scaling_state: ScalingState | None = None
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
class DeploymentTargetStatuses:
    """Per-axis filter declaration for a deployment handler.

    Each list enumerates the axis values the handler wants to be
    dispatched against. Empty lists disable that axis's filter (the
    coordinator simply omits the corresponding ``IN`` predicate).

    Attributes:
        lifecycle_stages: Lifecycle values the handler processes.
        scaling_states: Scaling-state values; typically ``[STABLE]`` for
            detectors (replica / reconcile) and ``[SCALING]`` for the
            scaling handler. Empty means "do not restrict by scaling".
        sub_steps: Sub-step values; used by DEPLOYING handlers to pick
            the PROVISIONING vs ROLLING_BACK slice. Empty means "all
            sub-steps".
    """

    lifecycle_stages: list[EndpointLifecycle]
    scaling_states: list[ScalingState] = field(default_factory=list)
    sub_steps: list[DeploymentLifecycleSubStep] = field(default_factory=list)


@dataclass(frozen=True)
class RouteTargetStatuses:
    """Target statuses for route handler filtering.

    Each axis is optional — ``None`` skips that predicate entirely.
    Pass a non-empty list to restrict to specific values on that axis.
    """

    lifecycle: list[RouteStatus] | None = None
    health: list[RouteHealthStatus] | None = None
    traffic: list[RouteTrafficStatus] | None = None
    sub_status: list[RouteSubStatus] | None = None


@dataclass(frozen=True)
class RouteTransitionTarget:
    """Target state for a route transition."""

    status: RouteStatus | None = None
    health_status: RouteHealthStatus | None = None
    sub_status: RouteSubStatus | None = None
    traffic_status: RouteTrafficStatus | None = None


@dataclass(frozen=True)
class RouteStatusTransitions:
    """Status transitions for route handlers.

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
    # ``scaling_state`` is orthogonal to ``lifecycle``: the lifecycle axis
    # records where the endpoint is in its monotonic DEPLOYING → READY →
    # DESTROYING progression, while ``scaling_state`` tracks whether it is
    # currently reconciling replica count (SCALING) or holding at the
    # desired count (STABLE). Persisted NOT NULL on ``endpoints.scaling_state``
    # (default STABLE) so this field is always populated on reads.
    scaling_state: ScalingState
    retry_count: int


@dataclass
class MountInfo:
    """Input form for an extra mount — ``mount_perm=None`` means the
    caller did not override and the revision-write step should pick up
    the vfolder's own stored permission. An explicit value is used as
    the override directly. Resolved to a concrete ``MountInfoEntry``
    (non-nullable ``mount_perm``) before persisting so the stored row
    becomes an immutable permission snapshot.

    ``subpath`` is the path within the vfolder to mount. ``None`` means
    the vfolder root.
    """

    vfolder_id: VFolderUUID
    mount_destination: str | None = None
    mount_perm: MountPermission | None = None
    subpath: str | None = None


@dataclass
class MountMetadata:
    # Write-path metadata for the model vfolder. ``AddRevisionInput`` requires
    # ``model_mount_config`` so the caller always supplies ``model_vfolder_id``;
    # the underlying ``deployment_revisions.model`` column stays nullable to
    # represent post-hoc SET NULL on vfolder deletion, but no write path
    # constructs this dataclass with ``None``.
    model_vfolder_id: VFolderUUID
    model_definition_path: str | None
    model_mount_destination: str
    extra_mounts: list[MountInfoEntry]
    # Subpath within the model vfolder. ``None`` means the vfolder root.
    vfolder_subpath: str | None = None


@dataclass
class ReplicaSpec:
    replica_count: int
    desired_replica_count: int | None = None

    @property
    def target_replica_count(self) -> int:
        if self.desired_replica_count is not None:
            return self.desired_replica_count
        return self.replica_count


@dataclass
class ReplicaData:
    replica_count: int
    desired_replica_count: int | None

    @property
    def target_replica_count(self) -> int:
        if self.desired_replica_count is not None:
            return self.desired_replica_count
        return self.replica_count


class ConfiguredModel(BackendAISchema):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class DeploymentHandlerOptions(ConfiguredModel):
    """Handler-keyed deployment scheduler policy.

    Mirrors ``SessionHandlerOptions``. Resolution order for a given
    ``handler_name``:
    1. ``by_handler[handler_name]`` if present.
    2. ``default`` otherwise.

    Each ``HandlerOptions`` field falls back to ``default``'s value
    when the per-handler override leaves it ``None``. The
    ``HandlerOptions`` field defaults (timeout=None, max_retry_count=5)
    flow through here so a freshly-constructed
    ``DeploymentHandlerOptions()`` keeps the legacy retry budget.
    """

    default: HandlerOptions = Field(default_factory=HandlerOptions)
    by_handler: dict[str, HandlerOptions] = Field(default_factory=dict)

    def resolve(self, handler_name: str) -> HandlerOptions:
        override = self.by_handler.get(handler_name)
        if override is None:
            return self.default
        return HandlerOptions(
            timeout=override.timeout if override.timeout is not None else self.default.timeout,
            max_retry_count=(
                override.max_retry_count
                if override.max_retry_count is not None
                else self.default.max_retry_count
            ),
        )


class DeploymentOptions(ConfiguredModel):
    """Per-deployment operational options.

    Snapshot from the scaling group's ``default_deployment_options`` at
    create time and persisted on the ``endpoints`` row so runtime
    lookups do not need to join against the scaling group. Future
    changes to the scaling group default therefore do not propagate to
    existing deployments.
    """

    handler_options: DeploymentHandlerOptions = Field(default_factory=DeploymentHandlerOptions)


class ReplicaGroupRolloutSpec(ConfiguredModel):
    """Per-group rollout step config snapshot from the deployment strategy at
    DEPLOYING_INITIALIZING; bounds how fast routes move toward the group's desired counts."""

    max_surge: IntOrPercent
    max_unavailable: IntOrPercent

    def resolve_max_surge(self, total: int) -> int:
        """Extra target replicas allowed above the goal (rounds up for percentages)."""
        return self._resolve(self.max_surge, total, round_up=True)

    def resolve_max_unavailable(self, total: int) -> int:
        """Replicas allowed unavailable below the goal (rounds down for percentages)."""
        return self._resolve(self.max_unavailable, total, round_up=False)

    @staticmethod
    def _resolve(value: IntOrPercent, total: int, *, round_up: bool) -> int:
        if value.count is not None:
            return value.count
        result = total * (value.percent or 0.0)
        return math.ceil(result) if round_up else math.floor(result)


class ResourceSpec(ConfiguredModel):
    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: Mapping[str, Any]
    resource_opts: Mapping[str, Any] | None = None


class ExecutionSpec(ConfiguredModel):
    startup_command: str | None = None
    bootstrap_script: str | None = None
    environ: dict[str, str] | None = None
    runtime_variant_id: RuntimeVariantID
    callback_url: yarl.URL | None = None
    inference_runtime_config: Mapping[str, Any] | None = None


class PresetValueSpec(ConfiguredModel):
    """A runtime variant preset value binding stored in a deployment revision."""

    preset_id: DeploymentPresetID
    value: str


class ModelRevisionSpec(ConfiguredModel):
    revision_id: DeploymentRevisionID | None = None
    # Image reference is a single UUID pointer to the ``images`` row. The
    # legacy canonical + architecture pair no longer lives on the spec;
    # callers that need those strings should resolve them from the
    # referenced ``ImageRow`` via the repository.
    image_id: ImageID
    resource_spec: ResourceSpec
    mounts: MountMetadata
    execution: ExecutionSpec
    model_definition: ModelDefinition | None = None
    preset_values: list[PresetValueSpec] = Field(default_factory=list)
    # Original deployment-level preset selection used to build this revision.
    # ``None`` for legacy rows and revisions created without a preset; the
    # materialised effects still live on ``preset_values`` and the resolved
    # configuration columns.
    revision_preset_id: DeploymentPresetID | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


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

    def to_draft(self, image_id: ImageID | None) -> RevisionDraft:
        """Project this legacy spec draft onto a ``RevisionDraft`` layer.

        ``image_id`` is resolved upstream from the spec's ``image_identifier``
        (canonical + architecture) via the repository.
        """
        return RevisionDraft(
            image_id=image_id,
            mounts=self.mounts,
            resource_slots=self.resource_spec.resource_slots,
            resource_opts=self.resource_spec.resource_opts,
            cluster_mode=self.resource_spec.cluster_mode,
            cluster_size=self.resource_spec.cluster_size,
            startup_command=self.execution.startup_command,
            bootstrap_script=self.execution.bootstrap_script,
            environ=self.execution.environ,
            runtime_variant_id=self.execution.runtime_variant_id,
            callback_url=self.execution.callback_url,
            inference_runtime_config=self.execution.inference_runtime_config,
        )


@dataclass
class RevisionDraft:
    """Intermediate representation for revision creation with all fields optional.

    Drafts are produced independently from each source (deployment-config.yaml,
    revision preset, model-definition.yaml, user request) and layered together
    via ``merge`` (``self`` is the lower-priority base, ``other`` overrides).
    Only non-None fields on ``other`` participate in the merge. ``environ`` /
    ``resource_slots`` / ``resource_opts`` are field-merged (dict union, later
    keys win); all other fields are replaced by the latest non-None value.
    """

    # Image.
    # ``image_id is None`` signals either that no layer in the merge chain
    # supplied an image yet, or that the backing image row has been deleted
    # (see ``deployment_revisions.image`` SET NULL FK) — downstream
    # resolvers must treat the latter as non-deployable.
    image_id: ImageID | None = None
    # Mount
    mounts: MountMetadata | None = None
    # Resource
    resource_slots: Mapping[str, Any] | None = None
    resource_opts: Mapping[str, Any] | None = None
    cluster_mode: ClusterMode | None = None
    cluster_size: int | None = None
    # Execution
    startup_command: str | None = None
    bootstrap_script: str | None = None
    environ: Mapping[str, str] | None = None
    runtime_variant_id: RuntimeVariantID | None = None
    callback_url: yarl.URL | None = None
    inference_runtime_config: Mapping[str, Any] | None = None
    # Model definition (draft form — partial fields allowed; merged then resolved
    # to a strict ``ModelDefinition`` at the persistence boundary).
    model_definition: ModelDefinitionDraft | None = None
    # Preset values (carried alongside; not field-merged)
    preset_values: list[PresetValueData] | None = None

    def merge(self, other: RevisionDraft) -> RevisionDraft:
        """Return a new draft with ``other`` layered on top of ``self``."""
        return RevisionDraft(
            image_id=other.image_id if other.image_id is not None else self.image_id,
            mounts=_merge_mounts(self.mounts, other.mounts),
            resource_slots=_merge_mappings(self.resource_slots, other.resource_slots),
            resource_opts=_merge_mappings(self.resource_opts, other.resource_opts),
            cluster_mode=other.cluster_mode
            if other.cluster_mode is not None
            else self.cluster_mode,
            cluster_size=other.cluster_size
            if other.cluster_size is not None
            else self.cluster_size,
            startup_command=other.startup_command
            if other.startup_command is not None
            else self.startup_command,
            bootstrap_script=other.bootstrap_script
            if other.bootstrap_script is not None
            else self.bootstrap_script,
            environ=_merge_mappings(self.environ, other.environ),
            runtime_variant_id=other.runtime_variant_id
            if other.runtime_variant_id is not None
            else self.runtime_variant_id,
            callback_url=other.callback_url
            if other.callback_url is not None
            else self.callback_url,
            inference_runtime_config=other.inference_runtime_config
            if other.inference_runtime_config is not None
            else self.inference_runtime_config,
            model_definition=_merge_model_definition(self.model_definition, other.model_definition),
            preset_values=list(other.preset_values)
            if other.preset_values is not None
            else (list(self.preset_values) if self.preset_values is not None else None),
        )

    def to_model_revision_spec(self) -> ModelRevisionSpec:
        """Project the merged draft into a final ``ModelRevisionSpec``.

        Validates that the merge chain produced an ``image_id`` and a
        ``runtime_variant_id`` — both are required at the persistence
        boundary. Missing values surface as ``InvalidAPIParameters`` so
        API callers get a 400 instead of a silent cascade of ``None`` s
        downstream.
        """
        if self.image_id is None:
            raise InvalidAPIParameters("image_id is required to build a revision")
        if self.mounts is None:
            raise InvalidAPIParameters("mounts are required to build a revision")
        if self.runtime_variant_id is None:
            raise InvalidAPIParameters("runtime_variant_id is required to build a revision")
        return ModelRevisionSpec(
            image_id=self.image_id,
            resource_spec=ResourceSpec(
                cluster_mode=self.cluster_mode or ClusterMode.SINGLE_NODE,
                cluster_size=self.cluster_size or 1,
                resource_slots=self.resource_slots or {},
                resource_opts=self.resource_opts,
            ),
            mounts=self.mounts,
            execution=ExecutionSpec(
                startup_command=self.startup_command,
                bootstrap_script=self.bootstrap_script,
                environ=dict(self.environ) if self.environ else None,
                runtime_variant_id=self.runtime_variant_id,
                callback_url=self.callback_url,
                inference_runtime_config=self.inference_runtime_config,
            ),
            model_definition=(
                self.model_definition.to_resolved() if self.model_definition is not None else None
            ),
        )


def _merge_mounts(
    lower: MountMetadata | None,
    upper: MountMetadata | None,
) -> MountMetadata | None:
    if upper is None:
        return lower
    if lower is None:
        return MountMetadata(
            model_vfolder_id=upper.model_vfolder_id,
            model_definition_path=upper.model_definition_path,
            model_mount_destination=upper.model_mount_destination,
            extra_mounts=list(upper.extra_mounts),
            vfolder_subpath=upper.vfolder_subpath,
        )
    return MountMetadata(
        model_vfolder_id=upper.model_vfolder_id,
        model_definition_path=upper.model_definition_path
        if upper.model_definition_path
        else lower.model_definition_path,
        model_mount_destination=upper.model_mount_destination,
        extra_mounts=list(upper.extra_mounts),
        vfolder_subpath=upper.vfolder_subpath if upper.vfolder_subpath else lower.vfolder_subpath,
    )


def _merge_mappings(
    lower: Mapping[str, Any] | None,
    upper: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if lower is None and upper is None:
        return None
    merged: dict[str, Any] = {}
    if lower is not None:
        merged.update(lower)
    if upper is not None:
        merged.update(upper)
    return merged or None


def _merge_model_definition(
    lower: ModelDefinitionDraft | None,
    upper: ModelDefinitionDraft | None,
) -> ModelDefinitionDraft | None:
    if upper is None:
        return lower
    if lower is None:
        return upper
    return lower.merge(upper)


# ========== Revision-creation Read Bundles ==========
#
# Each bundle groups the DB-sourced draft ingredients that the revision
# pipeline needs for one API path (legacy create, legacy modify, v2 add).
# ``DeploymentRepository`` owns the single batched read method per bundle so
# every query runs inside one session; the reader layer combines the bundle
# with storage-backed files (deployment-config.yaml, model-definition.yaml)
# before assembling the drafts list.


@dataclass(frozen=True)
class LegacyRevisionCreateReadBundle:
    """DB reads for legacy model-serving create (no existing revision)."""

    variant: RuntimeVariantData
    preset: DeploymentRevisionPresetData | None
    preset_resource_slots: list[ResourceSlotEntryData] | None


@dataclass(frozen=True)
class DeploymentRevisionReadBundle:
    """DB reads for v2 deployment ``add_revision`` (typed ids, no base)."""

    variant: RuntimeVariantData
    preset: DeploymentRevisionPresetData | None
    preset_resource_slots: list[ResourceSlotEntryData] | None


@dataclass
class DeploymentNetworkSpec:
    open_to_public: bool
    access_token_ids: list[UUID] | None = None
    url: str | None = None
    preferred_domain_name: str | None = None


@dataclass
class DeploymentNetworkData:
    open_to_public: bool
    access_token_ids: list[UUID] | None
    url: str | None
    preferred_domain_name: str | None


@dataclass
class DeploymentInfo:
    id: DeploymentID
    metadata: DeploymentMetadata
    state: DeploymentState
    replica: ReplicaData
    network: DeploymentNetworkData
    options: DeploymentOptions
    primary_replica_group_id: ReplicaGroupID | None = None
    current_revision_id: DeploymentRevisionID | None = None
    deploying_revision_id: DeploymentRevisionID | None = None
    # Full revision data, populated only by the legacy (REST v1) / engine
    # read paths that eagerly load the revision rows. ``None`` on the modern
    # read path even when ``current_revision_id`` is set.
    current_revision: ModelRevisionData | None = None
    policy: DeploymentPolicyData | None = None
    deploying_revision: ModelRevisionData | None = None
    sub_step: DeploymentLifecycleSubStep | None = None


@dataclass(frozen=True)
class DeploymentLastHistory:
    """Most recent ``deployment_history`` row snapshot for one deployment.

    Carried alongside :class:`DeploymentInfo` so the coordinator can
    (a) decide per failure whether the prior phase matches the current
    handler (retry counting / timeout classification) and (b) classify
    a freshly built history spec as a merge (increment attempts on the
    existing row) or a create (insert a new row).

    Attributes:
        id: Primary key of the row; used to target the UPDATE when
            merging.
        phase: The ``phase`` value recorded on that history row.
        attempts: Retry counter accumulated on that row.
        started_at: When the row was created — used as the phase start
            timestamp for timeout classification.
        error_code: Captured ``error_code``; merge only applies when
            equal to the new spec's error_code.
        to_status: Captured ``to_status`` (lifecycle string, or
            ``None`` when the prior transition did not touch
            lifecycle).
    """

    id: UUID
    phase: str
    attempts: int
    started_at: datetime
    error_code: str | None
    to_status: str | None


@dataclass
class DeploymentWithHistory:
    """Bundles a deployment with the most recent history row in its
    handler category.

    This is the primary data unit for deployment coordinator operations,
    analogous to SessionWithKernels for session scheduling. History rows
    are pre-filtered by ``handler_category`` at the repository layer;
    the coordinator then compares ``last_history.phase`` with the
    current handler name to derive retry metadata only when the two
    match (otherwise the failure counts as a fresh attempt).

    Attributes:
        deployment_info: Deployment information including lifecycle data
        last_history: Latest history row scoped to the current handler
            category, or ``None`` when no prior row exists in that
            category.
    """

    deployment_info: DeploymentInfo
    last_history: DeploymentLastHistory | None


@dataclass
class ScaleOutDecision:
    deployment_info: DeploymentInfo
    new_replica_count: int
    target_revision_id: DeploymentRevisionID | None = None


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
    deployment_id: DeploymentID
    session_id: SessionId | None
    status: RouteStatus
    health_status: RouteHealthStatus
    traffic_ratio: float
    created_at: datetime
    revision_id: UUID
    traffic_status: RouteTrafficStatus
    health_check: ModelHealthCheck | None
    replica_group_id: ReplicaGroupID | None = None
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
    last_triggered_at: datetime | None
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
    session_id: UUID | None
    readiness_status: ReadinessStatus
    liveness_status: LivenessStatus
    activeness_status: ActivenessStatus
    status: RouteStatus
    traffic_status: RouteTrafficStatus
    health_status: RouteHealthStatus
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
    runtime_variant_id: RuntimeVariantID
    inference_runtime_config: Mapping[str, Any] | None = None
    environ: dict[str, Any] | None = None


@dataclass
class ModelMountConfigData:
    vfolder_id: VFolderUUID | None
    mount_destination: str | None
    definition_path: str
    # Same type used for row storage, ``MountMetadata.extra_mounts``, and
    # this data-layer projection — keeps ``mount_perm`` visible end-to-end
    # so modify flows can carry it over without information loss.
    extra_mounts: list[MountInfoEntry]
    # Subpath within the model vfolder. ``None`` means the vfolder root.
    subpath: str | None = None


@dataclass
class ExecutionData:
    """Container-execution overrides frozen on the persisted revision:
    what command runs in the model container, what setup script runs
    before it, and where deployment lifecycle events get POSTed.

    Sibling of ``ModelRuntimeConfigData`` (runtime variant / environ /
    inference runtime knobs); kept separate so the schedulers and draft
    builders can pass these straight to the kernel spec without picking
    them out of the runtime config bag.
    """

    # Replaces the image ``CMD`` when starting the model container.
    # ``None`` keeps whatever the image baked in.
    startup_command: str | None
    # Shell script run once at container startup, before
    # ``startup_command``. ``None`` for revisions that do no extra setup.
    bootstrap_script: str | None
    # Webhook the manager POSTs to on deployment lifecycle events
    # (provisioning, ready, failure, …); ``None`` disables callbacks.
    callback_url: yarl.URL | None


@dataclass
class PresetAttributionData:
    """The deployment-level preset that produced this revision and the
    materialised values it expanded into.

    ``preset_id is None`` means the revision was created without a
    preset (legacy rows or fully ad-hoc creations); the resolver still
    populates the ``values`` list — possibly empty — from the
    ``deployment_revisions.preset_values`` JSONB column either way.
    """

    preset_id: DeploymentPresetID | None
    values: list[PresetValueData]


@dataclass
class ModelRevisionData:
    # Identity
    id: DeploymentRevisionID
    deployment_id: DeploymentID
    revision_number: int
    created_at: datetime
    # Image — ``image_id is None`` signals the backing image row has
    # been deleted (SET NULL FK); the revision is kept for history but
    # cannot be redeployed.
    image_id: ImageID | None
    # Resource
    cluster_config: ClusterConfigData
    resource_config: ResourceConfigData
    # Runtime + execution
    model_runtime_config: ModelRuntimeConfigData
    execution: ExecutionData
    # Mount
    model_mount_config: ModelMountConfigData
    # Preset attribution
    preset: PresetAttributionData
    # Model definition (resolved against the model vfolder at
    # persistence time; ``None`` if the source had none).
    model_definition: ModelDefinition | None = None

    def to_draft(self) -> RevisionDraft:
        """Project this persisted revision onto a ``RevisionDraft`` layer.

        Used as the base (lowest-priority-below-request) layer on the legacy
        modify path so untouched fields survive when the user submits a partial
        override. Every write-time field on ``ModelRevisionData`` —
        ``image_id``, ``cluster_config`` / ``resource_config``,
        ``model_runtime_config`` (runtime variant + environ +
        inference_runtime_config), ``execution`` (startup_command /
        bootstrap_script / callback_url), and ``model_definition`` —
        flows back into the draft as the baseline; preset /
        ``deployment-config.yaml`` / ``model-definition.yaml`` / user
        request layers then override on top via ``merge_revision_drafts``.
        """
        environ = self.model_runtime_config.environ
        resource_slots = dict(self.resource_config.resource_slot) or None
        resource_opts = dict(self.resource_config.resource_opts) or None
        model_definition_draft: ModelDefinitionDraft | None = (
            ModelDefinitionDraft.model_validate(self.model_definition.model_dump(by_alias=True))
            if self.model_definition is not None
            else None
        )
        return RevisionDraft(
            image_id=self.image_id,
            mounts=(
                MountMetadata(
                    model_vfolder_id=self.model_mount_config.vfolder_id,
                    model_definition_path=self.model_mount_config.definition_path or None,
                    model_mount_destination=self.model_mount_config.mount_destination or "/models",
                    extra_mounts=list(self.model_mount_config.extra_mounts),
                    vfolder_subpath=self.model_mount_config.subpath,
                )
                if self.model_mount_config.vfolder_id is not None
                else None
            ),
            resource_slots=resource_slots,
            resource_opts=resource_opts,
            cluster_mode=self.cluster_config.mode,
            cluster_size=self.cluster_config.size,
            startup_command=self.execution.startup_command,
            bootstrap_script=self.execution.bootstrap_script,
            environ={k: str(v) for k, v in environ.items()} if environ else None,
            runtime_variant_id=self.model_runtime_config.runtime_variant_id,
            callback_url=self.execution.callback_url,
            inference_runtime_config=self.model_runtime_config.inference_runtime_config,
            model_definition=model_definition_draft,
        )


@dataclass
class ModelDeploymentMetadataInfo:
    name: str
    status: ModelDeploymentStatus
    tags: list[str]
    project_id: UUID
    domain_name: str
    resource_group_name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ReplicaStateData:
    desired_replica_count: int
    replica_ids: list[UUID]


@dataclass
class ModelDeploymentData:
    """Modern (v2 / GraphQL) deployment projection.

    Carries revisions as ids only (``current_revision_id`` /
    ``deploying_revision_id``); the full revision is resolved on demand by
    the GraphQL DataLoader. The REST v1 surface, which embeds the full
    revision, uses :class:`LegacyDeploymentData` instead.
    """

    id: DeploymentID
    metadata: ModelDeploymentMetadataInfo
    network_access: DeploymentNetworkData
    current_revision_id: DeploymentRevisionID | None
    deploying_revision_id: DeploymentRevisionID | None
    revision_history_ids: list[DeploymentRevisionID]
    scaling_rule_ids: list[UUID]
    replica_state: ReplicaStateData
    default_deployment_strategy: DeploymentStrategy
    created_user_id: UUID
    options: DeploymentOptions
    # Orthogonal to ``metadata.status`` (the lifecycle axis): tracks
    # whether the endpoint is currently reconciling its replica count
    # (``SCALING``) or holding at the desired count (``STABLE``).
    scaling_state: ScalingState
    policy: DeploymentPolicyData | None = None
    access_token_ids: list[UUID] | None = None
    sub_step: DeploymentLifecycleSubStep | None = None


@dataclass
class LegacyDeploymentData:
    """Legacy v1 deployment projection — DO NOT USE in new code.

    Backs the REST v1 ``DeploymentDTO`` response only, which embeds the full
    current ``revision``. v2 / GraphQL use :class:`ModelDeploymentData`
    (revision ids only). Built independently from ``DeploymentInfo``; it is
    never converted to or from :class:`ModelDeploymentData`.
    """

    id: DeploymentID
    metadata: ModelDeploymentMetadataInfo
    network_access: DeploymentNetworkData
    revision: ModelRevisionData | None
    replica_state: ReplicaStateData
    default_deployment_strategy: DeploymentStrategy
    created_user_id: UUID
    policy: DeploymentPolicyData | None = None
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

    # Which axis produced this row. Lifecycle handlers advance the
    # monotonic lifecycle (PENDING → ... → DESTROYED); scaling handlers
    # operate on the orthogonal scaling_state axis. Persisted NOT NULL on
    # ``deployment_history.handler_category`` so this field is always set.
    handler_category: DeploymentHandlerCategory

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

    category: RouteHandlerCategory
    phase: str  # RouteLifecycleType value
    from_status: str | None
    to_status: str | None
    from_sub_status: str | None
    to_sub_status: str | None

    result: SchedulingResult
    error_code: str | None
    message: str

    sub_steps: list[SubStepResult]

    attempts: int
    created_at: datetime
    updated_at: datetime


@dataclass
class ReplicaGroupHistoryData:
    """Domain model for replica-group history."""

    id: UUID
    replica_group_id: ReplicaGroupID
    deployment_id: DeploymentID

    category: ReplicaGroupHandlerCategory
    phase: str
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


@dataclass(frozen=True)
class RevisionRefreshResult:
    """Per-deployment result of an admin bulk revision refresh."""

    deployment_id: UUID
    new_revision_id: UUID | None
    success: bool
    failure_reason: str | None
