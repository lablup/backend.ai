"""
Response DTOs for Deployment DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    LivenessStatus,
    ReadinessStatus,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenStrategySpecInfo,
    ClusterConfigInfoDTO,
    DeploymentMetadataInfoDTO,
    DeploymentNetworkAccessInfoDTO,
    DeploymentPolicyInfo,
    DeploymentStrategyInfoDTO,
    ExtraVFolderMountGQLDTO,
    ModelDefinitionInfoDTO,
    ModelMountConfigInfoDTO,
    ModelRuntimeConfigInfoDTO,
    ReplicaStateInfo,
    ResourceConfigInfoDTO,
    RollingUpdateStrategySpecInfo,
)

__all__ = (
    "AccessTokenNode",
    "ActivateDeploymentPayload",
    "ActivateRevisionPayload",
    "AddRevisionPayload",
    "AdminSearchDeploymentsPayload",
    "AdminSearchRevisionsPayload",
    "AutoScalingRuleNode",
    "CreateAccessTokenPayload",
    "CreateAutoScalingRulePayload",
    "CreateDeploymentPayload",
    "DeleteAutoScalingRulePayload",
    "DeleteDeploymentPayload",
    "DeploymentNode",
    "DeploymentPolicyNode",
    "DeploymentStatusChangedPayload",
    "ExtraVFolderMountNode",
    "GetAutoScalingRulePayload",
    "GetDeploymentPolicyPayload",
    "ReplicaNode",
    "ReplicaStatusChangedPayload",
    "RevisionNode",
    "RouteNode",
    "ScaleDeploymentPayload",
    "SearchAccessTokensPayload",
    "SearchAutoScalingRulesPayload",
    "SearchDeploymentPoliciesPayload",
    "SearchReplicasPayload",
    "SearchRoutesPayload",
    "SyncReplicaPayload",
    "UpdateAutoScalingRulePayload",
    "UpdateDeploymentPayload",
    "UpdateDeploymentPolicyPayloadDTO",
    "UpdateRouteTrafficStatusPayload",
    "UpsertDeploymentPolicyPayload",
)


class ExtraVFolderMountNode(BaseResponseModel):
    """Node model representing an extra vfolder mount."""

    vfolder_id: UUID = Field(description="VFolder ID")
    mount_destination: str | None = Field(default=None, description="Mount destination path")


class RevisionNode(BaseResponseModel):
    """Node model representing a deployment revision."""

    id: UUID = Field(description="Revision ID")
    name: str = Field(description="Revision name")
    image_id: UUID = Field(description="Image ID for this revision")
    cluster_config: ClusterConfigInfoDTO = Field(description="Cluster configuration")
    resource_config: ResourceConfigInfoDTO = Field(description="Resource configuration")
    model_runtime_config: ModelRuntimeConfigInfoDTO = Field(description="Runtime configuration")
    model_mount_config: ModelMountConfigInfoDTO | None = Field(
        default=None, description="Model mount configuration"
    )
    model_definition: ModelDefinitionInfoDTO | None = Field(
        default=None, description="Model definition configuration"
    )
    created_at: datetime = Field(description="Creation timestamp")
    extra_mounts: list[ExtraVFolderMountGQLDTO] = Field(
        default_factory=list, description="Extra vfolder mounts"
    )


class DeploymentNode(BaseResponseModel):
    """Node model representing a deployment entity."""

    id: UUID = Field(description="Deployment ID")
    metadata: DeploymentMetadataInfoDTO = Field(description="Deployment metadata")
    network_access: DeploymentNetworkAccessInfoDTO = Field(
        description="Network access configuration"
    )
    replica_state: ReplicaStateInfo = Field(description="Current replica state")
    default_deployment_strategy: DeploymentStrategyInfoDTO = Field(
        description="Default deployment update strategy"
    )
    created_user_id: UUID = Field(description="ID of the user who created this deployment")
    current_revision_id: UUID | None = Field(
        default=None, description="ID of the currently active revision"
    )
    policy: DeploymentPolicyInfo | None = Field(
        default=None, description="Deployment update policy"
    )


class RouteNode(BaseResponseModel):
    """Node model representing a deployment route."""

    id: UUID = Field(description="Route ID")
    deployment_id: UUID = Field(description="Deployment ID")
    session_id: str | None = Field(default=None, description="Session ID")
    status: RouteStatus = Field(description="Lifecycle status of the route")
    health_status: RouteHealthStatus = Field(description="Health check status of the route")
    traffic_ratio: float = Field(description="Traffic ratio assigned to this route")
    created_at: datetime = Field(description="Creation timestamp")
    revision_id: UUID | None = Field(default=None, description="Associated revision ID")
    traffic_status: RouteTrafficStatus = Field(description="Traffic status of the route")
    error_data: dict[str, Any] = Field(default_factory=dict, description="Error data if any")


class CreateDeploymentPayload(BaseResponseModel):
    """Payload for deployment creation mutation result."""

    deployment: DeploymentNode = Field(description="Created deployment")


class UpdateDeploymentPayload(BaseResponseModel):
    """Payload for deployment update mutation result."""

    deployment: DeploymentNode = Field(description="Updated deployment")


class DeleteDeploymentPayload(BaseResponseModel):
    """Payload for deployment deletion mutation result."""

    id: UUID = Field(description="ID of the deleted deployment")


class ActivateDeploymentPayload(BaseResponseModel):
    """Payload for deployment activation mutation result."""

    success: bool = Field(description="Whether the activation succeeded")


class SyncReplicaPayload(BaseResponseModel):
    """Payload for replica sync mutation result."""

    success: bool = Field(description="Whether the sync succeeded")


class ScaleDeploymentPayload(BaseResponseModel):
    """Payload for deployment scale mutation result."""

    deployment: DeploymentNode = Field(description="Scaled deployment")


class AddRevisionPayload(BaseResponseModel):
    """Payload for add revision mutation result."""

    revision: RevisionNode = Field(description="Added revision")


# ---------------------------------------------------------------------------
# New Node types for sub-entities
# ---------------------------------------------------------------------------


class AccessTokenNode(BaseResponseModel):
    """Node model representing a deployment access token."""

    id: UUID = Field(description="Access token ID")
    token: str = Field(description="Token value")
    valid_until: datetime = Field(description="Token expiration timestamp")
    created_at: datetime = Field(description="Creation timestamp")


class AutoScalingRuleNode(BaseResponseModel):
    """Node model representing a deployment auto-scaling rule."""

    id: UUID = Field(description="Auto-scaling rule ID")
    deployment_id: UUID = Field(description="Parent deployment ID")
    metric_source: str = Field(description="Metric source")
    metric_name: str = Field(description="Metric name")
    min_threshold: Decimal | None = Field(default=None, description="Minimum threshold")
    max_threshold: Decimal | None = Field(default=None, description="Maximum threshold")
    step_size: int = Field(description="Scale step size")
    time_window: int = Field(description="Time window in seconds")
    min_replicas: int | None = Field(default=None, description="Minimum replicas")
    max_replicas: int | None = Field(default=None, description="Maximum replicas")
    created_at: datetime = Field(description="Creation timestamp")
    last_triggered_at: datetime = Field(description="Last triggered timestamp")


class DeploymentPolicyNode(BaseResponseModel):
    """Node model representing a deployment update policy."""

    id: UUID = Field(description="Policy ID")
    deployment_id: UUID = Field(description="Parent deployment ID")
    strategy_spec: RollingUpdateStrategySpecInfo | BlueGreenStrategySpecInfo = Field(
        description="Deployment strategy specification"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


# ---------------------------------------------------------------------------
# Search payloads
# ---------------------------------------------------------------------------


class AdminSearchDeploymentsPayload(BaseResponseModel):
    """Payload for admin deployment search result."""

    items: list[DeploymentNode] = Field(description="Deployment list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class AdminSearchRevisionsPayload(BaseResponseModel):
    """Payload for admin revision search result."""

    items: list[RevisionNode] = Field(description="Revision list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class SearchRoutesPayload(BaseResponseModel):
    """Payload for route search result."""

    items: list[RouteNode] = Field(description="Route list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class CreateAccessTokenPayload(BaseResponseModel):
    """Payload for access token creation result."""

    access_token: AccessTokenNode = Field(description="Created access token")


class SearchAccessTokensPayload(BaseResponseModel):
    """Payload for access token search result."""

    items: list[AccessTokenNode] = Field(description="Access token list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class CreateAutoScalingRulePayload(BaseResponseModel):
    """Payload for auto-scaling rule creation result."""

    rule: AutoScalingRuleNode = Field(description="Created auto-scaling rule")


class GetAutoScalingRulePayload(BaseResponseModel):
    """Payload for auto-scaling rule get result."""

    rule: AutoScalingRuleNode = Field(description="Auto-scaling rule")


class UpdateAutoScalingRulePayload(BaseResponseModel):
    """Payload for auto-scaling rule update result."""

    rule: AutoScalingRuleNode = Field(description="Updated auto-scaling rule")


class DeleteAutoScalingRulePayload(BaseResponseModel):
    """Payload for auto-scaling rule deletion result."""

    id: UUID = Field(description="ID of the deleted auto-scaling rule")


class SearchAutoScalingRulesPayload(BaseResponseModel):
    """Payload for auto-scaling rule search result."""

    items: list[AutoScalingRuleNode] = Field(description="Auto-scaling rule list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class GetDeploymentPolicyPayload(BaseResponseModel):
    """Payload for deployment policy get result."""

    policy: DeploymentPolicyNode = Field(description="Deployment policy")


class UpsertDeploymentPolicyPayload(BaseResponseModel):
    """Payload for deployment policy upsert result."""

    policy: DeploymentPolicyNode = Field(description="Created or updated deployment policy")


class SearchDeploymentPoliciesPayload(BaseResponseModel):
    """Payload for deployment policy search result."""

    items: list[DeploymentPolicyNode] = Field(description="Deployment policy list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class ReplicaNode(BaseResponseModel):
    """Node model representing a deployment replica (user-facing view of routing row)."""

    id: UUID = Field(description="Replica ID")
    revision_id: UUID = Field(description="Associated revision ID")
    session_id: UUID = Field(description="Associated session ID")
    readiness_status: ReadinessStatus = Field(description="Readiness status")
    liveness_status: LivenessStatus = Field(description="Liveness status")
    activeness_status: ActivenessStatus = Field(description="Activeness status")
    weight: int = Field(description="Traffic weight for load balancing")
    created_at: datetime = Field(description="Creation timestamp")


class SearchReplicasPayload(BaseResponseModel):
    """Payload for replica search result."""

    items: list[ReplicaNode] = Field(description="Replica list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class DeploymentStatusChangedPayload(BaseResponseModel):
    """Payload for deployment status changed subscription event."""

    deployment: DeploymentNode = Field(description="The deployment whose status changed")


class ReplicaStatusChangedPayload(BaseResponseModel):
    """Payload for replica status changed subscription event."""

    replica: ReplicaNode = Field(description="The replica whose status changed")


class ActivateRevisionPayload(BaseResponseModel):
    """Payload for activate revision mutation result."""

    deployment: DeploymentNode = Field(description="The deployment with the activated revision")
    previous_revision_id: UUID | None = Field(
        default=None, description="ID of the previously active revision"
    )
    activated_revision_id: UUID = Field(description="ID of the newly activated revision")
    deployment_policy: DeploymentPolicyNode = Field(
        description="The deployment policy applied during activation"
    )


class UpdateRouteTrafficStatusPayload(BaseResponseModel):
    """Payload for update route traffic status mutation result."""

    route: RouteNode = Field(description="The updated route")


class UpdateDeploymentPolicyPayloadDTO(BaseResponseModel):
    """Payload returned after updating a deployment policy."""

    deployment_policy: DeploymentPolicyNode = Field(description="The updated deployment policy")
