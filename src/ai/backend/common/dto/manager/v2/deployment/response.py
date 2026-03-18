"""
Response DTOs for Deployment DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    DeploymentBasicInfo,
    DeploymentPolicyInfo,
    DeploymentRevisionInfo,
    NetworkConfigInfo,
    ReplicaStateInfo,
)

__all__ = (
    "ActivateDeploymentPayload",
    "AddRevisionPayload",
    "CreateDeploymentPayload",
    "DeleteDeploymentPayload",
    "DeploymentNode",
    "ExtraVFolderMountNode",
    "RevisionNode",
    "RouteNode",
    "ScaleDeploymentPayload",
    "UpdateDeploymentPayload",
)


class ExtraVFolderMountNode(BaseResponseModel):
    """Node model representing an extra vfolder mount."""

    vfolder_id: UUID = Field(description="VFolder ID")
    mount_destination: str | None = Field(default=None, description="Mount destination path")


class RevisionNode(BaseResponseModel):
    """Node model representing a deployment revision."""

    id: UUID = Field(description="Revision ID")
    name: str = Field(description="Revision name")
    revision_info: DeploymentRevisionInfo = Field(description="Revision configuration details")
    created_at: datetime = Field(description="Creation timestamp")
    extra_mounts: list[ExtraVFolderMountNode] = Field(
        default_factory=list, description="Extra vfolder mounts"
    )


class DeploymentNode(BaseResponseModel):
    """Node model representing a deployment entity."""

    id: UUID = Field(description="Deployment ID")
    basic: DeploymentBasicInfo = Field(description="Basic deployment information")
    network: NetworkConfigInfo = Field(description="Network configuration")
    replica_state: ReplicaStateInfo = Field(description="Current replica state")
    default_deployment_strategy: DeploymentStrategy = Field(
        description="Default deployment update strategy"
    )
    current_revision: RevisionNode | None = Field(
        default=None, description="Currently active revision"
    )
    policy: DeploymentPolicyInfo | None = Field(
        default=None, description="Deployment update policy"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class RouteNode(BaseResponseModel):
    """Node model representing a deployment route."""

    id: UUID = Field(description="Route ID")
    endpoint_id: UUID = Field(description="Endpoint ID")
    session_id: str | None = Field(default=None, description="Session ID")
    status: RouteStatus = Field(description="Route status")
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


class ScaleDeploymentPayload(BaseResponseModel):
    """Payload for deployment scale mutation result."""

    deployment: DeploymentNode = Field(description="Scaled deployment")


class AddRevisionPayload(BaseResponseModel):
    """Payload for add revision mutation result."""

    revision: RevisionNode = Field(description="Added revision")
