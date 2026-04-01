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
from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
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
from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceOptsDTOInput
from ai.backend.common.types import AutoScalingMetricSource, ClusterMode, RuntimeVariant
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
    "ModelDeploymentMetadataInput",
    "ModelDeploymentNetworkAccessInput",
    "ModelMountConfigInput",
    "ModelRuntimeConfigInput",
    "ReplicaFilter",
    "ReplicaOrder",
    "ReplicaStatusFilter",
    "ReplicaTrafficStatusFilter",
    "ResourceConfigInput",
    "ResourceGroupInput",
    "ResourceSlotEntryInput",
    "ResourceSlotInput",
    "RevisionFilter",
    "RevisionInput",
    "RevisionOrder",
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

    resource_group: ResourceGroupInput = Field(description="Resource group")
    resource_slots: ResourceSlotInput = Field(description="Resource slot allocations")
    resource_opts: ResourceOptsDTOInput | None = Field(
        default=None, description="Additional resource options"
    )


class ImageInput(BaseRequestModel):
    """Container image input for a revision."""

    id: UUID = Field(description="Container image ID")


class EnvironmentVariableEntryInput(BaseRequestModel):
    """A single environment variable entry with name and value."""

    name: str = Field(description="Environment variable name")
    value: str = Field(description="Environment variable value")


class EnvironmentVariablesInput(BaseRequestModel):
    """A collection of environment variable entries."""

    entries: list[EnvironmentVariableEntryInput] = Field(
        description="List of environment variable entries"
    )


class ModelRuntimeConfigInput(BaseRequestModel):
    """Runtime configuration input for a revision."""

    runtime_variant: str = Field(description="Runtime variant identifier")
    inference_runtime_config: dict[str, Any] | None = Field(
        default=None, description="Framework-specific inference runtime configuration"
    )
    environ: EnvironmentVariablesInput | None = Field(
        default=None, description="Environment variables for the service"
    )


class ModelMountConfigInput(BaseRequestModel):
    """Model mount configuration input for a revision."""

    vfolder_id: UUID = Field(description="VFolder ID for the model")
    mount_destination: str = Field(description="Mount destination path inside container")
    definition_path: str = Field(description="Path to model definition file")


class ExtraVFolderMountInput(BaseRequestModel):
    """Input for an extra vfolder mount."""

    vfolder_id: UUID = Field(description="VFolder ID to mount")
    mount_destination: str | None = Field(default=None, description="Mount destination path")


