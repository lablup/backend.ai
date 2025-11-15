from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from ai.backend.common.dependencies import (
    DependencyComposer,
    DependencyProvider,
    DependencyStack,
    NonMonitorableDependencyProvider,
)


class TestDependencyProviderInterface:
    """

    Test that DependencyProvider enforces its abstract interface.
    """

    def test_cannot_instantiate_abstract_provider(self) -> None:
        """

        DependencyProvider should not be instantiable directly.
        """
        with pytest.raises(TypeError):
            DependencyProvider()  # type: ignore[abstract]


class TestDependencyComposerInterface:
    """

    Test that DependencyComposer enforces its abstract interface.
    """

    def test_cannot_instantiate_abstract_composer(self) -> None:
        """

        DependencyComposer should not be instantiable directly.
        """
        with pytest.raises(TypeError):
            DependencyComposer()  # type: ignore[abstract]


class TestDependencyStackInterface:
    """

    Test that DependencyStack enforces its abstract interface.
    """

    def test_cannot_instantiate_abstract_stack(self) -> None:
        """

        DependencyStack should not be instantiable directly.
        """
        with pytest.raises(TypeError):
            DependencyStack()  # type: ignore[abstract]


class SimpleDependencyProvider(NonMonitorableDependencyProvider[str, str]):
    """

    Simple concrete provider for testing.
    """

    @property
    def stage_name(self) -> str:
        """

        Get the stage name.
        """
        return "simple"

    @asynccontextmanager
    async def provide(self, setup_input: str) -> AsyncIterator[str]:
        """

        Provide a simple resource.
        """
        yield f"resource-{setup_input}"


class TestDependencyProviderConcrete:
    """

    Test concrete DependencyProvider implementations.
    """

    @pytest.mark.asyncio
    async def test_provider_lifecycle(self) -> None:
        """

        Provider should properly enter and exit its context.
        """
        provider = SimpleDependencyProvider()
        assert provider.stage_name == "simple"

        async with provider.provide("test") as resource:
            assert resource == "resource-test"

    @pytest.mark.asyncio
    async def test_provider_cleanup_on_exception(self) -> None:
        """

        Provider should cleanup even when exception occurs.
        """

        class CleanupTracker:
            cleaned_up: bool = False

        tracker = CleanupTracker()

        class ProviderWithCleanup(NonMonitorableDependencyProvider[str, str]):
            @property
            def stage_name(self) -> str:
                return "cleanup-test"

            @asynccontextmanager
            async def provide(self, setup_input: str) -> AsyncIterator[str]:
                try:
                    yield "resource"
                finally:
                    tracker.cleaned_up = True

        provider = ProviderWithCleanup()

        with pytest.raises(RuntimeError):
            async with provider.provide("test") as resource:
                assert resource == "resource"
                raise RuntimeError("Test error")

        assert tracker.cleaned_up is True
