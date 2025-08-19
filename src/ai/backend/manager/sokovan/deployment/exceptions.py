"""Exceptions for deployment package."""

from ai.backend.common.exception import BackendAIError


class DeploymentError(BackendAIError):
    """Base exception for deployment operations."""

    pass


class EndpointNotFound(DeploymentError):
    """Raised when endpoint is not found."""

    pass


class EndpointAlreadyExists(DeploymentError):
    """Raised when trying to create an endpoint that already exists."""

    pass


class InvalidReplicaCount(DeploymentError):
    """Raised when replica count is invalid."""

    pass


class ScalingError(DeploymentError):
    """Raised when scaling operation fails."""

    pass


class ReplicaCreationError(DeploymentError):
    """Raised when replica creation fails."""

    pass


class HealthCheckError(DeploymentError):
    """Raised when health check fails."""

    pass


class NetworkConfigurationError(DeploymentError):
    """Raised when network configuration fails."""

    pass


class ResourceLimitExceeded(DeploymentError):
    """Raised when resource limits are exceeded."""

    pass
