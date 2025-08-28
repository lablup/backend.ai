from dataclasses import dataclass
from enum import StrEnum
from typing import Optional
from uuid import UUID

from ai.backend.common.data.model_deployment.types import (
    LivenessStatus,
    ModelDeploymentStatus,
    ReadinessStatus,
)
from ai.backend.manager.api.gql.base import StringFilter


class ReadinessStatusFilterType(StrEnum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class ReadinessStatusFilterOptions:
    type: ReadinessStatusFilterType
    values: list[ReadinessStatus]


class LivenessStatusFilterType(StrEnum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class LivenessStatusFilterOptions:
    """Repository layer filter options for liveness status."""

    type: LivenessStatusFilterType
    values: list[LivenessStatus]


@dataclass
class ModelReplicaFilterOptions:
    """Repository layer filter options for replica queries."""

    readiness_status: Optional[ReadinessStatusFilterOptions] = None
    liveness_status: Optional[LivenessStatusFilterOptions] = None

    # Logical operations
    AND: Optional[list["ModelReplicaFilterOptions"]] = None
    OR: Optional[list["ModelReplicaFilterOptions"]] = None
    NOT: Optional[list["ModelReplicaFilterOptions"]] = None
    DISTINCT: Optional[bool] = None


class DeploymentStatusFilterType(StrEnum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class DeploymentStatusFilterOptions:
    type: DeploymentStatusFilterType
    values: list[ModelDeploymentStatus]


@dataclass
class DeploymentFilterOptions:
    """Repository layer filter options for deployment queries."""

    name: Optional[StringFilter] = None
    status: Optional[DeploymentStatusFilterOptions] = None
    open_to_public: Optional[bool] = None
    tags: Optional[StringFilter] = None

    # Logical operations
    AND: Optional[list["DeploymentFilterOptions"]] = None
    OR: Optional[list["DeploymentFilterOptions"]] = None
    NOT: Optional[list["DeploymentFilterOptions"]] = None
    DISTINCT: Optional[bool] = None


@dataclass
class ModelRevisionFilterOptions:
    """Repository layer filter options for model revision queries."""

    name: Optional[StringFilter] = None
    deployment_id: Optional[UUID] = None

    # Logical operations
    AND: Optional[list["ModelRevisionFilterOptions"]] = None
    OR: Optional[list["ModelRevisionFilterOptions"]] = None
    NOT: Optional[list["ModelRevisionFilterOptions"]] = None
    DISTINCT: Optional[bool] = None
