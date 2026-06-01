from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, TypeVar, final

if TYPE_CHECKING:
    from ai.backend.common.health_checker import ServiceHealthChecker

SetupInputT = TypeVar("SetupInputT")
ResourceT = TypeVar("ResourceT")
ResourcesT = TypeVar("ResourcesT")


class DependencyProvider[SetupInputT, ResourceT](ABC):
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
    def provide(self, setup_input: SetupInputT) -> AbstractAsyncContextManager[ResourceT]:
        """Return an async context manager for the dependency.

        Args:
            setup_input: Input required for dependency setup

        Returns:
            An async context manager that yields the initialized dependency
        """
        raise NotImplementedError

    def gen_liveness_checker(self, resource: ResourceT) -> ServiceHealthChecker | None:
        """
        Return a liveness health checker for the provided resource.

        Override this method when the dependency should contribute to the liveness
        probe — typically connection-stuck issues where a process restart is the
        actual recovery path (e.g., Etcd, Valkey, Docker daemon).

        Args:
            resource: The initialized resource from provide()

        Returns:
            ServiceHealthChecker instance or None if this dependency does not
            contribute to liveness checks.
        """
        return None

    def gen_readiness_checker(self, resource: ResourceT) -> ServiceHealthChecker | None:
        """
        Return a readiness health checker for the provided resource.

        Override this method when the dependency should contribute to the readiness
        probe only — failure should drain traffic but no process restart is needed
        (e.g., database connections).

        Args:
            resource: The initialized resource from provide()

        Returns:
            ServiceHealthChecker instance or None if this dependency does not
            contribute to readiness checks.
        """
        return None


class NonMonitorableDependencyProvider(DependencyProvider[SetupInputT, ResourceT]):
    """
    Base class for dependency providers that do not require health monitoring.

    Both liveness and readiness checkers are pinned to None.
    """

    @final
    def gen_liveness_checker(self, resource: ResourceT) -> None:
        return None

    @final
    def gen_readiness_checker(self, resource: ResourceT) -> None:
        return None


class DependencyComposer[SetupInputT, ResourcesT](ABC):
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
    ) -> AbstractAsyncContextManager[ResourcesT]:
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
