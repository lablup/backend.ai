"""Types for route lifecycle management."""

from dataclasses import dataclass, field
from enum import StrEnum

from ai.backend.manager.repositories.deployment.types import RouteData


class RouteLifecycleType(StrEnum):
    """Types of route lifecycle operations."""

    PROVISIONING = "provisioning"
    RUNNING = "running"
    HEALTH_CHECK = "health_check"
    ROUTE_EVICTION = "route_eviction"
    TERMINATING = "terminating"
    SERVICE_DISCOVERY_SYNC = "service_discovery_sync"


@dataclass
class RouteExecutionError:
    """Error information for failed route operations."""

    route_info: RouteData
    reason: str
    error_detail: str


@dataclass
class RouteExecutionResult:
    """Result of a route execution operation."""

    successes: list[RouteData] = field(default_factory=list)
    errors: list[RouteExecutionError] = field(default_factory=list)
    stale: list[RouteData] = field(default_factory=list)
