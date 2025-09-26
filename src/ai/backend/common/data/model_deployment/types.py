from enum import StrEnum


class ReadinessStatus(StrEnum):
    NOT_CHECKED = "NOT_CHECKED"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"


class LivenessStatus(StrEnum):
    NOT_CHECKED = "NOT_CHECKED"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DEGRADED = "DEGRADED"


class ActivenessStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ModelDeploymentStatus(StrEnum):
    PENDING = "PENDING"
    SCALING = "SCALING"
    DEPLOYING = "DEPLOYING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class DeploymentStrategy(StrEnum):
    ROLLING = "ROLLING"
    BLUE_GREEN = "BLUE_GREEN"
