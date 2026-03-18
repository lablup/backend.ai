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
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.deployment.types import (
    AccessTokenOrderField,
    AutoScalingRuleOrderField,
    DeploymentOrderField,
    OrderDirection,
    RevisionOrderField,
    RouteOrderField,
)
from ai.backend.common.types import AutoScalingMetricSource, ClusterMode, RuntimeVariant

__all__ = (
    "AccessTokenFilter",
    "AccessTokenOrder",
    "ActivateDeploymentInput",
    "ActivateRevisionInput",
    "AddRevisionInput",
    "AdminSearchDeploymentsInput",
    "AdminSearchRevisionsInput",
    "AutoScalingRuleFilter",
    "AutoScalingRuleOrder",
    "BlueGreenConfigInput",
    "CreateAccessTokenInput",
    "CreateAutoScalingRuleInput",
    "CreateDeploymentInput",
    "DeleteAutoScalingRuleInput",
    "DeleteDeploymentInput",
    "DeploymentFilter",
    "DeploymentOrder",
    "DeploymentPolicyFilter",
    "DeploymentStatusFilter",
    "ExtraVFolderMountInput",
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
    "SearchRoutesInput",
    "SyncReplicaInput",
    "UpdateAutoScalingRuleInput",
    "UpdateDeploymentInput",
    "UpdateRouteTrafficStatusInput",
    "UpsertDeploymentPolicyInput",
)


class ExtraVFolderMountInput(BaseRequestModel):
    """Input for an extra vfolder mount."""

    vfolder_id: UUID = Field(description="VFolder ID to mount")
    mount_destination: str | None = Field(default=None, description="Mount destination path")


class RollingUpdateConfigInput(BaseRequestModel):
    """Input for rolling update configuration."""

    max_surge: int = Field(
        default=1, ge=0, description="Maximum number of extra replicas during update"
    )
    max_unavailable: int = Field(
        default=0, ge=0, description="Maximum number of unavailable replicas during update"
    )


class BlueGreenConfigInput(BaseRequestModel):
    """Input for blue/green deployment configuration."""

    auto_promote: bool = Field(default=False, description="Automatically promote new revision")
    promote_delay_seconds: int = Field(
        default=0, ge=0, description="Delay in seconds before promotion"
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
    extra_mounts: list[ExtraVFolderMountInput] | None = Field(
        default=None, description="Additional vfolder mounts"
    )
    environ: Mapping[str, str] | None = Field(default=None, description="Environment variables")


class CreateDeploymentInput(BaseRequestModel):
    """Input for creating a deployment."""

    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="Deployment name",
    )
    tags: list[str] | None = Field(default=None, description="Deployment tags")
    open_to_public: bool = Field(default=False, description="Whether the deployment is public")
    preferred_domain_name: str | None = Field(
        default=None, description="Preferred domain name for URL"
    )
    strategy: DeploymentStrategy = Field(description="Deployment strategy")
    rollback_on_failure: bool = Field(
        default=False, description="Roll back automatically on failure"
    )
    desired_replica_count: int = Field(ge=0, description="Desired number of replicas")
    initial_revision: RevisionInput = Field(description="Initial revision configuration")
    rolling_update: RollingUpdateConfigInput | None = Field(
        default=None, description="Rolling update config"
    )
    blue_green: BlueGreenConfigInput | None = Field(default=None, description="Blue/green config")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class UpdateDeploymentInput(BaseRequestModel):
    """Input for updating a deployment."""

    name: str | None = Field(default=None, description="Updated deployment name")
    desired_replicas: int | None = Field(
        default=None, ge=0, description="Updated desired replica count"
    )
    tags: list[str] | Sentinel | None = Field(
        default=SENTINEL, description="Updated tags. Use SENTINEL to clear."
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


class DeploymentFilter(BaseRequestModel):
    """Filter for deployments."""

    name: StringFilter | None = Field(default=None, description="Name filter")
    status: DeploymentStatusFilter | None = Field(default=None, description="Status filter")
    open_to_public: bool | None = Field(default=None, description="Public access filter")


class RevisionFilter(BaseRequestModel):
    """Filter for deployment revisions."""

    name: StringFilter | None = Field(default=None, description="Name filter")
    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")


class RouteFilter(BaseRequestModel):
    """Filter for deployment routes."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")
    status: RouteStatusFilter | None = Field(default=None, description="Route status filter")
    traffic_status: RouteTrafficStatusFilter | None = Field(
        default=None, description="Traffic status filter"
    )


class AccessTokenFilter(BaseRequestModel):
    """Filter for access tokens."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")


class AutoScalingRuleFilter(BaseRequestModel):
    """Filter for auto-scaling rules."""

    deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")


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


# ---------------------------------------------------------------------------
# Search input types
# ---------------------------------------------------------------------------


class AdminSearchDeploymentsInput(BaseRequestModel):
    """Input for searching deployments (admin, no scope)."""

    filter: DeploymentFilter | None = Field(default=None, description="Filter criteria")
    order: list[DeploymentOrder] | None = Field(default=None, description="Sort order")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class AdminSearchRevisionsInput(BaseRequestModel):
    """Input for searching deployment revisions (admin, no scope)."""

    filter: RevisionFilter | None = Field(default=None, description="Filter criteria")
    order: list[RevisionOrder] | None = Field(default=None, description="Sort order")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchRoutesInput(BaseRequestModel):
    """Input for searching deployment routes."""

    filter: RouteFilter | None = Field(default=None, description="Filter criteria")
    order: list[RouteOrder] | None = Field(default=None, description="Sort order")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchAccessTokensInput(BaseRequestModel):
    """Input for searching access tokens."""

    filter: AccessTokenFilter | None = Field(default=None, description="Filter criteria")
    order: list[AccessTokenOrder] | None = Field(default=None, description="Sort order")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")


class SearchAutoScalingRulesInput(BaseRequestModel):
    """Input for searching auto-scaling rules."""

    filter: AutoScalingRuleFilter | None = Field(default=None, description="Filter criteria")
    order: list[AutoScalingRuleOrder] | None = Field(default=None, description="Sort order")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
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
    rollback_on_failure: bool = Field(default=False, description="Roll back on failure")
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
