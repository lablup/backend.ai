from __future__ import annotations

from contextlib import AsyncExitStack

from ..base import (
    DependencyComposer,
    DependencyProvider,
    DependencyStack,
    ResourcesT,
    ResourceT,
    SetupInputT,
)


class AsyncExitDependencyStack(DependencyStack):
    """Basic DependencyStack implementation using AsyncExitStack.

    Provides simple lifecycle management without additional tracking or logging.
    """

    _stack: AsyncExitStack

    def __init__(self) -> None:
        self._stack = AsyncExitStack()

    async def enter_dependency(
        self,
        provider: DependencyProvider[SetupInputT, ResourceT],
        setup_input: SetupInputT,
    ) -> ResourceT:
        """Execute a dependency provider using AsyncExitStack."""
        return await self._stack.enter_async_context(provider.provide(setup_input))

    async def enter_composer(
        self,
        composer: DependencyComposer[SetupInputT, ResourcesT],
        setup_input: SetupInputT,
    ) -> ResourcesT:
        """Execute a dependency composer with a new nested stack."""
        nested_stack = AsyncExitDependencyStack()
        await self._stack.enter_async_context(nested_stack)
        return await nested_stack._stack.enter_async_context(
            composer.compose(nested_stack, setup_input)
        )

    async def __aenter__(self) -> AsyncExitDependencyStack:
        """Enter the async context."""
        await self._stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Exit the async context and cleanup resources in LIFO order."""
        return await self._stack.__aexit__(exc_type, exc_val, exc_tb)
