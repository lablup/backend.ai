from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import pytest
from conftest import DependencyLifecycleTracker, MockDependencyProvider

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.dependencies.stacks.asyncexit import AsyncExitDependencyStack


class TestAsyncExitDependencyStack:
    """

    Test AsyncExitDependencyStack implementation.
    """

    @pytest.mark.asyncio
    async def test_single_dependency_lifecycle(
        self, lifecycle_tracker: DependencyLifecycleTracker
    ) -> None:
        """

        Stack should properly manage single dependency lifecycle.
        """
        provider = MockDependencyProvider("test-dep", lifecycle_tracker)

        async with AsyncExitDependencyStack() as stack:
            resource = await stack.enter_dependency(provider, "input")
            assert resource == "resource:test-dep"
            assert lifecycle_tracker.events == ["enter:test-dep"]

        # After stack exits, cleanup should have occurred
        assert lifecycle_tracker.events == ["enter:test-dep", "exit:test-dep"]

    @pytest.mark.asyncio
    async def test_multiple_dependencies_lifo_cleanup(
        self, lifecycle_tracker: DependencyLifecycleTracker
    ) -> None:
        """

        Stack should cleanup multiple dependencies in LIFO order.
        """
        provider1 = MockDependencyProvider("dep1", lifecycle_tracker)
        provider2 = MockDependencyProvider("dep2", lifecycle_tracker)
        provider3 = MockDependencyProvider("dep3", lifecycle_tracker)

        async with AsyncExitDependencyStack() as stack:
            await stack.enter_dependency(provider1, "input")
            await stack.enter_dependency(provider2, "input")
            await stack.enter_dependency(provider3, "input")

        # Cleanup should occur in reverse order
        cleanup_order = lifecycle_tracker.get_cleanup_order()
        assert cleanup_order == ["dep3", "dep2", "dep1"]

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self, lifecycle_tracker: DependencyLifecycleTracker
    ) -> None:
        """

        Stack should cleanup successfully entered dependencies even when exception occurs.
        """
        provider1 = MockDependencyProvider("dep1", lifecycle_tracker)
        provider2 = MockDependencyProvider("dep2", lifecycle_tracker, raise_on_enter=True)

        with pytest.raises(RuntimeError, match="Simulated error in dep2"):
            async with AsyncExitDependencyStack() as stack:
                await stack.enter_dependency(provider1, "input")
                await stack.enter_dependency(provider2, "input")

        # dep1 should be cleaned up even though dep2 failed
        assert "exit:dep1" in lifecycle_tracker.events
        assert "exit:dep2" not in lifecycle_tracker.events

    @pytest.mark.asyncio
    async def test_nested_composer(self, lifecycle_tracker: DependencyLifecycleTracker) -> None:
        """

        Stack should support nested composers with proper cleanup.
        """

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
                provider1 = MockDependencyProvider("composer-dep1", lifecycle_tracker)
                provider2 = MockDependencyProvider("composer-dep2", lifecycle_tracker)

                res1 = await stack.enter_dependency(provider1, setup_input)
                res2 = await stack.enter_dependency(provider2, setup_input)

                yield ComposerResources(resource1=res1, resource2=res2)

        async with AsyncExitDependencyStack() as stack:
            composer = TestComposer()
            resources = await stack.enter_composer(composer, "input")
            assert resources.resource1 == "resource:composer-dep1"
            assert resources.resource2 == "resource:composer-dep2"

        # Nested dependencies should be cleaned up in LIFO order
        cleanup_order = lifecycle_tracker.get_cleanup_order()
        assert cleanup_order == ["composer-dep2", "composer-dep1"]

    @pytest.mark.asyncio
    async def test_multiple_composers_cleanup_order(
        self, lifecycle_tracker: DependencyLifecycleTracker
    ) -> None:
        """

        Multiple composers should cleanup in LIFO order.
        """

        class SimpleComposer(DependencyComposer[str, str]):
            def __init__(self, name: str) -> None:
                self._name = name

            @property
            def stage_name(self) -> str:
                return self._name

            @asynccontextmanager
            async def compose(self, stack: DependencyStack, setup_input: str) -> AsyncIterator[str]:
                provider = MockDependencyProvider(f"{self._name}-dep", lifecycle_tracker)
                resource = await stack.enter_dependency(provider, setup_input)
                yield resource

        async with AsyncExitDependencyStack() as stack:
            await stack.enter_composer(SimpleComposer("composer1"), "input")
            await stack.enter_composer(SimpleComposer("composer2"), "input")
            await stack.enter_composer(SimpleComposer("composer3"), "input")

        # Composers should cleanup in reverse order
        cleanup_order = lifecycle_tracker.get_cleanup_order()
        assert cleanup_order == ["composer3-dep", "composer2-dep", "composer1-dep"]

    @pytest.mark.asyncio
    async def test_exception_in_nested_composer(
        self, lifecycle_tracker: DependencyLifecycleTracker
    ) -> None:
        """

        Exception in nested composer should cleanup successfully entered dependencies.
        """

        class FailingComposer(DependencyComposer[str, str]):
            @property
            def stage_name(self) -> str:
                return "failing-composer"

            @asynccontextmanager
            async def compose(self, stack: DependencyStack, setup_input: str) -> AsyncIterator[str]:
                provider1 = MockDependencyProvider("failing-dep1", lifecycle_tracker)
                provider2 = MockDependencyProvider(
                    "failing-dep2", lifecycle_tracker, raise_on_enter=True
                )

                await stack.enter_dependency(provider1, setup_input)
                await stack.enter_dependency(provider2, setup_input)  # This will fail
                yield "should-not-reach"

        with pytest.raises(RuntimeError, match="Simulated error in failing-dep2"):
            async with AsyncExitDependencyStack() as stack:
                await stack.enter_composer(FailingComposer(), "input")

        # failing-dep1 should be cleaned up
        assert "exit:failing-dep1" in lifecycle_tracker.events
        assert "exit:failing-dep2" not in lifecycle_tracker.events
