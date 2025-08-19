"""Types for health monitoring."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..types import ReadinessStatus, SyncStatus


@dataclass(frozen=True)
class HealthStatus:
    """Health status of an endpoint."""

    endpoint_id: UUID
    route_sync_status: SyncStatus
    readiness_status: ReadinessStatus
    healthy_replicas: list[UUID]
    unhealthy_replicas: list[UUID]
    timestamp: datetime
    details: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class SyncCheckResult:
    """Result of route-session synchronization check."""

    endpoint_id: UUID
    synced_routes: list[UUID]
    out_of_sync_routes: list[UUID]
    orphaned_routes: list[UUID]  # Routes without sessions
    orphaned_sessions: list[UUID]  # Sessions without routes
    timestamp: datetime


@dataclass(frozen=True)
class ReadinessCheckResult:
    """Result of readiness check via appproxy."""

    endpoint_id: UUID
    ready_replicas: list[UUID]
    not_ready_replicas: list[UUID]
    unknown_replicas: list[UUID]
    timestamp: datetime
    check_details: Optional[dict[UUID, str]] = None
