from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncContextManager, Generic, Optional, TypeVar, final

if TYPE_CHECKING:
    from ai.backend.common.health_checker import ServiceHealthChecker

SetupInputT = TypeVar("SetupInputT")
ResourceT = TypeVar("ResourceT")
ResourcesT = TypeVar("ResourcesT")


class DependencyProvider(ABC, Generic[SetupInputT, ResourceT]):
    """Base class for all dependency providers.

    Dependency providers are stateless objects that provide async context managers
    for managing the lifecycle of dependencies (setup and cleanup).

    Type Parameters:
        SetupInputT: Type of input required for dependency setup
        ResourceT: Type of resource/dependency provided
    """

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Get the stage name for this dependency provider.

        Returns:
            The stage name used for tracking and identification
        """
        raise NotImplementedError

    @abstractmethod
    def provide(self, setup_input: SetupInputT) -> AsyncContextManager[ResourceT]:
        """Return an async context manager for the dependency.

        Args:
            setup_input: Input required for dependency setup

        Returns:
            An async context manager that yields the initialized dependency
        """
        raise NotImplementedError

    @abstractmethod
    def gen_health_checkers(self, resource: ResourceT) -> Optional[ServiceHealthChecker]:
        """
        Return a health checker for the provided resource.

        Override this method to provide health checking capability for this dependency.
        The health checker will be automatically collected by DependencyBuilderStack
        and registered using checker.target_service_group as the key.

        Args:
            resource: The initialized resource from provide()

        Returns:
            ServiceHealthChecker instance or None if no health checking is needed
        """
        raise NotImplementedError


class NonMonitorableDependencyProvider(DependencyProvider[SetupInputT, ResourceT]):
    """
    Base class for dependency providers that do not require health monitoring.

    This class provides a default implementation of gen_health_checkers()
    that returns None, indicating no health checks are needed.
    """

    @final
    def gen_health_checkers(self, resource: ResourceT) -> None:
        """
        Return None as this dependency does not require health monitoring.

        Args:
            resource: The initialized resource from provide()

        Returns:
            None indicating no health checks
        """
        return None


class DependencyComposer(ABC, Generic[SetupInputT, ResourcesT]):
    """Abstract base for dependency composers.

    Composers compose multiple dependency providers into a larger unit,
    orchestrating their initialization in a specific order.
    """

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Get the stage name for this dependency composer.

        Returns:
            The stage name used for tracking and identification
        """
        raise NotImplementedError

    @abstractmethod
    def compose(
        self,
        stack: DependencyStack,
        setup_input: SetupInputT,
    ) -> AsyncContextManager[ResourcesT]:
        """Compose multiple dependencies using the provided stack.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Input required for composition

        Returns:
            An async context manager that yields the composed resources

        Raises:
            Any exception raised during composition
        """
        raise NotImplementedError


class DependencyStack(ABC):
    """Abstract base for dependency stack management.

    Provides lifecycle management and tracking for dependencies during setup.
    Supports both individual dependency providers and aggregators that compose
    multiple dependencies.
    """

    @abstractmethod
    async def enter_dependency(
        self,
        provider: DependencyProvider[SetupInputT, ResourceT],
        setup_input: SetupInputT,
    ) -> ResourceT:
        """Execute a single dependency provider and register for cleanup.

        Args:
            provider: The dependency provider to execute
            setup_input: Input required for the provider

        Returns:
            The resource created by the provider

        Raises:
            Any exception raised by the provider
        """
        raise NotImplementedError

    @abstractmethod
    async def enter_composer(
        self,
        composer: DependencyComposer[SetupInputT, ResourcesT],
        setup_input: SetupInputT,
    ) -> ResourcesT:
        """Execute a dependency composer and register for cleanup.

        Args:
            composer: The dependency composer to execute
            setup_input: Input required for the composer

        Returns:
            The resources created by the composer

        Raises:
            Any exception raised by the composer
        """
        raise NotImplementedError
