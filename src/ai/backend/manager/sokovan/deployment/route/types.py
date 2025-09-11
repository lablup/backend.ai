"""Types for route lifecycle management."""

from dataclasses import dataclass, field
from enum import StrEnum

from ai.backend.manager.repositories.deployment.types import RouteData


class RouteLifecycleType(StrEnum):
    """Types of route lifecycle operations."""

    PROVISIONING = "provisioning"
    RUNNING = "running"
    HEALTH_CHECK = "health_check"
    TERMINATING = "terminating"


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
