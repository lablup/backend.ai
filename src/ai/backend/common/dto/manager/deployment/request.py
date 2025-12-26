"""
Request DTOs for deployment system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import ClusterMode, RuntimeVariant

from .types import DeploymentOrder, RevisionOrder, RouteOrder

__all__ = (
    # Filters
    "DeploymentFilter",
    "RevisionFilter",
    "RouteFilter",
    # Search/List requests
    "SearchDeploymentsRequest",
    "SearchRevisionsRequest",
    "SearchRoutesRequest",
    # Create requests
    "CreateDeploymentRequest",
    "CreateRevisionRequest",
    # Update requests
    "UpdateDeploymentRequest",
    "UpdateRouteTrafficStatusRequest",
    # Path params
    "DeploymentPathParam",
    "RevisionPathParam",
    "RoutePathParam",
    # Nested input types
    "DeploymentMetadataInput",
    "NetworkAccessInput",
    "DeploymentStrategyInput",
    "RollingUpdateConfigInput",
    "BlueGreenConfigInput",
    "ImageInput",
    "ClusterConfigInput",
    "ResourceConfigInput",
    "ModelMountConfigInput",
    "ModelRuntimeConfigInput",
    "ExtraVFolderMountInput",
    "RevisionInput",
)


class DeploymentFilter(BaseRequestModel):
    """Filter for deployments."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    project_id: Optional[UUID] = Field(default=None, description="Filter by project ID")
    domain_name: Optional[StringFilter] = Field(default=None, description="Filter by domain name")
    status: Optional[list[ModelDeploymentStatus]] = Field(
        default=None, description="Filter by deployment status"
    )


