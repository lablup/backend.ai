from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import NewType, Optional

# Service group is a string identifier with type safety
# Allows components to define their own service groups while maintaining type safety
ServiceGroup = NewType("ServiceGroup", str)

# Built-in service groups
MANAGER: ServiceGroup = ServiceGroup("manager")
AGENT: ServiceGroup = ServiceGroup("agent")
STORAGE_PROXY: ServiceGroup = ServiceGroup("storage-proxy")
APPPROXY: ServiceGroup = ServiceGroup("appproxy")
DATABASE: ServiceGroup = ServiceGroup("database")
ETCD: ServiceGroup = ServiceGroup("etcd")
REDIS: ServiceGroup = ServiceGroup("redis")
API: ServiceGroup = ServiceGroup("api")
CONTAINER: ServiceGroup = ServiceGroup("container")

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
