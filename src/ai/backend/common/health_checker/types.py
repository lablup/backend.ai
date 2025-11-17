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

# Built-in component IDs for database
CID_POSTGRES: ComponentId = ComponentId("postgres")

# Built-in component IDs for Redis/Valkey
CID_REDIS_ARTIFACT: ComponentId = ComponentId("artifact")
CID_REDIS_CONTAINER_LOG: ComponentId = ComponentId("container_log")
CID_REDIS_LIVE: ComponentId = ComponentId("live")
CID_REDIS_STAT: ComponentId = ComponentId("stat")
CID_REDIS_IMAGE: ComponentId = ComponentId("image")
CID_REDIS_STREAM: ComponentId = ComponentId("stream")
CID_REDIS_SCHEDULE: ComponentId = ComponentId("schedule")
CID_REDIS_BGTASK: ComponentId = ComponentId("bgtask")
CID_REDIS_SESSION: ComponentId = ComponentId("session")
CID_REDIS_CORE_LIVE: ComponentId = ComponentId("core_live")

# Built-in component IDs for etcd
CID_ETCD: ComponentId = ComponentId("etcd")

# Built-in component IDs for container
CID_DOCKER: ComponentId = ComponentId("docker")


@dataclass(frozen=True)
class HealthCheckKey:
    """
    Unique key to identify a health checker registration.

    Uses frozen dataclass to be hashable and usable as dict key.
    """

    service_group: ServiceGroup
    component_id: ComponentId


@dataclass
class ComponentHealthStatus:
    """
    Health status for a single component.

    Represents the result of checking one component within a service group.
    """

    is_healthy: bool
    last_checked_at: datetime
    error_message: Optional[str] = None


@dataclass
class ServiceHealth:
    """
    Health status of a service group containing multiple components.

    A service health checker checks multiple components and returns
    their individual statuses aggregated in this structure.
    """

    results: dict[ComponentId, ComponentHealthStatus]


@dataclass
class AllServicesHealth:
    """
    Aggregated health status of all service groups.

    Contains health results from all registered service health checkers.
    """

    results: dict[ServiceGroup, ServiceHealth]
