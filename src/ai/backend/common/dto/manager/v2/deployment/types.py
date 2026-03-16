"""
Common types for Deployment DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.types import ClusterMode, RuntimeVariant

__all__ = (
    "BlueGreenConfigInfo",
    "ClusterMode",
    "DeploymentBasicInfo",
    "DeploymentOrderField",
    "DeploymentPolicyInfo",
    "DeploymentRevisionInfo",
    "DeploymentStrategy",
    "EndpointLifecycle",
    "ModelDeploymentStatus",
    "NetworkConfigInfo",
    "OrderDirection",
    "ReplicaStateInfo",
    "RevisionOrderField",
    "RollingUpdateConfigInfo",
    "RouteOrderField",
    "RouteStatus",
    "RouteTrafficStatus",
    "RuntimeVariant",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class DeploymentOrderField(StrEnum):
    """Fields available for ordering deployments."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RevisionOrderField(StrEnum):
    """Fields available for ordering deployment revisions."""

    NAME = "name"
    CREATED_AT = "created_at"


class RouteOrderField(StrEnum):
    """Fields available for ordering deployment routes."""

    CREATED_AT = "created_at"
    STATUS = "status"
    TRAFFIC_RATIO = "traffic_ratio"


class DeploymentBasicInfo(BaseResponseModel):
    """Basic identifying information for a deployment."""

    name: str
    status: ModelDeploymentStatus
    tags: list[str]
    project_id: UUID
    domain_name: str
    created_user_id: UUID


class DeploymentRevisionInfo(BaseResponseModel):
    """Revision configuration details for a deployment."""

    cluster_mode: ClusterMode
    cluster_size: int
    resource_group: str
    resource_slots: dict[str, Any]
    image_id: UUID
    runtime_variant: RuntimeVariant
    model_vfolder_id: UUID | None
    model_mount_destination: str | None
    model_definition_path: str | None


class NetworkConfigInfo(BaseResponseModel):
    """Network configuration for a deployment."""

    open_to_public: bool
    url: str | None
    preferred_domain_name: str | None


class ReplicaStateInfo(BaseResponseModel):
    """Current replica state of a deployment."""

    desired_replica_count: int
    replica_ids: list[UUID]


class RollingUpdateConfigInfo(BaseResponseModel):
    """Rolling update policy configuration."""

    max_surge: int
    max_unavailable: int


class BlueGreenConfigInfo(BaseResponseModel):
    """Blue/green deployment policy configuration."""

    auto_promote: bool
    promote_delay_seconds: int


class DeploymentPolicyInfo(BaseResponseModel):
    """Deployment update policy information."""

    strategy: DeploymentStrategy
    rollback_on_failure: bool
    rolling_update: RollingUpdateConfigInfo | None
    blue_green: BlueGreenConfigInfo | None
