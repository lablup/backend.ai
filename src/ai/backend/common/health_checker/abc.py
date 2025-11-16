from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.common.health_checker.types import HealthCheckResult, ServiceGroup


class HealthChecker(ABC):
    """
    Abstract base class for health checking components.

    Each HealthChecker is responsible for checking all components within a specific
    ServiceGroup (e.g., REDIS, DATABASE, ETCD). A single checker can verify multiple
    components and return their individual health statuses.

    Subclasses must implement:
    - target_service_group: Which service group this checker is responsible for
    - check_health: Check all components and return their statuses
    - timeout: Timeout for the entire check operation
    """

    @property
    @abstractmethod
    def target_service_group(self) -> ServiceGroup:
        """
        The service group this health checker is responsible for.

        Returns:
            The ServiceGroup this checker monitors (e.g., REDIS, DATABASE, ETCD)
        """
        raise NotImplementedError

    @abstractmethod
    async def check_health(self) -> HealthCheckResult:
        """
        Check the health of all components in this service group.

        Returns:
            HealthCheckResult containing status for each component along with metadata
            (e.g., latency, endpoint information)

        Raises:
            HealthCheckError: When the check itself fails catastrophically.
                Individual component failures should be reflected in the
                HealthCheckResult.results dict, not raised as exceptions.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float:
        """
        The timeout for the entire health check operation in seconds.

        Returns:
            The check timeout in seconds
        """
        raise NotImplementedError
