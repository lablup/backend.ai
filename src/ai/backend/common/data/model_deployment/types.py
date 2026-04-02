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


class ModelDeploymentStatus(CIStrEnum):
    PENDING = "PENDING"
    SCALING = "SCALING"
    DEPLOYING = "DEPLOYING"
    READY = "READY"
    DESTROYING = "DESTROYING"
    DESTROYED = "DESTROYED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


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
