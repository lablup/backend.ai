"""
Response DTOs for deployment system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.types import ClusterMode, RuntimeVariant

__all__ = (
    # DTOs
    "DeploymentDTO",
    "DeploymentPolicyDTO",
    "RevisionDTO",
    "RouteDTO",
    "NetworkConfigDTO",
    "ClusterConfigDTO",
    "ResourceConfigDTO",
    "ModelRuntimeConfigDTO",
    "ModelMountConfigDTO",
    "ReplicaStateDTO",
    "PreStartActionDTO",
    "ModelHealthCheckDTO",
    "ModelServiceConfigDTO",
    "ModelMetadataDTO",
    "ModelConfigDTO",
    "ModelDefinitionDTO",
    # Responses
    "CreateDeploymentResponse",
    "UpsertDeploymentPolicyResponse",
    "GetDeploymentResponse",
    "GetDeploymentPolicyResponse",
    "GetModelDefinitionResponse",
    "ListDeploymentPoliciesResponse",
    "ListDeploymentsResponse",
    "UpdateDeploymentResponse",
    "DestroyDeploymentResponse",
    "GetRevisionResponse",
    "AddRevisionResponse",
    "ListRevisionsResponse",
    "ActivateRevisionResponse",
    "DeactivateRevisionResponse",
    "ListRoutesResponse",
    "UpdateRouteTrafficStatusResponse",
    # Pagination
    "PaginationInfo",
    "CursorPaginationInfo",
)


class PreStartActionDTO(BaseModel):
    """Action to execute before the model service starts (e.g. downloading weights, warming up caches)."""

    action: str = Field(
        description="Identifier of the pre-start action to execute (e.g. 'download_weights', 'warm_cache')"
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value arguments passed to the pre-start action handler",
    )


class ModelHealthCheckDTO(BaseModel):
    """HTTP health-check configuration that the platform uses to determine whether a model service replica is healthy and ready to receive traffic."""

    interval: float = Field(
        default=10.0,
        description="Interval in seconds between consecutive health check requests",
    )
    path: str = Field(
        description="HTTP path on the model service to probe for health status (e.g. '/health', '/v1/models')"
    )
    max_retries: int = Field(
        default=10,
        description="Maximum number of consecutive health check failures before marking the replica as unhealthy",
    )
    max_wait_time: float = Field(
        default=15.0,
        description="Maximum time in seconds to wait for a single health check response before treating it as a failure",
    )
    expected_status_code: int = Field(
        default=200,
        description="HTTP status code that indicates a healthy response (e.g. 200)",
    )
    initial_delay: float = Field(
        default=60.0,
        description="Time in seconds to wait after the container starts before sending the first health check request",
    )


class ModelServiceConfigDTO(BaseModel):
    """Runtime service configuration that defines how a model is started, exposed, and monitored inside the container."""

    pre_start_actions: list[PreStartActionDTO] = Field(
        default_factory=list,
        description="Ordered list of actions to execute before the service starts (e.g. weight download, cache warming)",
    )
    start_command: str | list[str] = Field(
        description="Shell command (string) or argument list to launch the model service process (e.g. 'python serve.py' or ['python', 'serve.py'])"
    )
    shell: str = Field(
        default="/bin/bash",
        description="Shell interpreter used when start_command is provided as a single string",
    )
    port: int = Field(
        description="TCP port number on which the model service listens for inference requests"
    )
    health_check: ModelHealthCheckDTO | None = Field(
        default=None,
        description="Optional HTTP health check configuration; when omitted, the platform relies on process liveness only",
    )


class ModelMetadataDTO(BaseModel):
    """Descriptive metadata about a model, used for catalog display, search filtering, and resource planning."""

    author: str | None = Field(
        default=None, description="Author or organization that created the model"
    )
    title: str | None = Field(default=None, description="Human-readable display name of the model")
    version: int | str | None = Field(
        default=None,
        description="Version identifier of the model (integer or semantic version string)",
    )
    created: str | None = Field(
        default=None, description="ISO 8601 timestamp when the model was originally created"
    )
    last_modified: str | None = Field(
        default=None,
        description="ISO 8601 timestamp of the most recent modification to the model",
    )
    description: str | None = Field(
        default=None,
        description="Free-form text describing what the model does and its intended use",
    )
    task: str | None = Field(
        default=None,
        description="Primary ML task the model performs (e.g. 'Text Generation', 'Image Classification', 'Object Detection')",
    )
    category: str | None = Field(
        default=None,
        description="High-level category for grouping models (e.g. 'NLP', 'Vision', 'Audio')",
    )
    architecture: str | None = Field(
        default=None,
        description="Neural network architecture name (e.g. 'Transformer', 'ResNet', 'Diffusion')",
    )
    framework: list[str] | None = Field(
        default=None,
        description="List of ML frameworks the model depends on (e.g. ['PyTorch', 'HuggingFace Transformers'])",
    )
    label: list[str] | None = Field(
        default=None,
        description="User-defined tags for search and filtering (e.g. ['production', 'korean', 'chat'])",
    )
    license: str | None = Field(
        default=None,
        description="SPDX license identifier or license name (e.g. 'Apache-2.0', 'MIT')",
    )
    min_resource: dict[str, Any] | None = Field(
        default=None,
        description="Minimum compute resources required to run the model, keyed by slot type (e.g. {'cuda.shares': 0.5, 'mem': '16g'})",
    )


class ModelConfigDTO(BaseModel):
    """Configuration for an individual model entry within a model definition file, describing where the model resides, how to serve it, and its metadata."""

    name: str = Field(description="Unique name identifying this model within the model definition")
    model_path: str = Field(
        description="Absolute path inside the container where the model weights/files are mounted (e.g. '/models/my_model')"
    )
    service: ModelServiceConfigDTO | None = Field(
        default=None,
        description="Service configuration defining how to start and monitor the model; omit for models that are loaded by another service",
    )
    metadata: ModelMetadataDTO | None = Field(
        default=None,
        description="Optional descriptive metadata about the model for catalog display and resource planning",
    )


class ModelDefinitionDTO(BaseModel):
    """Top-level model definition describing one or more models to be served within a single deployment revision. Corresponds to the contents of a model-definition.yaml file."""

    models: list[ModelConfigDTO] = Field(
        default_factory=list,
        description="List of model configurations to serve; each entry defines a distinct model with its own path, service config, and metadata",
    )


class NetworkConfigDTO(BaseModel):
    """Network configuration for deployment."""

    open_to_public: bool = Field(description="Whether the deployment is public")
    url: str | None = Field(default=None, description="Deployment URL")
    preferred_domain_name: str | None = Field(default=None, description="Preferred domain name")


class ClusterConfigDTO(BaseModel):
    """Cluster configuration for revision."""

    mode: ClusterMode = Field(description="Cluster mode")
    size: int = Field(description="Cluster size")


class ResourceConfigDTO(BaseModel):
    """Resource configuration for revision."""

    resource_group_name: str = Field(description="Resource group name")
    resource_slot: dict[str, Any] = Field(description="Resource slot allocation")


class ModelRuntimeConfigDTO(BaseModel):
    """Model runtime configuration for revision."""

    runtime_variant: RuntimeVariant = Field(description="Runtime variant")


class ModelMountConfigDTO(BaseModel):
    """Model mount configuration for revision."""

    vfolder_id: UUID = Field(description="VFolder ID for model")
    mount_destination: str | None = Field(description="Mount destination path")
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
    current_revision: RevisionDTO | None = Field(
        default=None, description="Current active revision"
    )
    deployment_policy: DeploymentPolicyDTO | None = Field(
        default=None, description="Deployment rollout policy"
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


class GetModelDefinitionResponse(BaseResponseModel):
    """Response for getting the model definition of a deployment's active revision."""

    model_definition: ModelDefinitionDTO = Field(description="Parsed model definition content")