class CreateRevisionInputDTO(BaseRequestModel):
    """Input for a deployment revision (nested structure matching GQL CreateRevisionInput)."""

    name: str | None = Field(default=None, description="Revision name")
    cluster_config: ClusterConfigInput = Field(description="Cluster configuration")
    resource_config: ResourceConfigInput = Field(description="Resource configuration")
    image: ImageInput = Field(description="Container image")
    model_runtime_config: ModelRuntimeConfigInput = Field(description="Runtime configuration")
    model_mount_config: ModelMountConfigInput = Field(description="Model mount configuration")
    model_definition: ModelDefinition | None = Field(
        default=None,
        description="Model definition to override the default values generated by the server",
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = Field(
        default=None, description="Additional vfolder mounts"
    )


class AddRevisionGQLInputDTO(BaseRequestModel):
    """Input for adding a revision via GQL (flat structure matching GQL AddRevisionInput)."""

    name: str | None = Field(default=None, description="Revision name")
    deployment_id: UUID = Field(description="Deployment ID")
    cluster_config: ClusterConfigInput = Field(description="Cluster configuration")
    resource_config: ResourceConfigInput = Field(description="Resource configuration")
    image: ImageInput = Field(description="Container image")
    model_runtime_config: ModelRuntimeConfigInput = Field(description="Runtime configuration")
    model_mount_config: ModelMountConfigInput = Field(description="Model mount configuration")
    model_definition: ModelDefinition | None = Field(
        default=None,
        description="Model definition to override the default values generated by the server",
    )
    extra_mounts: list[ExtraVFolderMountInput] | None = Field(
        default=None, description="Additional vfolder mounts"
    )


class ModelDeploymentMetadataInput(BaseRequestModel):
    """Metadata input for creating a model deployment."""

    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
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

    name: str | None = Field(default=None, description="Revision name")
    image_id: UUID = Field(description="Container image ID")
    cluster_mode: ClusterMode = Field(description="Cluster mode for the revision")
    cluster_size: int = Field(default=1, ge=1, description="Number of nodes in the cluster")
    resource_group: str = Field(description="Resource group for allocation")
    resource_slots: Mapping[str, Any] = Field(description="Resource slot requirements")
    resource_opts: Mapping[str, Any] | None = Field(
        default=None, description="Optional resource options"
    )
    runtime_variant: RuntimeVariant = Field(
        default=RuntimeVariant.CUSTOM, description="Runtime variant"
    )
    inference_runtime_config: dict[str, Any] | None = Field(
        default=None, description="Framework-specific inference runtime configuration"
    )
    model_vfolder_id: UUID = Field(description="Model VFolder ID")
    model_mount_destination: str = Field(
        default="/models", description="Mount destination for model vfolder"
    )
    model_definition_path: str = Field(description="Path to model definition file")
    model_definition: ModelDefinition | None = Field(
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
    desired_replica_count: int = Field(ge=0, description="Desired number of replicas")
    initial_revision: CreateRevisionInputDTO = Field(description="Initial revision configuration")


class UpdateDeploymentInput(BaseRequestModel):
    """Input for updating a deployment."""

    name: str | None = Field(default=None, description="Updated deployment name")
    desired_replica_count: int | None = Field(
        default=None, ge=0, description="Updated desired replica count"
    )
    tags: list[str] | Sentinel | None = Field(
        default=SENTINEL, description="Updated tags. Use SENTINEL to clear."
    )
    open_to_public: bool | None = Field(
        default=None, description="Updated network visibility. None means no change."
    )
    preferred_domain_name: str | None = Field(
        default=None, description="Updated preferred domain name. None means no change."
    )
    active_revision_id: UUID | None = Field(
        default=None, description="ID of the revision to activate. None means no change."
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
    revision: RevisionInput = Field(description="Revision configuration")


# ---------------------------------------------------------------------------
# Filter types
# ---------------------------------------------------------------------------


class DeploymentStatusFilter(BaseRequestModel):
    """Filter for deployment status."""

    equals: str | None = Field(default=None, description="Exact status match")
    in_: list[str] | None = Field(default=None, alias="in", description="Status is in list")


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


class ReplicaTrafficStatusFilter(BaseRequestModel):
    """Filter for replica traffic status."""

    equals: RouteTrafficStatus | None = Field(
        default=None, description="Exact traffic status match"
    )
    in_: list[RouteTrafficStatus] | None = Field(
        default=None, alias="in", description="Traffic status is in list"
    )


class DeploymentFilter(BaseRequestModel):
    """Filter for deployments."""

    name: StringFilter | None = Field(default=None, description="Name filter")
    status: DeploymentStatusFilter | None = Field(default=None, description="Status filter")
    open_to_public: bool | None = Field(default=None, description="Public access filter")
    tags: StringFilter | None = Field(default=None, description="Tags filter")
    endpoint_url: StringFilter | None = Field(default=None, description="Endpoint URL filter")
    AND: list[DeploymentFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[DeploymentFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[DeploymentFilter] | None = Field(default=None, description="NOT negation")


DeploymentFilter.model_rebuild()


class RevisionFilter(BaseRequestModel):
    """Filter for deployment revisions."""

    name: StringFilter | None = Field(default=None, description="Name filter")
    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    AND: list[RevisionFilter] | None = Field(default=None, description="AND conjunction")
    OR: list[RevisionFilter] | None = Field(default=None, description="OR conjunction")
    NOT: list[RevisionFilter] | None = Field(default=None, description="NOT negation")


RevisionFilter.model_rebuild()


class RouteFilter(BaseRequestModel):
    """Filter for deployment routes."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    status: list[RouteStatus] | None = Field(default=None, description="Route status filter")
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
    valid_until: DateTimeFilter | None = Field(
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
    last_triggered_at: DateTimeFilter | None = Field(
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

    deployment_id: UUID = Field(description="Deployment ID")
    valid_until: datetime = Field(description="Token expiration timestamp")


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
