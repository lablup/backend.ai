from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from io import StringIO
from typing import Any

import pytest

from ai.backend.common.dependencies import (
    DependencyComposer,
    DependencyStack,
    NonMonitorableDependencyProvider,
)
from ai.backend.common.dependencies.stacks.visualizing import (
    DependencyStatus,
    VisualizingDependencyStack,
)


class SimpleDependencyProvider(NonMonitorableDependencyProvider[Any, str]):
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


class TestVisualizingDependencyStack:
    """
    Test VisualizingDependencyStack implementation.
    """

    @pytest.mark.asyncio
    async def test_single_dependency_visualization(self) -> None:
        """
        Stack should visualize single dependency lifecycle.
        """
        cleanup_tracker: list[str] = []
        output = StringIO()
        provider = SimpleDependencyProvider("test-dep", cleanup_tracker)

        async with VisualizingDependencyStack(output=output, show_timestamps=False) as stack:
            resource = await stack.enter_dependency(provider, "input")
            assert resource == "resource:test-dep"

        # Check output
        output_str = output.getvalue()
        assert "✓ test-dep" in output_str

        # Check events
        events = stack.get_events()
        assert len(events) == 1
        assert events[0].stage_name == "test-dep"
        assert events[0].status == DependencyStatus.COMPLETED

        # Verify cleanup
        assert cleanup_tracker == ["test-dep"]

    @pytest.mark.asyncio
    async def test_composer_visualization(self) -> None:
        """
        Stack should visualize composer with starting indicator.
        """
        cleanup_tracker: list[str] = []
        output = StringIO()

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
                provider1 = SimpleDependencyProvider("dep1", cleanup_tracker)
                provider2 = SimpleDependencyProvider("dep2", cleanup_tracker)

                res1 = await stack.enter_dependency(provider1, setup_input)
                res2 = await stack.enter_dependency(provider2, setup_input)

                yield ComposerResources(resource1=res1, resource2=res2)

        async with VisualizingDependencyStack(output=output, show_timestamps=False) as stack:
            composer = TestComposer()
            resources = await stack.enter_composer(composer, "input")
            assert resources.resource1 == "resource:dep1"
            assert resources.resource2 == "resource:dep2"

        # Check output
        output_str = output.getvalue()
        assert "▶ test-composer" in output_str
        assert "✓ dep1" in output_str
        assert "✓ dep2" in output_str

        # Check events - composer starting + 2 dependencies completed
        events = stack.get_events()
        assert len(events) == 3
        assert events[0].status == DependencyStatus.STARTING
        assert events[1].status == DependencyStatus.COMPLETED
        assert events[2].status == DependencyStatus.COMPLETED

        # Verify cleanup order (LIFO)
        assert cleanup_tracker == ["dep2", "dep1"]

    @pytest.mark.asyncio
    async def test_nested_composer_indentation(self) -> None:
        """
        Stack should properly indent nested composers.
        """
        cleanup_tracker: list[str] = []
        output = StringIO()

        class InnerComposer(DependencyComposer[str, str]):
            @property
            def stage_name(self) -> str:
                return "inner-composer"

            @asynccontextmanager
            async def compose(self, stack: DependencyStack, setup_input: str) -> AsyncIterator[str]:
                provider = SimpleDependencyProvider("inner-dep", cleanup_tracker)
                resource = await stack.enter_dependency(provider, setup_input)
                yield resource

        class OuterComposer(DependencyComposer[str, str]):
            @property
            def stage_name(self) -> str:
                return "outer-composer"

            @asynccontextmanager
            async def compose(self, stack: DependencyStack, setup_input: str) -> AsyncIterator[str]:
                inner_composer = InnerComposer()
                resource = await stack.enter_composer(inner_composer, setup_input)
                yield resource

        async with VisualizingDependencyStack(output=output, show_timestamps=False) as stack:
            await stack.enter_composer(OuterComposer(), "input")

        # Check output has proper indentation
        output_lines = output.getvalue().strip().split("\n")
        # Find lines with composers and dependencies
        outer_line = next(line for line in output_lines if "outer-composer" in line)
        inner_line = next(line for line in output_lines if "inner-composer" in line)
        dep_line = next(line for line in output_lines if "inner-dep" in line)

        # Verify indentation levels
        assert not outer_line.startswith("  ")  # No indent
        assert inner_line.startswith("  ")  # 1 level indent
        assert dep_line.startswith("    ")  # 2 level indent

    @pytest.mark.asyncio
    async def test_failure_visualization(self) -> None:
        """
        Stack should visualize failed dependencies.
        """
        cleanup_tracker: list[str] = []
        output = StringIO()
        provider1 = SimpleDependencyProvider("dep1", cleanup_tracker)
        provider2 = SimpleDependencyProvider("dep2", cleanup_tracker, raise_on_enter=True)

        with pytest.raises(RuntimeError, match="Simulated error in dep2"):
            async with VisualizingDependencyStack(output=output, show_timestamps=False) as stack:
                await stack.enter_dependency(provider1, "input")
                await stack.enter_dependency(provider2, "input")

        # Check output
        output_str = output.getvalue()
        assert "✓ dep1" in output_str
        assert "✗ dep2" in output_str
        assert "RuntimeError" in output_str

        # Check has_failures
        assert stack.has_failures() is True

        # Verify cleanup
        assert cleanup_tracker == ["dep1"]

    @pytest.mark.asyncio
    async def test_timestamps_option(self) -> None:
        """
        Stack should respect show_timestamps option.
        """
        cleanup_tracker: list[str] = []
        output_with_ts = StringIO()
        output_without_ts = StringIO()

        provider1 = SimpleDependencyProvider("dep1", cleanup_tracker)
        provider2 = SimpleDependencyProvider("dep2", cleanup_tracker)

        # With timestamps
        async with VisualizingDependencyStack(output=output_with_ts, show_timestamps=True) as stack:
            await stack.enter_dependency(provider1, "input")

        # Without timestamps
        async with VisualizingDependencyStack(
            output=output_without_ts, show_timestamps=False
        ) as stack:
            await stack.enter_dependency(provider2, "input")

        # Verify timestamps present/absent
        assert "[" in output_with_ts.getvalue()
        assert "]" in output_with_ts.getvalue()
        assert "[" not in output_without_ts.getvalue()

    @pytest.mark.asyncio
    async def test_summary_output(self) -> None:
        """
        Stack should print summary with correct counts.
        """
        cleanup_tracker: list[str] = []
        output = StringIO()

        async with VisualizingDependencyStack(output=output, show_timestamps=False) as stack:
            provider1 = SimpleDependencyProvider("dep1", cleanup_tracker)
            provider2 = SimpleDependencyProvider("dep2", cleanup_tracker)
            await stack.enter_dependency(provider1, "input")
            await stack.enter_dependency(provider2, "input")

            stack.print_summary()

        # Check summary
        summary = output.getvalue()
        assert "Summary" in summary
        assert "Completed: 2" in summary
        assert "Failed: 0" in summary

    @pytest.mark.asyncio
    async def test_composer_failure_visualization(self) -> None:
        """
        Stack should visualize composer failures.
        """
        cleanup_tracker: list[str] = []
        output = StringIO()

        class FailingComposer(DependencyComposer[str, str]):
            @property
            def stage_name(self) -> str:
                return "failing-composer"

            @asynccontextmanager
            async def compose(self, stack: DependencyStack, setup_input: str) -> AsyncIterator[str]:
                provider1 = SimpleDependencyProvider("dep1", cleanup_tracker)
                await stack.enter_dependency(provider1, setup_input)
                raise RuntimeError("Composer internal error")
                yield  # Never reached but required for async generator

        with pytest.raises(RuntimeError, match="Composer internal error"):
            async with VisualizingDependencyStack(output=output, show_timestamps=False) as stack:
                await stack.enter_composer(FailingComposer(), "input")

        # Check output
        output_str = output.getvalue()
        assert "▶ failing-composer" in output_str
        assert "✓ dep1" in output_str
        assert "✗ failing-composer" in output_str

        # Verify cleanup
        assert cleanup_tracker == ["dep1"]
