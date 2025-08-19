"""Common types for deployment package."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)


class DeploymentStatus(StrEnum):
    """Deployment lifecycle status."""

    CREATING = "creating"
    READY = "ready"
    SCALING = "scaling"
    UPDATING = "updating"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    ERROR = "error"


class ReplicaStatus(StrEnum):
    """Replica (session) status for deployment."""

    PROVISIONING = "provisioning"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class SyncStatus(StrEnum):
    """Synchronization status between routing and session."""

    SYNCED = "synced"
    OUT_OF_SYNC = "out_of_sync"
    UNKNOWN = "unknown"


class ReadinessStatus(StrEnum):
    """Readiness status from health checks."""

    READY = "ready"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EndpointSpec:
    """Specification for creating an endpoint."""

    name: str
    model_id: UUID
    replicas: int
    runtime_variant: RuntimeVariant
    resources: ResourceSlot
    image: str
    architecture: str
    scaling_group: str
    extra_mounts: list[VFolderMount]
    environ: dict[str, str]
    open_to_public: bool
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None


@dataclass(frozen=True)
class NetworkConfig:
    """Network configuration for deployment."""

    endpoint_id: UUID
    port_mappings: dict[str, int]
    subdomain: Optional[str] = None


@dataclass(frozen=True)
class AutoScalingRule:
    """Auto-scaling rule definition."""

    id: UUID
    endpoint_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: Decimal
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]


@dataclass(frozen=True)
class ScalingDecision:
    """Decision made by auto-scaler."""

    endpoint_id: UUID
    current_replicas: int
    target_replicas: int
    reason: str
    metric_value: Optional[float] = None
    rule_id: Optional[UUID] = None
    timestamp: Optional[datetime] = None


@dataclass(frozen=True)
class ScalingResult:
    """Result of scaling operation."""

    endpoint_id: UUID
    previous_replicas: int
    current_replicas: int
    success: bool
    message: str
    created_replicas: list[UUID] = None
    destroyed_replicas: list[UUID] = None


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of health check operation."""

    endpoint_id: UUID
    route_sync_status: SyncStatus
    readiness_status: ReadinessStatus
    healthy_replicas: list[UUID]
    unhealthy_replicas: list[UUID]
    timestamp: datetime
    details: dict[str, str] = None
