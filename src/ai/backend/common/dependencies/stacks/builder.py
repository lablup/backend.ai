from __future__ import annotations

from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Any

from ai.backend.common.dependencies.base import DependencyStack

if TYPE_CHECKING:
    from ai.backend.common.dependencies.base import (
        DependencyComposer,
        DependencyProvider,
        ResourcesT,
        ResourceT,
        SetupInputT,
    )
    from ai.backend.common.health_checker import ServiceHealthChecker
    from ai.backend.common.health_checker.types import ServiceGroup


class DependencyBuilderStack(DependencyStack):
    """
    DependencyStack that collects health checkers from providers.

    Uses AsyncExitStack internally for lifecycle management while collecting
    liveness/readiness health checkers from each provider. Each ServiceGroup
    can have only one checker per kind.
    """

    _stack: AsyncExitStack
    _liveness_checkers: dict[ServiceGroup, ServiceHealthChecker]
    _readiness_checkers: dict[ServiceGroup, ServiceHealthChecker]

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._liveness_checkers = {}
        self._readiness_checkers = {}

    async def enter_dependency(
        self,
        provider: DependencyProvider[SetupInputT, ResourceT],
        setup_input: SetupInputT,
    ) -> ResourceT:
        """
        Execute a dependency provider and collect its liveness/readiness checkers.
        """
        resource = await self._stack.enter_async_context(provider.provide(setup_input))

        liveness = provider.gen_liveness_checker(resource)
        if liveness is not None:
            self._liveness_checkers[liveness.target_service_group] = liveness

        readiness = provider.gen_readiness_checker(resource)
        if readiness is not None:
            self._readiness_checkers[readiness.target_service_group] = readiness

        return resource

    async def enter_composer(
        self,
        composer: DependencyComposer[SetupInputT, ResourcesT],
        setup_input: SetupInputT,
    ) -> ResourcesT:
        """
        Execute a dependency composer and merge collected checkers from nested deps.
        """
        nested_stack = DependencyBuilderStack()
        await self._stack.enter_async_context(nested_stack)

        resources = await nested_stack._stack.enter_async_context(
            composer.compose(nested_stack, setup_input)
        )

        for service_group, checker in nested_stack._liveness_checkers.items():
            self._liveness_checkers[service_group] = checker
        for service_group, checker in nested_stack._readiness_checkers.items():
            self._readiness_checkers[service_group] = checker

        return resources

    def get_liveness_checkers(self) -> dict[ServiceGroup, ServiceHealthChecker]:
        """Return collected liveness checkers."""
        return self._liveness_checkers.copy()

    def get_readiness_checkers(self) -> dict[ServiceGroup, ServiceHealthChecker]:
        """Return collected readiness checkers."""
        return self._readiness_checkers.copy()

    async def __aenter__(self) -> DependencyBuilderStack:
        await self._stack.__aenter__()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> bool | None:
        return await self._stack.__aexit__(exc_type, exc_val, exc_tb)
