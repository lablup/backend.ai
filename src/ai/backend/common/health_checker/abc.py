from __future__ import annotations

from abc import ABC, abstractmethod


class HealthChecker(ABC):
    """
    Abstract base class for health checking components.

    Implementations should check the health of a specific component or service
    (e.g., database, Redis, etcd, HTTP endpoints) and raise appropriate
    HealthCheckError subclasses when unhealthy.

    Subclasses must also define a timeout property.
    """

    @abstractmethod
    async def check_health(self) -> None:
        """
        Check if the component is healthy.

        This method should complete normally if the component is healthy.
        If the component is unhealthy, it should raise a specific HealthCheckError
        subclass defined by the implementation.

        Raises:
            HealthCheckError: Each implementation must define and raise its own
                specific error type (e.g., DatabaseHealthCheckError,
                RedisHealthCheckError, EtcdHealthCheckError, HttpHealthCheckError).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float:
        """
        The timeout for each health check in seconds.

        Returns:
            The check timeout in seconds
        """
        raise NotImplementedError
