from enum import StrEnum


class ReadinessStatus(StrEnum):
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"


class ModelDeploymentStatus(StrEnum):
    CREATED = "CREATED"
    DEPLOYING = "DEPLOYING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class DeploymentStrategy(StrEnum):
    ROLLING = "ROLLING"
    BLUE_GREEN = "BLUE_GREEN"


class DeploymentExecutionStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"