class RevisionFilter(BaseRequestModel):
    """Filter for revisions."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    deployment_id: Optional[UUID] = Field(default=None, description="Filter by deployment ID")


class SearchDeploymentsRequest(BaseRequestModel):
    """Request body for searching deployments with filters, orders, and pagination."""

    filter: Optional[DeploymentFilter] = Field(default=None, description="Filter conditions")
    order: Optional[DeploymentOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchRevisionsRequest(BaseRequestModel):
    """Request body for searching revisions with filters, orders, and pagination."""

    filter: Optional[RevisionFilter] = Field(default=None, description="Filter conditions")
    order: Optional[RevisionOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class UpdateDeploymentRequest(BaseRequestModel):
    """Request to update a deployment."""

    name: Optional[str] = Field(default=None, description="Updated deployment name")
    desired_replicas: Optional[int] = Field(
        default=None, ge=0, description="Updated desired replica count"
    )


class DeploymentPathParam(BaseRequestModel):
    """Path parameter for deployment ID."""

    deployment_id: UUID = Field(description="Deployment ID")


class RevisionPathParam(BaseRequestModel):
    """Path parameter for revision ID."""

    deployment_id: UUID = Field(description="Deployment ID")
    revision_id: UUID = Field(description="Revision ID")


class RouteFilter(BaseRequestModel):
    """Filter for routes."""

    deployment_id: Optional[UUID] = Field(default=None, description="Filter by deployment ID")
    statuses: Optional[list[RouteStatus]] = Field(
        default=None, description="Filter by route status"
    )
    traffic_statuses: Optional[list[RouteTrafficStatus]] = Field(
        default=None, description="Filter by traffic status"
    )


class SearchRoutesRequest(BaseRequestModel):
    """Request body for searching routes with filters, orders, and pagination."""

    filter: Optional[RouteFilter] = Field(default=None, description="Filter conditions")
    order: Optional[RouteOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    # Cursor-based pagination (optional, for forward/backward navigation)
    cursor: Optional[str] = Field(default=None, description="Cursor for pagination")
    cursor_direction: Optional[str] = Field(
        default=None, description="Cursor direction: 'forward' or 'backward'"
    )


class UpdateRouteTrafficStatusRequest(BaseRequestModel):
    """Request to update route traffic status."""

    traffic_status: RouteTrafficStatus = Field(description="New traffic status")


class RoutePathParam(BaseRequestModel):
    """Path parameter for route ID."""

    deployment_id: UUID = Field(description="Deployment ID")
    route_id: UUID = Field(description="Route ID")


# ========== Nested Input Types for Create ==========


class RollingUpdateConfigInput(BaseRequestModel):
    """Configuration for rolling update strategy."""

    max_surge: int = Field(default=1, description="Maximum additional replicas during update")
    max_unavailable: int = Field(
        default=0, description="Maximum unavailable replicas during update"
    )


class BlueGreenConfigInput(BaseRequestModel):
    """Configuration for blue-green deployment strategy."""

    auto_promote: bool = Field(default=False, description="Automatically promote new version")
    promote_delay_seconds: int = Field(
        default=0, description="Delay in seconds before auto promotion"
    )


class DeploymentMetadataInput(BaseRequestModel):
    """Deployment metadata input."""

    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    name: Optional[str] = Field(default=None, description="Deployment name")
    tags: Optional[list[str]] = Field(default=None, description="Tags for the deployment")


class NetworkAccessInput(BaseRequestModel):
    """Network access configuration input."""

    open_to_public: bool = Field(default=False, description="Whether the deployment is public")
    preferred_domain_name: Optional[str] = Field(
        default=None, description="Preferred domain name for the deployment"
    )


class DeploymentStrategyInput(BaseRequestModel):
    """Deployment strategy input."""

    type: DeploymentStrategy = Field(description="Strategy type (ROLLING or BLUE_GREEN)")
    rollback_on_failure: bool = Field(default=False, description="Rollback on failure")
    rolling_update: Optional[RollingUpdateConfigInput] = Field(
        default=None, description="Rolling update configuration"
    )
    blue_green: Optional[BlueGreenConfigInput] = Field(
        default=None, description="Blue-green deployment configuration"
    )


class ImageInput(BaseRequestModel):
    """Container image input."""

    id: UUID = Field(description="Image ID")


class ClusterConfigInput(BaseRequestModel):
    """Cluster configuration input."""

    mode: ClusterMode = Field(description="Cluster mode")
    size: int = Field(default=1, ge=1, description="Cluster size")


class ResourceConfigInput(BaseRequestModel):
    """Resource configuration input."""

    resource_group: str = Field(description="Resource group name")
    resource_slots: Mapping[str, Any] = Field(
        description='Resource slots (e.g., {"cpu": "1", "mem": "1073741824"})'
    )
    resource_opts: Optional[Mapping[str, Any]] = Field(
        default=None, description='Resource options (e.g., {"shmem": "64m"})'
    )


class ModelMountConfigInput(BaseRequestModel):
    """Model mount configuration input."""

    vfolder_id: UUID = Field(description="Model vfolder ID")
    mount_destination: str = Field(default="/models", description="Mount destination path")
    definition_path: str = Field(description="Model definition file path within vfolder")


class ModelRuntimeConfigInput(BaseRequestModel):
    """Model runtime configuration input."""

    runtime_variant: RuntimeVariant = Field(
        default=RuntimeVariant.CUSTOM, description="Runtime variant"
    )
    inference_runtime_config: Optional[Mapping[str, Any]] = Field(
        default=None, description="Inference runtime configuration"
    )
    environ: Optional[Mapping[str, str]] = Field(default=None, description="Environment variables")


class ExtraVFolderMountInput(BaseRequestModel):
    """Extra vfolder mount input."""

    vfolder_id: UUID = Field(description="VFolder ID to mount")
    mount_destination: Optional[str] = Field(default=None, description="Mount destination path")


class RevisionInput(BaseRequestModel):
    """Revision input for creating a new revision."""

    name: Optional[str] = Field(default=None, description="Revision name")
    cluster_config: ClusterConfigInput = Field(description="Cluster configuration")
    resource_config: ResourceConfigInput = Field(description="Resource configuration")
    image: ImageInput = Field(description="Container image")
    model_runtime_config: ModelRuntimeConfigInput = Field(description="Model runtime configuration")
    model_mount_config: ModelMountConfigInput = Field(description="Model mount configuration")
    extra_mounts: Optional[list[ExtraVFolderMountInput]] = Field(
        default=None, description="Extra vfolder mounts"
    )


# ========== Create Requests ==========


class CreateDeploymentRequest(BaseRequestModel):
    """Request to create a new deployment."""

    metadata: DeploymentMetadataInput = Field(description="Deployment metadata")
    network_access: NetworkAccessInput = Field(description="Network access configuration")
    default_deployment_strategy: DeploymentStrategyInput = Field(
        description="Default deployment strategy"
    )
    desired_replica_count: int = Field(ge=0, description="Desired number of replicas")
    initial_revision: RevisionInput = Field(description="Initial revision configuration")


class CreateRevisionRequest(BaseRequestModel):
    """Request to create a new revision for an existing deployment."""

    name: Optional[str] = Field(default=None, description="Revision name")
    cluster_config: ClusterConfigInput = Field(description="Cluster configuration")
    resource_config: ResourceConfigInput = Field(description="Resource configuration")
    image: ImageInput = Field(description="Container image")
    model_runtime_config: ModelRuntimeConfigInput = Field(description="Model runtime configuration")
    model_mount_config: ModelMountConfigInput = Field(description="Model mount configuration")
    extra_mounts: Optional[list[ExtraVFolderMountInput]] = Field(
        default=None, description="Extra vfolder mounts"
    )