class GetRevisionResponse(BaseResponseModel):
    """Response for getting a revision."""

    revision: RevisionDTO = Field(description="Revision data")


class AddRevisionResponse(BaseResponseModel):
    """Response for adding a new revision to a deployment."""

    revision: RevisionDTO = Field(description="Created revision")


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
    session_id: str | None = Field(default=None, description="Session ID")
    status: RouteStatus = Field(description="Route status")
    traffic_ratio: float = Field(description="Traffic ratio for this route")
    created_at: datetime = Field(description="Creation timestamp")
    revision_id: UUID | None = Field(default=None, description="Revision ID")
    traffic_status: RouteTrafficStatus = Field(description="Traffic status")
    error_data: dict[str, Any] = Field(default_factory=dict, description="Error data if any")


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


# ========== Deployment Policy DTOs ==========


class DeploymentPolicyDTO(BaseModel):
    """DTO representing the rollout policy for a deployment.

    Controls how new revisions are promoted to production traffic,
    including the update strategy and automatic rollback behavior.
    """

    id: UUID = Field(description="Unique identifier of this deployment policy")
    deployment_id: UUID = Field(description="UUID of the deployment this policy belongs to")
    strategy: DeploymentStrategy = Field(
        description="Configured rollout strategy type (ROLLING for gradual replacement, BLUE_GREEN for parallel environment switching)"
    )
    strategy_spec: dict[str, Any] = Field(
        description="Raw strategy-specific parameters stored as a dictionary; contains rolling update or blue-green fields depending on the active strategy"
    )
    rollback_on_failure: bool = Field(
        description="Whether the system automatically reverts to the previous stable revision when health checks fail during rollout"
    )
    created_at: datetime = Field(
        description="UTC timestamp when this deployment policy was created"
    )
    updated_at: datetime = Field(
        description="UTC timestamp of the last modification to this deployment policy"
    )


class UpsertDeploymentPolicyResponse(BaseResponseModel):
    """Response for creating or updating a deployment policy."""

    deployment_policy: DeploymentPolicyDTO = Field(description="The deployment policy")
    created: bool = Field(
        description="True if a new policy was created, False if an existing one was updated"
    )


class ListDeploymentPoliciesResponse(BaseResponseModel):
    """Response for listing deployment policies."""

    deployment_policies: list[DeploymentPolicyDTO] = Field(
        description="List of deployment policies"
    )
    pagination: PaginationInfo = Field(description="Pagination information")


class GetDeploymentPolicyResponse(BaseResponseModel):
    """Response for getting a deployment policy."""

    deployment_policy: DeploymentPolicyDTO = Field(description="Deployment policy data")
