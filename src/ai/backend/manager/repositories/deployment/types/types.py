from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
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

    name: StringFilter | None = None
    status: DeploymentStatusFilter | None = None
    open_to_public: bool | None = None
    tags: StringFilter | None = None
    endpoint_url: StringFilter | None = None
    id: UUID | None = None

    # Logical operations
    AND: list[DeploymentFilterOptions] | None = None
    OR: list[DeploymentFilterOptions] | None = None
    NOT: list[DeploymentFilterOptions] | None = None


@dataclass
class ModelRevisionFilterOptions:
    """Filtering options for model revisions."""

    name: StringFilter | None = None
    deployment_id: UUID | None = None
    id: UUID | None = None
    ids_in: list[UUID] | None = None

    # Logical operations
    AND: list[ModelRevisionFilterOptions] | None = None
    OR: list[ModelRevisionFilterOptions] | None = None
    NOT: list[ModelRevisionFilterOptions] | None = None


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

    readiness_status_filter: ReadinessStatusFilter | None = None
    liveness_status_filter: LivenessStatusFilter | None = None
    activeness_status_filter: ActivenessStatusFilter | None = None
    id: UUID | None = None
    ids_in: list[UUID] | None = None

    # Logical operations
    AND: list[ModelReplicaFilterOptions] | None = None
    OR: list[ModelReplicaFilterOptions] | None = None
    NOT: list[ModelReplicaFilterOptions] | None = None
