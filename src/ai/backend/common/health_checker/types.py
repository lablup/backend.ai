from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import NewType, Optional


class ServiceGroup(enum.StrEnum):
    """
    Represents the service group category for health checks.

    Each Backend.AI component can check health of various services
    it depends on (database, Redis, etcd, etc.).
    """

    MANAGER = "manager"
    AGENT = "agent"
    DATABASE = "database"
    REDIS = "redis"
    ETCD = "etcd"
    HTTP = "http"


# Component ID is a string identifier with type safety
# For services like database, redis, etcd: use service name (e.g., "postgres", "redis")
# For servers: use server-specific identifier
ComponentId = NewType("ComponentId", str)


@dataclass(frozen=True)
class HealthCheckKey:
    """
    Unique key to identify a health checker registration.

    Uses frozen dataclass to be hashable and usable as dict key.
    """

    service_group: ServiceGroup
    component_id: ComponentId


@dataclass
class HealthCheckStatus:
    """
    Internal representation of health check status stored in memory.

    This is used internally by the registry and probe to track
    the current health status of each component.
    """

    is_healthy: bool
    last_checked_at: datetime
    error_message: Optional[str] = None
