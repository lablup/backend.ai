from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.dependencies import DependencyComposer, DependencyProvider, DependencyStack
from ai.backend.common.dependencies.stacks.asyncexit import AsyncExitDependencyStack


class SimpleDependencyProvider(DependencyProvider[Any, str]):
    """

    Simple dependency provider for testing.
    """

    def __init__(
        self, stage_name: str, cleanup_tracker: list[str], raise_on_enter: bool = False
    ) -> None:
        self._stage_name = stage_name
        self._cleanup_tracker = cleanup_tracker
        self._raise_on_enter = raise_on_enter

    @property
    def stage_name(self) -> str:
        """

        Get the stage name.
        """
        return self._stage_name

    @asynccontextmanager
    async def provide(self, setup_input: Any) -> AsyncIterator[str]:
        """

        Provide a resource.
        """
        if self._raise_on_enter:
            raise RuntimeError(f"Simulated error in {self._stage_name}")
        try:
            yield f"resource:{self._stage_name}"
        finally:
            self._cleanup_tracker.append(self._stage_name)


class TestAsyncExitDependencyStack:
    """

    Test AsyncExitDependencyStack implementation.
    """

    @pytest.mark.asyncio
    async def test_single_dependency_lifecycle(self) -> None:
        """

        Stack should properly manage single dependency lifecycle.
        """
        cleanup_tracker: list[str] = []
        provider = SimpleDependencyProvider("test-dep", cleanup_tracker)

        async with AsyncExitDependencyStack() as stack:
            resource = await stack.enter_dependency(provider, "input")
            assert resource == "resource:test-dep"
            assert cleanup_tracker == []

        # After stack exits, cleanup should have occurred
        assert cleanup_tracker == ["test-dep"]

    @pytest.mark.asyncio
    async def test_multiple_dependencies_lifo_cleanup(self) -> None:
        """

        Stack should cleanup multiple dependencies in LIFO order.
        """
        cleanup_tracker: list[str] = []
        provider1 = SimpleDependencyProvider("dep1", cleanup_tracker)
        provider2 = SimpleDependencyProvider("dep2", cleanup_tracker)
        provider3 = SimpleDependencyProvider("dep3", cleanup_tracker)

        async with AsyncExitDependencyStack() as stack:
            await stack.enter_dependency(provider1, "input")
            await stack.enter_dependency(provider2, "input")
            await stack.enter_dependency(provider3, "input")

        # Cleanup should occur in reverse order
        assert cleanup_tracker == ["dep3", "dep2", "dep1"]

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(self) -> None:
        """

        Stack should cleanup successfully entered dependencies even when exception occurs.
        """
        cleanup_tracker: list[str] = []
        provider1 = SimpleDependencyProvider("dep1", cleanup_tracker)
        provider2 = SimpleDependencyProvider("dep2", cleanup_tracker, raise_on_enter=True)

        with pytest.raises(RuntimeError, match="Simulated error in dep2"):
            async with AsyncExitDependencyStack() as stack:
                await stack.enter_dependency(provider1, "input")
                await stack.enter_dependency(provider2, "input")

        # dep1 should be cleaned up even though dep2 failed
        assert cleanup_tracker == ["dep1"]

    @pytest.mark.asyncio
    async def test_nested_composer(self) -> None:
        """

        Stack should support nested composers with proper cleanup.
        """
        cleanup_tracker: list[str] = []

        @dataclass
        class ComposerResources:
            resource1: str
            resource2: str

        class TestComposer(DependencyComposer[str, ComposerResources]):
            @property
            def stage_name(self) -> str:
                return "test-composer"

            @asynccontextmanager
            async def compose(
                self, stack: DependencyStack, setup_input: str
            ) -> AsyncIterator[ComposerResources]:
                provider1 = SimpleDependencyProvider("composer-dep1", cleanup_tracker)
                provider2 = SimpleDependencyProvider("composer-dep2", cleanup_tracker)

                res1 = await stack.enter_dependency(provider1, setup_input)
                res2 = await stack.enter_dependency(provider2, setup_input)

                yield ComposerResources(resource1=res1, resource2=res2)

        async with AsyncExitDependencyStack() as stack:
            composer = TestComposer()
            resources = await stack.enter_composer(composer, "input")
            assert resources.resource1 == "resource:composer-dep1"
            assert resources.resource2 == "resource:composer-dep2"

        # Nested dependencies should be cleaned up in LIFO order
        assert cleanup_tracker == ["composer-dep2", "composer-dep1"]

    @pytest.mark.asyncio
    async def test_multiple_composers_cleanup_order(self) -> None:
        """

        Multiple composers should cleanup in LIFO order.
        """
        cleanup_tracker: list[str] = []

        class SimpleComposer(DependencyComposer[str, str]):
            def __init__(self, name: str) -> None:
                self._name = name

            @property
            def stage_name(self) -> str:
                return self._name

            @asynccontextmanager
            async def compose(self, stack: DependencyStack, setup_input: str) -> AsyncIterator[str]:
                provider = SimpleDependencyProvider(f"{self._name}-dep", cleanup_tracker)
                resource = await stack.enter_dependency(provider, setup_input)
                yield resource

        async with AsyncExitDependencyStack() as stack:
            await stack.enter_composer(SimpleComposer("composer1"), "input")
            await stack.enter_composer(SimpleComposer("composer2"), "input")
            await stack.enter_composer(SimpleComposer("composer3"), "input")

        # Composers should cleanup in reverse order
        assert cleanup_tracker == ["composer3-dep", "composer2-dep", "composer1-dep"]

    @pytest.mark.asyncio
    async def test_exception_in_nested_composer(self) -> None:
        """

        Exception in nested composer should cleanup successfully entered dependencies.
        """
        cleanup_tracker: list[str] = []

        class FailingComposer(DependencyComposer[str, str]):
            @property
            def stage_name(self) -> str:
                return "failing-composer"

            @asynccontextmanager
            async def compose(self, stack: DependencyStack, setup_input: str) -> AsyncIterator[str]:
                provider1 = SimpleDependencyProvider("failing-dep1", cleanup_tracker)
                provider2 = SimpleDependencyProvider(
                    "failing-dep2", cleanup_tracker, raise_on_enter=True
                )

                await stack.enter_dependency(provider1, setup_input)
                await stack.enter_dependency(provider2, setup_input)  # This will fail
                yield "should-not-reach"

        with pytest.raises(RuntimeError, match="Simulated error in failing-dep2"):
            async with AsyncExitDependencyStack() as stack:
                await stack.enter_composer(FailingComposer(), "input")

        # failing-dep1 should be cleaned up
        assert cleanup_tracker == ["failing-dep1"]
