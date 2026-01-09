from __future__ import annotations

from abc import ABC, abstractmethod

from .types import ComponentHealthStatus, ComponentId, ServiceGroup, ServiceHealth


class ComponentHealthChecker(ABC):
    """
    Abstract base class for individual component health checkers.

    Each component health checker monitors a single component and reports
    its health status. These are used by ServiceHealthChecker implementations
    to check individual components within a service group.
    """

    @property
    @abstractmethod
    def component_id(self) -> ComponentId:
        """
        The component identifier this checker monitors.

        Returns:
            ComponentId for this specific component
        """
        raise NotImplementedError

    @abstractmethod
    async def check_component(self) -> ComponentHealthStatus:
        """
        Perform a health check on this component.

        Returns:
            ComponentHealthStatus containing the health status of this component
        """
        raise NotImplementedError


class ServiceHealthChecker(ABC):
    """
    Abstract base class for service group health checkers.

    Each service health checker monitors a specific service group (e.g., REDIS, DATABASE, ETCD)
    and checks the health of all components within that group.

    Subclasses must implement:
    - target_service_group: Which service group this checker is responsible for
    - check_service: Check all components and return their statuses
    - timeout: Timeout for the entire check operation
    """

    @property
    @abstractmethod
    def target_service_group(self) -> ServiceGroup:
        """
        The service group this checker monitors.

        Returns:
            ServiceGroup identifier (e.g., REDIS, DATABASE, ETCD)
        """
        raise NotImplementedError

    @abstractmethod
    async def check_service(self) -> ServiceHealth:
        """
        Perform a health check on all components in the service group.

        Returns:
            ServiceHealth containing status for each component in the service group

        Raises:
            HealthCheckError: When the check itself fails catastrophically.
                Individual component failures should be reflected in the
                ServiceHealth.results dict, not raised as exceptions.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float:
        """
        The timeout for the health check in seconds.

        This is used by the probe to enforce a maximum check duration
        for the entire service group check.
        """
        raise NotImplementedError


class StaticServiceHealthChecker(ServiceHealthChecker):
    """
    Base class for static service health checkers.

    Static services have a fixed set of components that are determined
    at initialization time (e.g., Redis clients, Database connections).
    Components cannot be added or removed after initialization.
    """

    pass


class DynamicServiceHealthChecker(ServiceHealthChecker):
    """
    Base class for dynamic service health checkers.

    Dynamic services have components that can be added or removed at runtime
    (e.g., Agents joining/leaving the cluster). Provides methods to manage
    the set of component health checkers.
    """

    @abstractmethod
    def register_component(self, checker: ComponentHealthChecker) -> None:
        """
        Register a component health checker.

        Args:
            checker: The component health checker to register
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_component(self, component_id: ComponentId) -> None:
        """
        Unregister a component health checker.

        Args:
            component_id: The component identifier to unregister
        """
        raise NotImplementedError
