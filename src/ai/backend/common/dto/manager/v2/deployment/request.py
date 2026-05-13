"""
Request DTOs for Deployment DTO v2.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.config import (
    ModelDefinitionDraft,
    PreStartAction,
)
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    IntFilter,
    NullableDateTimeFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.deployment.types import (
    AccessTokenOrderField,
    AutoScalingRuleOrderField,
    DeploymentOrderField,
    IntOrPercent,
    OrderDirection,
    ReplicaOrderField,
    RevisionOrderField,
    RouteOrderField,
)
from ai.backend.common.dto.manager.v2.deployment_options import DeploymentOptionsInput
from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceOptsDTOInput
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    AutoScalingMetricSource,
    ClusterMode,
    MountPermission,
)
from ai.backend.common.utils import dedent_strip

__all__ = (
    "AccessTokenFilter",
    "AccessTokenOrder",
    "ActivateDeploymentInput",
    "ActivateRevisionInput",
    "AddRevisionGQLInputDTO",
    "AddRevisionInput",
    "AdminSearchDeploymentsInput",
    "AdminSearchRevisionsInput",
    "AutoScalingRuleFilter",
    "AutoScalingRuleOrder",
    "BlueGreenConfigInput",
    "ClusterConfigInput",
    "CreateRevisionInputDTO",
    "CreateAccessTokenInput",
    "CreateAutoScalingRuleInput",
    "CreateDeploymentInput",
    "DeleteAutoScalingRuleInput",
    "DeleteDeploymentInput",
    "DeploymentFilter",
    "DeploymentOrder",
    "DeploymentPolicyFilter",
    "DeploymentStatusFilter",
    "DeploymentStrategyInput",
    "EnvironmentVariableEntryInput",
    "EnvironmentVariablesInput",
    "ExtraVFolderMountInput",
    "ImageInput",
    "ModelConfigInput",
    "ModelDefinitionInput",
    "ModelDeploymentMetadataInput",
    "ModelDeploymentNetworkAccessInput",
    "ModelHealthCheckInput",
    "ModelMetadataInput",
    "ModelMountConfigInput",
    "ModelRuntimeConfigInput",
    "ModelServiceConfigInput",
    "ReplicaFilter",
    "ReplicaOrder",
    "ReplicaStatusFilter",
    "ReplicaTrafficStatusFilter",
    "ResourceConfigInput",
    "ResourceSlotEntryInput",
    "ResourceSlotInput",
    "RevisionFilter",
    "RevisionInput",
    "RevisionOrder",
    "ReplaceDeploymentOptionsGQLInput",
    "ReplaceDeploymentOptionsInput",
    "RollingUpdateConfigInput",
    "RouteFilter",
    "RouteOrder",
    "RouteStatusFilter",
    "RouteTrafficStatusFilter",
    "ScaleDeploymentInput",
    "SearchAccessTokensInput",
    "SearchAutoScalingRulesInput",
    "SearchDeploymentPoliciesInput",
    "SearchReplicasInput",
    "SearchRoutesInput",
    "SyncReplicaInput",
    "UpdateAutoScalingRuleInput",
    "UpdateDeploymentInput",
    "UpdateRouteTrafficStatusInput",
    "UpsertDeploymentPolicyInput",
)


class ModelHealthCheckInput(BaseRequestModel):
    interval: float | None = None
    path: str | None = None
    max_retries: int | None = None
    max_wait_time: float | None = None
    expected_status_code: int | None = None
    initial_delay: float | None = None


class ModelMetadataInput(BaseRequestModel):
    author: str | None = None
    title: str | None = None
    version: str | None = None
    created: str | None = None
    last_modified: str | None = None
    description: str | None = None
    task: str | None = None
    category: str | None = None
    architecture: str | None = None
    framework: list[str] | None = None
    label: list[str] | None = None
    license: str | None = None
    min_resource: dict[str, Any] | None = None


class ModelServiceConfigInput(BaseRequestModel):
    pre_start_actions: list[PreStartAction] | None = None
    start_command: list[str] | None = None
    shell: str | None = None
    port: int | None = None
    health_check: ModelHealthCheckInput | None = None


class ModelConfigInput(BaseRequestModel):
    name: str | None = None
    model_path: str | None = None
    service: ModelServiceConfigInput | None = None
    metadata: ModelMetadataInput | None = None


class ModelDefinitionInput(BaseRequestModel):
    """All-optional v2 input mirror of :class:`ModelDefinitionDraft`.

    Fields a request omits are filled by lower-priority sources in the
    revision merge chain (runtime variant baseline, revision preset,
    vfolder ``model-definition.yaml``, ``model_mount_destination``
    default). Required-field enforcement happens later in
    ``ModelDefinitionDraft.to_resolved`` after the merge.
    """

    models: list[ModelConfigInput] | None = None

    def to_draft(self) -> ModelDefinitionDraft:
        # ``exclude_unset=True`` keeps the resulting draft's
        # ``model_fields_set`` aligned with what the caller actually
        # provided. Without it, every field would appear "explicitly
        # set" (to ``None``) and clobber lower-priority sources during
        # the revision merge.
        return ModelDefinitionDraft.model_validate(self.model_dump(exclude_unset=True))


class ClusterConfigInput(BaseRequestModel):
    """Cluster configuration input for a revision."""

    mode: ClusterMode = Field(description="Cluster mode")
    size: int = Field(description="Cluster size (number of nodes)")


class ResourceGroupInput(BaseRequestModel):
    """Resource group input for a revision."""

    name: str = Field(description="Resource group name")


class ResourceSlotInput(BaseRequestModel):
    """Collection of compute resource allocations."""

    entries: list[ResourceSlotEntryInput] = Field(description="List of resource allocations")


class ResourceConfigInput(BaseRequestModel):
    """Resource configuration input for a revision."""

    resource_slots: ResourceSlotInput = Field(description="Resource slot allocations")
    resource_opts: ResourceOptsDTOInput | None = Field(
        default=None, description="Additional resource options"
    )


class ImageInput(BaseRequestModel):
    """Container image input for a revision."""

    id: ImageID = Field(description="Container image ID")


class EnvironmentVariableEntryInput(BaseRequestModel):
    """A single environment variable entry with name and value.

    .. deprecated::
        Retained only for legacy deployment/session DTOs that already expose ``name``.
        New code should use
        :class:`ai.backend.common.dto.manager.v2.common.EnvironmentVariableEntryInput`
        (``key``/``value``) instead.
    """

    name: str = Field(description="Environment variable name")
    value: str = Field(description="Environment variable value")


class EnvironmentVariablesInput(BaseRequestModel):
    """A collection of environment variable entries.

    .. deprecated::
        Retained only for legacy deployment/session DTOs.
        New code should use
        :class:`ai.backend.common.dto.manager.v2.common.EnvironmentVariablesInput`.
    """

    entries: list[EnvironmentVariableEntryInput] = Field(
        description="List of environment variable entries"
    )


class ModelRuntimeConfigInput(BaseRequestModel):
    """Runtime configuration input for a revision."""

    runtime_variant_id: RuntimeVariantID = Field(
        description=(
            "Runtime variant ID (UUID). Internal v2 adapters consume the id"
            " directly; legacy REST handlers resolve name→id via the"
            " RuntimeVariant resolver service before invoking internal flows."
        ),
    )
    inference_runtime_config: dict[str, Any] | None = Field(
        default=None, description="Framework-specific inference runtime configuration"
    )
    environ: EnvironmentVariablesInput | None = Field(
        default=None, description="Environment variables for the service"
    )


class ModelMountConfigInput(BaseRequestModel):
    """Model mount configuration input for a revision."""

    vfolder_id: VFolderUUID | None = Field(
        default=None, description="VFolder ID for the model"
    )
    mount_destination: str = Field(
        default="/models", description="Mount destination path inside container"
    )
    definition_path: str | None = Field(
        default=None,
        description=(
            "Optional path to the model definition file within the model vfolder. "
            "When omitted, the server auto-detects `model-definition.yaml` or "
            "`model-definition.yml`."
        ),
    )

    @classmethod
    def default(cls) -> "ModelMountConfigInput":
        """Return an all-default mount config.

        Used by adapters when the caller submits a partial revision draft
        without a ``model_mount_config`` block: the resulting instance
        carries ``vfolder_id=None`` (the DB ``model`` column is nullable),
        the canonical ``"/models"`` mount destination, and no definition
        path override.
        """
        return cls()


class ExtraVFolderMountInput(BaseRequestModel):
    """Input for an extra vfolder mount."""

    vfolder_id: VFolderUUID = Field(description="VFolder ID to mount")
    mount_destination: str | None = Field(default=None, description="Mount destination path")
    mount_perm: MountPermission | None = Field(
        default=None,
        description=(
            "Optional permission override. ``null`` (default) uses the vfolder's own "
            "stored permission; a concrete value (e.g. ``ro``) forces that permission "
            "regardless of what the vfolder grants."
        ),
    )


class CreateRevisionInputDTO(BaseRequestModel):
    """Input for a deployment revision (nested structure matching GQL CreateRevisionInput)."""

    name: str | None = Field(default=None, description="Revision name")
    revision_preset_id: DeploymentPresetID | None = Field(
        default=None,
        description="DeploymentRevisionPreset ID. When specified, preset values are used as defaults and can be overridden by explicitly provided fields.",
    )
    cluster_config: ClusterConfigInput = Field(description="Cluster configuration")
    resource_config: ResourceConfigInput = Field(description="Resource configuration")
    image: ImageInput = Field(description="Container image")
    model_runtime_config: ModelRuntimeConfigInput = Field(description="Runtime configuration")
    model_mount_config: ModelMountConfigInput = Field(description="Model mount configuration")
    model_definition: ModelDefinitionInput | None = Field(
        default=None,
        description="Model definition to override the default values generated by the server",
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = Field(
        default=None, description="Additional vfolder mounts"
    )
    auto_activate: bool = Field(
        default=False,
        description="If true, automatically activate this revision after creation.",
    )


class AddRevisionOptions(BaseRequestModel):
    """Options for the add revision operation."""

    auto_activate: bool = Field(
        default=False,
        description="When true, automatically activate the newly added revision immediately after creation.",
    )


class AddRevisionGQLInputDTO(BaseRequestModel):
    """Input for adding a revision. Used by both GQL and REST v2 APIs."""

    revision_preset_id: DeploymentPresetID | None = Field(
        default=None,
        description="DeploymentRevisionPreset ID. When specified, preset values are used as defaults and can be overridden by explicitly provided fields.",
    )
    deployment_id: UUID = Field(description="Deployment ID")
    cluster_config: ClusterConfigInput | None = Field(
        default=None, description="Cluster configuration"
    )
    resource_config: ResourceConfigInput | None = Field(
        default=None, description="Resource configuration"
    )
    image: ImageInput | None = Field(default=None, description="Container image")
    model_runtime_config: ModelRuntimeConfigInput | None = Field(
        default=None, description="Runtime configuration"
    )
    model_mount_config: ModelMountConfigInput | None = Field(
        default=None, description="Model mount configuration"
    )
    model_definition: ModelDefinitionInput | None = Field(
        default=None,
        description="Model definition to override the default values generated by the server",
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = Field(
        default=None, description="Additional vfolder mounts"
    )
    options: AddRevisionOptions | None = Field(
        default=None,
        description="Additional options for the add revision operation.",
    )


class ModelDeploymentMetadataInput(BaseRequestModel):
    """Metadata input for creating a model deployment."""

    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    resource_group: ResourceGroupName = Field(description="Resource group name")
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="Deployment name",
    )
    tags: list[str] | None = Field(default=None, description="Deployment tags")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class ModelDeploymentNetworkAccessInput(BaseRequestModel):
    """Network access configuration input for a deployment."""

    preferred_domain_name: str | None = Field(
        default=None, description="Preferred domain name for URL"
    )
    open_to_public: bool = Field(default=False, description="Whether the deployment is public")


class RollingUpdateConfigInput(BaseRequestModel):
    """Input for rolling update configuration.

    ``max_surge`` and ``max_unavailable`` are :class:`IntOrPercent` objects (oneOf):

    - ``{"count": 2}``        — absolute replica count
    - ``{"percent": 0.25}``   — fraction of desired replicas (0.0-1.0)
    """

    max_surge: IntOrPercent = Field(
        default_factory=lambda: IntOrPercent(percent=0.5),
        description=dedent_strip("""
            Maximum number of extra replicas that can be created
            during a rolling update.
            Defaults to 50% of desired replicas.
        """),
        examples=[
            {"count": 2},
            {"percent": 0.25},
        ],
    )
    max_unavailable: IntOrPercent = Field(
        default_factory=lambda: IntOrPercent(percent=0.0),
        description=dedent_strip("""
            Maximum number of replicas that can be unavailable
            during a rolling update.
            Defaults to 0%.
        """),
        examples=[
            {"count": 0},
            {"percent": 0.0},
        ],
    )


class BlueGreenConfigInput(BaseRequestModel):
    """Input for blue/green deployment configuration."""

    auto_promote: bool = Field(default=False, description="Automatically promote new revision")
    promote_delay_seconds: int = Field(
        default=0, ge=0, description="Delay in seconds before promotion"
    )


class DeploymentStrategyInput(BaseRequestModel):
    """Deployment strategy input with type discriminator."""

    type: DeploymentStrategy = Field(description="Deployment strategy type")
    rolling_update: RollingUpdateConfigInput | None = Field(
        default=None, description="Rolling update config (required for ROLLING strategy)"
    )
    blue_green: BlueGreenConfigInput | None = Field(
        default=None, description="Blue/green config (required for BLUE_GREEN strategy)"
    )


class RevisionInput(BaseRequestModel):
    """Input for a deployment revision."""

    revision_preset_id: DeploymentPresetID | None = Field(
        default=None,
        description="DeploymentRevisionPreset ID. When specified, preset values are used as defaults and can be overridden by explicitly provided fields.",
    )
    image_id: UUID | None = Field(default=None, description="Container image ID")
    cluster_mode: ClusterMode | None = Field(
        default=None, description="Cluster mode for the revision"
    )
    cluster_size: int | None = Field(
        default=None, ge=1, description="Number of nodes in the cluster"
    )
    resource_slots: Mapping[str, Any] | None = Field(
        default=None, description="Resource slot requirements"
    )
    resource_opts: Mapping[str, Any] | None = Field(
        default=None, description="Optional resource options"
    )
    runtime_variant_id: RuntimeVariantID | None = Field(
        default=None, description="Runtime variant ID (UUID)"
    )
    inference_runtime_config: dict[str, Any] | None = Field(
        default=None, description="Framework-specific inference runtime configuration"
    )
    model_vfolder_id: VFolderUUID | None = Field(default=None, description="Model VFolder ID")
    model_mount_destination: str | None = Field(
        default=None, description="Mount destination for model vfolder"
    )
    model_definition_path: str | None = Field(
        default=None, description="Path to model definition file"
    )
    model_definition: ModelDefinitionInput | None = Field(
        default=None,
        description="Model definition to override the default values generated by the server",
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = Field(
        default=None, description="Additional vfolder mounts"
    )
    environ: Mapping[str, str] | None = Field(default=None, description="Environment variables")


class CreateDeploymentInput(BaseRequestModel):
    """Input for creating a deployment."""

    metadata: ModelDeploymentMetadataInput = Field(description="Deployment metadata")
    network_access: ModelDeploymentNetworkAccessInput = Field(
        description="Network access configuration"
    )
    default_deployment_strategy: DeploymentStrategyInput = Field(
        description="Deployment strategy configuration"
    )
    replica_count: int = Field(ge=0, description="Number of replicas")
    initial_revision: CreateRevisionInputDTO | None = Field(
        default=None,
        description="Initial revision configuration. If omitted, deployment is created without a revision and must be added later via add_revision.",
    )


class UpdateDeploymentInput(BaseRequestModel):
    """Input for updating a deployment."""

    name: str | None = Field(default=None, description="Updated deployment name")
    replica_count: int | None = Field(default=None, ge=0, description="Updated replica count")
    tags: list[str] | Sentinel | None = Field(
        default=SENTINEL, description="Updated tags. Use SENTINEL to clear."
    )
    open_to_public: bool | None = Field(
        default=None, description="Updated network visibility. None means no change."
    )
    preferred_domain_name: str | None = Field(
        default=None, description="Updated preferred domain name. None means no change."
    )
    default_deployment_strategy: DeploymentStrategyInput | None = Field(
        default=None, description="Updated deployment strategy. None means no change."
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteDeploymentInput(BaseRequestModel):
    """Input for deleting a deployment."""

    id: UUID = Field(description="Deployment ID to delete")


class ActivateDeploymentInput(BaseRequestModel):
    """Input for activating a deployment."""

    id: UUID = Field(description="Deployment ID to activate")


class ScaleDeploymentInput(BaseRequestModel):
    """Input for scaling a deployment."""

    id: UUID = Field(description="Deployment ID to scale")
    replicas: int = Field(ge=0, description="Target replica count")


class AddRevisionInput(BaseRequestModel):
    """Input for adding a revision to a deployment."""

    deployment_id: UUID = Field(description="Deployment ID")
    revision: RevisionInput | None = Field(default=None, description="Revision configuration")


# ---------------------------------------------------------------------------
# Filter types
# ---------------------------------------------------------------------------


class DeploymentStatusFilter(BaseRequestModel):
    """Filter for deployment status."""

    equals: str | None = Field(default=None, description="Exact status match")
    in_: list[str] | None = Field(default=None, alias="in", description="Status is in list")
    not_equals: str | None = Field(default=None, description="Excludes exact status match")
    not_in: list[str] | None = Field(default=None, description="Status is not in list")


class RouteStatusFilter(BaseRequestModel):
    """Filter for route status."""

    equals: RouteStatus | None = Field(default=None, description="Exact status match")
    in_: list[RouteStatus] | None = Field(default=None, alias="in", description="Status is in list")
    not_equals: RouteStatus | None = Field(default=None, description="Excludes exact status match")
    not_in: list[RouteStatus] | None = Field(default=None, description="Status is not in list")


class RouteTrafficStatusFilter(BaseRequestModel):
    """Filter for route traffic status."""

    equals: RouteTrafficStatus | None = Field(default=None, description="Exact status match")
    in_: list[RouteTrafficStatus] | None = Field(
        default=None, alias="in", description="Status is in list"
    )
    not_equals: RouteTrafficStatus | None = Field(
        default=None, description="Excludes exact status match"
    )
    not_in: list[RouteTrafficStatus] | None = Field(
        default=None, description="Status is not in list"
    )


class ReplicaStatusFilter(BaseRequestModel):
    """Filter for replica (route) status."""

    equals: RouteStatus | None = Field(default=None, description="Exact status match")
    in_: list[RouteStatus] | None = Field(default=None, alias="in", description="Status is in list")
    not_equals: RouteStatus | None = Field(default=None, description="Excludes exact status match")
    not_in: list[RouteStatus] | None = Field(default=None, description="Status is not in list")


class ReplicaTrafficStatusFilter(BaseRequestModel):
    """Filter for replica traffic status."""

    equals: RouteTrafficStatus | None = Field(
        default=None, description="Exact traffic status match"
    )
    in_: list[RouteTrafficStatus] | None = Field(
        default=None, alias="in", description="Traffic status is in list"
    )
    not_equals: RouteTrafficStatus | None = Field(
        default=None, description="Excludes exact traffic status match"
    )
    not_in: list[RouteTrafficStatus] | None = Field(
        default=None, description="Traffic status is not in list"
    )


class DeploymentFilter(BaseRequestModel):
    """Filter for deployments."""

    name: StringFilter | None = Field(default=None, description="Name filter")
    status: DeploymentStatusFilter | None = Field(default=None, description="Status filter")
    open_to_public: bool | None = Field(default=None, description="Public access filter")
    tags: StringFilter | None = Field(default=None, description="Tags filter")
    endpoint_url: StringFilter | None = Field(default=None, description="Endpoint URL filter")
    domain_name: StringFilter | None = Field(default=None, description="Domain name filter")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    resource_group: StringFilter | None = Field(
        default=None, description="Resource group name filter"
    )
    created_user_id: UUIDFilter | None = Field(
        default=None, description="Filter by the user who created the deployment"
    )
    created_at: DateTimeFilter | None = Field(default=None, description="Creation datetime filter")
    destroyed_at: NullableDateTimeFilter | None = Field(
        default=None, description="Destruction datetime filter (supports is_null)"
    )
    AND: list[DeploymentFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[DeploymentFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[DeploymentFilter] | None = Field(default=None, description="NOT negation")


DeploymentFilter.model_rebuild()


class RevisionFilter(BaseRequestModel):
    """Filter for deployment revisions."""

    revision_number: IntFilter | None = Field(default=None, description="Filter by revision number")
    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    image_id: UUIDFilter | None = Field(default=None, description="Filter by container image ID")
    model_vfolder_id: UUIDFilter | None = Field(
        default=None, description="Filter by model VFolder ID"
    )
    resource_group: StringFilter | None = Field(
        default=None, description="Resource group name filter"
    )
    cluster_mode: StringFilter | None = Field(default=None, description="Cluster mode filter")
    created_at: DateTimeFilter | None = Field(default=None, description="Creation datetime filter")
    AND: list[RevisionFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[RevisionFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[RevisionFilter] | None = Field(default=None, description="NOT negation")


RevisionFilter.model_rebuild()


class RouteFilter(BaseRequestModel):
    """Filter for deployment routes."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    status: list[RouteStatus] | None = Field(
        default=None, description="Route lifecycle status filter"
    )
    health_status: list[RouteHealthStatus] | None = Field(
        default=None, description="Route health status filter"
    )
    traffic_status: list[RouteTrafficStatus] | None = Field(
        default=None, description="Traffic status filter"
    )
    AND: list[RouteFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[RouteFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[RouteFilter] | None = Field(default=None, description="NOT negation")


RouteFilter.model_rebuild()


class AccessTokenFilter(BaseRequestModel):
    """Filter for access tokens."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    token: StringFilter | None = Field(default=None, description="Token value filter")
    expires_at: DateTimeFilter | None = Field(
        default=None, description="Expiration datetime filter"
    )
    created_at: DateTimeFilter | None = Field(default=None, description="Creation datetime filter")
    AND: list[AccessTokenFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[AccessTokenFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[AccessTokenFilter] | None = Field(default=None, description="NOT negation")


AccessTokenFilter.model_rebuild()


class AutoScalingRuleFilter(BaseRequestModel):
    """Filter for auto-scaling rules."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    created_at: DateTimeFilter | None = Field(default=None, description="Creation datetime filter")
    last_triggered_at: NullableDateTimeFilter | None = Field(
        default=None, description="Last triggered datetime filter"
    )
    AND: list[AutoScalingRuleFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[AutoScalingRuleFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[AutoScalingRuleFilter] | None = Field(default=None, description="NOT negation")


AutoScalingRuleFilter.model_rebuild()


class ReplicaFilter(BaseRequestModel):
    """Filter for deployment replicas."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    status: ReplicaStatusFilter | None = Field(default=None, description="Replica status filter")
    traffic_status: ReplicaTrafficStatusFilter | None = Field(
        default=None, description="Replica traffic status filter"
    )
    AND: list[ReplicaFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[ReplicaFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[ReplicaFilter] | None = Field(default=None, description="NOT negation")


ReplicaFilter.model_rebuild()


class DeploymentPolicyFilter(BaseRequestModel):
    """Filter for deployment policies."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")


# ---------------------------------------------------------------------------
# Order types
# ---------------------------------------------------------------------------


class DeploymentOrder(BaseRequestModel):
    """Ordering specification for deployments."""

    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC


class RevisionOrder(BaseRequestModel):
    """Ordering specification for revisions."""

    field: RevisionOrderField
    direction: OrderDirection = OrderDirection.DESC


class RouteOrder(BaseRequestModel):
    """Ordering specification for routes."""

    field: RouteOrderField
    direction: OrderDirection = OrderDirection.DESC


class AccessTokenOrder(BaseRequestModel):
    """Ordering specification for access tokens."""

    field: AccessTokenOrderField
    direction: OrderDirection = OrderDirection.DESC


class AutoScalingRuleOrder(BaseRequestModel):
    """Ordering specification for auto-scaling rules."""

    field: AutoScalingRuleOrderField
    direction: OrderDirection = OrderDirection.DESC


class ReplicaOrder(BaseRequestModel):
    """Ordering specification for deployment replicas."""

    field: ReplicaOrderField
    direction: OrderDirection = OrderDirection.DESC


# ---------------------------------------------------------------------------
# Search input types
# ---------------------------------------------------------------------------


class AdminSearchDeploymentsInput(BaseRequestModel):
    """Input for searching deployments (admin, no scope)."""

    filter: DeploymentFilter | None = Field(default=None, description="Filter criteria")
    order: list[DeploymentOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Max results per page (offset)")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class AdminSearchRevisionsInput(BaseRequestModel):
    """Input for searching deployment revisions (admin, no scope)."""

    filter: RevisionFilter | None = Field(default=None, description="Filter criteria")
    order: list[RevisionOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Max results per page (offset)")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchRoutesInput(BaseRequestModel):
    """Input for searching deployment routes."""

    filter: RouteFilter | None = Field(default=None, description="Filter criteria")
    order: list[RouteOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Max results per page (offset)")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchAccessTokensInput(BaseRequestModel):
    """Input for searching access tokens."""

    filter: AccessTokenFilter | None = Field(default=None, description="Filter criteria")
    order: list[AccessTokenOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Max results per page (offset)")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchAutoScalingRulesInput(BaseRequestModel):
    """Input for searching auto-scaling rules."""

    filter: AutoScalingRuleFilter | None = Field(default=None, description="Filter criteria")
    order: list[AutoScalingRuleOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Max results per page (offset)")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchReplicasInput(BaseRequestModel):
    """Input for searching deployment replicas."""

    filter: ReplicaFilter | None = Field(default=None, description="Filter criteria")
    order: list[ReplicaOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Max results per page (offset)")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchDeploymentPoliciesInput(BaseRequestModel):
    """Input for searching deployment policies."""

    filter: DeploymentPolicyFilter | None = Field(default=None, description="Filter criteria")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


# ---------------------------------------------------------------------------
# Sub-entity mutation inputs
# ---------------------------------------------------------------------------


class CreateAccessTokenInput(BaseRequestModel):
    """Input for creating an access token."""

    model_deployment_id: UUID = Field(description="Model deployment ID")
    expires_at: datetime = Field(
        description=(
            "Token expiration timestamp. Required: there is no safe default — "
            "callers must decide the token lifetime themselves."
        )
    )


class DeleteAccessTokenInput(BaseRequestModel):
    """Input for deleting an access token."""

    id: UUID = Field(description="Access token ID")


class BulkDeleteAccessTokensInput(BaseRequestModel):
    """Input for bulk deleting access tokens."""

    ids: list[UUID] = Field(description="List of access token UUIDs to delete.")


class CreateAutoScalingRuleInput(BaseRequestModel):
    """Input for creating an auto-scaling rule."""

    deployment_id: UUID = Field(description="Deployment ID")
    metric_source: AutoScalingMetricSource = Field(description="Metric source")
    metric_name: str = Field(description="Metric name")
    min_threshold: Decimal | None = Field(default=None, description="Minimum threshold")
    max_threshold: Decimal | None = Field(default=None, description="Maximum threshold")
    step_size: int = Field(ge=1, description="Scale step size")
    time_window: int = Field(ge=1, description="Time window in seconds")
    min_replicas: int | None = Field(default=None, ge=0, description="Minimum replicas")
    max_replicas: int | None = Field(default=None, ge=1, description="Maximum replicas")


class UpdateAutoScalingRuleInput(BaseRequestModel):
    """Input for updating an auto-scaling rule (all fields are optional)."""

    metric_source: AutoScalingMetricSource | None = Field(
        default=None, description="Metric source (None = no change)"
    )
    metric_name: str | None = Field(default=None, description="Metric name (None = no change)")
    min_threshold: Decimal | None = Field(
        default=None, description="Minimum threshold (None = no change)"
    )
    max_threshold: Decimal | None = Field(
        default=None, description="Maximum threshold (None = no change)"
    )
    step_size: int | None = Field(
        default=None, ge=1, description="Scale step size (None = no change)"
    )
    time_window: int | None = Field(
        default=None, ge=1, description="Time window in seconds (None = no change)"
    )
    min_replicas: int | None = Field(
        default=None, ge=0, description="Minimum replicas (None = no change)"
    )
    max_replicas: int | None = Field(
        default=None, ge=1, description="Maximum replicas (None = no change)"
    )


class DeleteAutoScalingRuleInput(BaseRequestModel):
    """Input for deleting an auto-scaling rule."""

    id: UUID = Field(description="Auto-scaling rule ID")


class BulkDeleteAutoScalingRulesInput(BaseRequestModel):
    """Input for bulk deleting auto-scaling rules."""

    ids: list[UUID] = Field(description="List of auto-scaling rule UUIDs to delete.")


class UpsertDeploymentPolicyInput(BaseRequestModel):
    """Input for creating or updating a deployment policy."""

    deployment_id: UUID = Field(description="Deployment ID")
    strategy: DeploymentStrategy = Field(description="Deployment strategy")
    rolling_update: RollingUpdateConfigInput | None = Field(
        default=None, description="Rolling update config (required for ROLLING strategy)"
    )
    blue_green: BlueGreenConfigInput | None = Field(
        default=None, description="Blue/green config (required for BLUE_GREEN strategy)"
    )


class SyncReplicaInput(BaseRequestModel):
    """Input for syncing replicas for a deployment."""

    model_deployment_id: UUID = Field(description="Deployment ID to sync replicas for")


class ActivateRevisionInput(BaseRequestModel):
    """Input for activating a revision as the current revision."""

    deployment_id: UUID = Field(description="Deployment ID")
    revision_id: UUID = Field(description="Revision ID to activate")


class UpdateRouteTrafficStatusInput(BaseRequestModel):
    """Input for updating a route's traffic status."""

    route_id: UUID = Field(description="Route ID to update")
    traffic_status: RouteTrafficStatus = Field(description="New traffic status (ACTIVE/INACTIVE)")


class ReplaceDeploymentOptionsInput(BaseRequestModel):
    """REST body for fully replacing a deployment's ``options`` surface.

    Replace semantics — the supplied payload is the complete new value
    (partial updates are not supported here).
    """

    options: DeploymentOptionsInput = Field(
        description="New deployment options payload. Replaces the existing options atomically.",
    )


class ReplaceDeploymentOptionsGQLInput(BaseRequestModel):
    """GraphQL mutation input for fully replacing a deployment's ``options`` surface.

    Mirrors :class:`ReplaceDeploymentOptionsInput` with an additional
    ``deployment_id`` argument so the GQL mutation can take a single
    input object (REST carries the id in the path instead).
    """

    deployment_id: DeploymentID = Field(description="Target deployment ID.")
    options: DeploymentOptionsInput = Field(
        description="New deployment options payload. Replaces the existing options atomically.",
    )
