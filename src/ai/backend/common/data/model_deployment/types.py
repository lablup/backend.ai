from typing import Any, Self, override

from ai.backend.common.types import CIStrEnum


class ReadinessStatus(CIStrEnum):
    NOT_CHECKED = "NOT_CHECKED"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"


class LivenessStatus(CIStrEnum):
    NOT_CHECKED = "NOT_CHECKED"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DEGRADED = "DEGRADED"


class ActivenessStatus(CIStrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


# Map ``EndpointLifecycle`` (legacy lifecycle column form) values onto the
# corresponding v2 :class:`ModelDeploymentStatus`. Read by ``_missing_`` to
# resolve historical ``deployment_history`` rows where the writer stored
# :class:`EndpointLifecycle` values instead of v2 status names.
_LIFECYCLE_TO_DEPLOYMENT_STATUS_ALIASES: dict[str, str] = {
    "destroying": "STOPPING",
    "destroyed": "STOPPED",
    "created": "PENDING",  # never-deployed initial state
}


class ModelDeploymentStatus(CIStrEnum):
    PENDING = "PENDING"
    SCALING = "SCALING"
    DEPLOYING = "DEPLOYING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"

    @classmethod
    @override
    def _missing_(cls, value: Any) -> Self | None:
        if isinstance(value, str):
            alias = _LIFECYCLE_TO_DEPLOYMENT_STATUS_ALIASES.get(value.lower())
            if alias is not None:
                return cls(alias)
        return super()._missing_(value)


class DeploymentStrategy(CIStrEnum):
    ROLLING = "ROLLING"
    BLUE_GREEN = "BLUE_GREEN"


class RouteStatus(CIStrEnum):
    """Lifecycle status of a route in the deployment."""

    PROVISIONING = "provisioning"
    RUNNING = "running"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED_TO_START = "failed_to_start"


class RouteHealthStatus(CIStrEnum):
    """Health check status of a route."""

    NOT_CHECKED = "not_checked"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class RouteTrafficStatus(CIStrEnum):
    """Traffic routing status for a route.

    Controls whether traffic should be sent to this route.
    Actual traffic delivery depends on health being HEALTHY.

    - ACTIVE: Traffic enabled (will receive traffic when health is HEALTHY)
    - INACTIVE: Traffic disabled (will not receive traffic regardless of health)
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
