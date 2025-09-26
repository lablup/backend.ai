from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID

from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.data.deployment.types import (
    AccessTokenOrderField,
    DeploymentOrderField,
    ModelRevisionOrderField,
    ReplicaOrderField,
)


@dataclass
class DeploymentOrderingOptions:
    """Ordering options for deployment queries."""

    order_by: list[tuple[DeploymentOrderField, bool]] = field(
        default_factory=lambda: [(DeploymentOrderField.CREATED_AT, True)]
    )  # (field, desc)


@dataclass
class ModelRevisionOrderingOptions:
    """Ordering options for model revision queries."""

    order_by: list[tuple[ModelRevisionOrderField, bool]] = field(
        default_factory=lambda: [(ModelRevisionOrderField.CREATED_AT, True)]
    )  # (field, desc)


@dataclass
class ModelReplicaOrderingOptions:
    """Ordering options for model replica queries."""

    order_by: list[tuple[ReplicaOrderField, bool]] = field(
        default_factory=lambda: [(ReplicaOrderField.CREATED_AT, True)]
    )  # (field, desc)


@dataclass
class AccessTokenOrderingOptions:
    """Ordering options for access token queries."""

    order_by: list[tuple[AccessTokenOrderField, bool]] = field(
        default_factory=lambda: [(AccessTokenOrderField.CREATED_AT, True)]
    )  # (field, desc)


class DeploymentStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class DeploymentStatusFilter:
    """Status filter with operation type and values."""

    type: DeploymentStatusFilterType
    values: list[ModelDeploymentStatus]


@dataclass
class DeploymentFilterOptions:
    """Filtering options for deployments."""

    name: Optional[StringFilter] = None
    status: Optional[DeploymentStatusFilter] = None
    open_to_public: Optional[bool] = None
    tags: Optional[StringFilter] = None
    endpoint_url: Optional[StringFilter] = None
    id: Optional[UUID] = None

    # Logical operations
    AND: Optional[list["DeploymentFilterOptions"]] = None
    OR: Optional[list["DeploymentFilterOptions"]] = None
    NOT: Optional[list["DeploymentFilterOptions"]] = None


@dataclass
class ModelRevisionFilterOptions:
    """Filtering options for model revisions."""

    name: Optional[StringFilter] = None
    deployment_id: Optional[UUID] = None
    id: Optional[UUID] = None
    ids_in: Optional[list[UUID]] = None

    # Logical operations
    AND: Optional[list["ModelRevisionFilterOptions"]] = None
    OR: Optional[list["ModelRevisionFilterOptions"]] = None
    NOT: Optional[list["ModelRevisionFilterOptions"]] = None


class ReadinessStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class ReadinessStatusFilter:
    """Readiness status filter with operation type and values."""

    type: ReadinessStatusFilterType
    values: list[ReadinessStatus]


class LivenessStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class LivenessStatusFilter:
    """Liveness status filter with operation type and values."""

    type: LivenessStatusFilterType
    values: list[LivenessStatus]


class ActivenessStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class ActivenessStatusFilter:
    """Activeness status filter with operation type and values."""

    type: ActivenessStatusFilterType
    values: list[ActivenessStatus]


@dataclass
class ModelReplicaFilterOptions:
    """Filtering options for model replicas."""

    readiness_status_filter: Optional[ReadinessStatusFilter] = None
    liveness_status_filter: Optional[LivenessStatusFilter] = None
    activeness_status_filter: Optional[ActivenessStatusFilter] = None
    id: Optional[UUID] = None
    ids_in: Optional[list[UUID]] = None

    # Logical operations
    AND: Optional[list["ModelReplicaFilterOptions"]] = None
    OR: Optional[list["ModelReplicaFilterOptions"]] = None
    NOT: Optional[list["ModelReplicaFilterOptions"]] = None
