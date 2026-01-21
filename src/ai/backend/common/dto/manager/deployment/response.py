"""
Response DTOs for deployment system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.types import ClusterMode, RuntimeVariant

__all__ = (
    # DTOs
    "DeploymentDTO",
    "RevisionDTO",
    "RouteDTO",
    "NetworkConfigDTO",
    "ClusterConfigDTO",
    "ResourceConfigDTO",
    "ModelRuntimeConfigDTO",
    "ModelMountConfigDTO",
    "ReplicaStateDTO",
    # Responses
    "CreateDeploymentResponse",
    "GetDeploymentResponse",
    "ListDeploymentsResponse",
    "UpdateDeploymentResponse",
    "DestroyDeploymentResponse",
    "CreateRevisionResponse",
    "GetRevisionResponse",
    "ListRevisionsResponse",
    "ActivateRevisionResponse",
    "DeactivateRevisionResponse",
    "ListRoutesResponse",
    "UpdateRouteTrafficStatusResponse",
    # Pagination
    "PaginationInfo",
    "CursorPaginationInfo",
)


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: Optional[int] = Field(default=None, description="Maximum items returned")


class NetworkConfigDTO(BaseModel):
    """Network configuration for deployment."""

    open_to_public: bool = Field(description="Whether the deployment is public")
    url: Optional[str] = Field(default=None, description="Deployment URL")
    preferred_domain_name: Optional[str] = Field(default=None, description="Preferred domain name")


class ClusterConfigDTO(BaseModel):
    """Cluster configuration for revision."""

    mode: ClusterMode = Field(description="Cluster mode")
    size: int = Field(description="Cluster size")


class ResourceConfigDTO(BaseModel):
    """Resource configuration for revision."""

    resource_group_name: str = Field(description="Resource group name")
    resource_slot: dict = Field(description="Resource slot allocation")


class ModelRuntimeConfigDTO(BaseModel):
    """Model runtime configuration for revision."""

    runtime_variant: RuntimeVariant = Field(description="Runtime variant")


class ModelMountConfigDTO(BaseModel):
    """Model mount configuration for revision."""

    vfolder_id: UUID = Field(description="VFolder ID for model")
    mount_destination: str = Field(description="Mount destination path")
    definition_path: str = Field(description="Model definition path")


class ReplicaStateDTO(BaseModel):
    """Replica state information."""

    desired_replica_count: int = Field(description="Desired number of replicas")
    replica_ids: list[UUID] = Field(description="IDs of current replicas")


class RevisionDTO(BaseModel):
    """DTO for model revision data."""

    id: UUID = Field(description="Revision ID")
    name: str = Field(description="Revision name")
    cluster_config: ClusterConfigDTO = Field(description="Cluster configuration")
    resource_config: ResourceConfigDTO = Field(description="Resource configuration")
    model_runtime_config: ModelRuntimeConfigDTO = Field(description="Model runtime configuration")
    model_mount_config: ModelMountConfigDTO = Field(description="Model mount configuration")
    created_at: datetime = Field(description="Creation timestamp")
    image_id: UUID = Field(description="Image ID")


class DeploymentDTO(BaseModel):
    """DTO for deployment data."""

    id: UUID = Field(description="Deployment ID")
    name: str = Field(description="Deployment name")
    status: ModelDeploymentStatus = Field(description="Deployment status")
    tags: list[str] = Field(default_factory=list, description="Deployment tags")
    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    created_user_id: UUID = Field(description="ID of user who created the deployment")
    network_config: NetworkConfigDTO = Field(description="Network configuration")
    replica_state: ReplicaStateDTO = Field(description="Replica state")
    default_deployment_strategy: DeploymentStrategy = Field(
        description="Default deployment strategy"
    )
    current_revision: Optional[RevisionDTO] = Field(
        default=None, description="Current active revision"
    )


class CreateDeploymentResponse(BaseResponseModel):
    """Response for creating a deployment."""

    deployment: DeploymentDTO = Field(description="Created deployment")


class GetDeploymentResponse(BaseResponseModel):
    """Response for getting a deployment."""

    deployment: DeploymentDTO = Field(description="Deployment data")


class ListDeploymentsResponse(BaseResponseModel):
    """Response for listing deployments."""

    deployments: list[DeploymentDTO] = Field(description="List of deployments")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateDeploymentResponse(BaseResponseModel):
    """Response for updating a deployment."""

    deployment: DeploymentDTO = Field(description="Updated deployment")


class DestroyDeploymentResponse(BaseResponseModel):
    """Response for destroying a deployment."""

    deleted: bool = Field(description="Whether the deployment was deleted")


class CreateRevisionResponse(BaseResponseModel):
    """Response for creating a revision."""

    revision: RevisionDTO = Field(description="Created revision")


class GetRevisionResponse(BaseResponseModel):
    """Response for getting a revision."""

    revision: RevisionDTO = Field(description="Revision data")


class ListRevisionsResponse(BaseResponseModel):
    """Response for listing revisions."""

    revisions: list[RevisionDTO] = Field(description="List of revisions")
    pagination: PaginationInfo = Field(description="Pagination information")


class ActivateRevisionResponse(BaseResponseModel):
    """Response for activating a revision."""

    success: bool = Field(description="Whether the revision was activated")


class DeactivateRevisionResponse(BaseResponseModel):
    """Response for deactivating a revision."""

    success: bool = Field(description="Whether the revision was deactivated")


class RouteDTO(BaseModel):
    """DTO for route data."""

    id: UUID = Field(description="Route ID")
    endpoint_id: UUID = Field(description="Endpoint/Deployment ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    status: RouteStatus = Field(description="Route status")
    traffic_ratio: float = Field(description="Traffic ratio for this route")
    created_at: datetime = Field(description="Creation timestamp")
    revision_id: Optional[UUID] = Field(default=None, description="Revision ID")
    traffic_status: RouteTrafficStatus = Field(description="Traffic status")
    error_data: dict = Field(default_factory=dict, description="Error data if any")


class CursorPaginationInfo(BaseModel):
    """Cursor-based pagination information."""

    total_count: int = Field(description="Total number of items")
    has_next_page: bool = Field(description="Whether there are more items")
    has_previous_page: bool = Field(description="Whether there are previous items")


class ListRoutesResponse(BaseResponseModel):
    """Response for listing routes."""

    routes: list[RouteDTO] = Field(description="List of routes")
    pagination: CursorPaginationInfo = Field(description="Pagination information")


class UpdateRouteTrafficStatusResponse(BaseResponseModel):
    """Response for updating route traffic status."""

    route: RouteDTO = Field(description="Updated route")
