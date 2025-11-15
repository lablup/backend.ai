from __future__ import annotations

from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

from ..base import DependencyStack

if TYPE_CHECKING:
    from ai.backend.common.health_checker import HealthChecker, HealthCheckKey

    from ..base import DependencyComposer, DependencyProvider, ResourcesT, ResourceT, SetupInputT


class DependencyBuilderStack(DependencyStack):
    """
    DependencyStack that collects health checkers from providers.

    Uses AsyncExitStack internally for lifecycle management while automatically
    collecting health checkers from providers that implement get_health_checker() method.

    Health checkers can be retrieved after dependency initialization
    to register them with a HealthProbe for health monitoring.
    """

    _stack: AsyncExitStack
    _health_checkers: dict[HealthCheckKey, HealthChecker]

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._health_checkers = {}

    async def enter_dependency(
        self,
        provider: DependencyProvider[SetupInputT, ResourceT],
        setup_input: SetupInputT,
    ) -> ResourceT:
        """
        Execute a dependency provider and collect health checkers.
        """
        resource = await self._stack.enter_async_context(provider.provide(setup_input))

        # Collect health checkers from provider
        registrations = provider.gen_health_checkers(resource)
        for registration in registrations:
            self._health_checkers[registration.key] = registration.checker

        return resource

    async def enter_composer(
        self,
        composer: DependencyComposer[SetupInputT, ResourcesT],
        setup_input: SetupInputT,
    ) -> ResourcesT:
        """
        Execute a dependency composer and collect health checkers from nested dependencies.

        Creates a nested DependencyBuilderStack to track dependencies
        within the composer, then merges collected health checkers.
        """
        # Create nested builder stack
        nested_stack = DependencyBuilderStack()
        await self._stack.enter_async_context(nested_stack)

        # Compose and get resources
        resources = await nested_stack._stack.enter_async_context(
            composer.compose(nested_stack, setup_input)
        )

        # Collect health checkers from nested stack
        for key, checker in nested_stack._health_checkers.items():
            self._health_checkers[key] = checker

        return resources

    def get_health_checkers(self) -> dict[HealthCheckKey, HealthChecker]:
        """
        Return collected health checkers.

        Returns:
            Dictionary mapping HealthCheckKey to HealthChecker instances
            collected from all initialized dependencies.
        """
        return self._health_checkers.copy()

    async def __aenter__(self) -> DependencyBuilderStack:
        """
        Enter the async context.
        """
        await self._stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """
        Exit the async context and cleanup resources in LIFO order.
        """
        return await self._stack.__aexit__(exc_type, exc_val, exc_tb)
