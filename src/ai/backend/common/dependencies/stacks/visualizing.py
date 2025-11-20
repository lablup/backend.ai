from __future__ import annotations

import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TextIO

from ..base import (
    DependencyComposer,
    DependencyProvider,
    DependencyStack,
    ResourcesT,
    ResourceT,
    SetupInputT,
)


class DependencyStatus(Enum):
    """
    Status of a dependency during lifecycle.
    """

    STARTING = "starting"  # Composer starting
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DependencyEvent:
    """
    Event record for dependency lifecycle.
    """

    stage_name: str
    status: DependencyStatus
    timestamp: datetime
    error: Exception | None = None
    depth: int = 0


class VisualizingDependencyStack(DependencyStack):
    """
    Dependency stack that visualizes the lifecycle of dependencies.

    This stack tracks and displays the lifecycle events of all dependencies
    and composers as they are entered and exited. Useful for debugging
    and validating dependency setup in production environments.
    """

    _stack: AsyncExitStack
    _output: TextIO
    _show_timestamps: bool
    _events: list[DependencyEvent]
    _depth: int

    def __init__(
        self,
        output: TextIO = sys.stdout,
        show_timestamps: bool = True,
    ) -> None:
        """
        Initialize visualizing dependency stack.

        Args:
            output: Output stream for visualization (default: stdout)
            show_timestamps: Whether to show timestamps in output
        """
        self._stack = AsyncExitStack()
        self._output = output
        self._show_timestamps = show_timestamps
        self._events = []
        self._depth = 0

    def _format_event(self, event: DependencyEvent) -> str:
        """
        Format a dependency event for display.
        """
        parts = []

        # Timestamp
        if self._show_timestamps:
            timestamp_str = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
            parts.append(f"[{timestamp_str}]")

        # Indentation
        indent = "  " * event.depth

        # Format based on status
        if event.status == DependencyStatus.STARTING:
            # Composer starting
            parts.append(f"{indent}▶ {event.stage_name}")
        elif event.status == DependencyStatus.COMPLETED:
            # Completed - just show name with check mark
            parts.append(f"{indent}  ✓ {event.stage_name}")
        else:  # FAILED
            parts.append(f"{indent}  ✗ {event.stage_name}")
            # Error details
            if event.error:
                parts.append(f"- {type(event.error).__name__}: {event.error}")

        return " ".join(parts)

    def _print_event(self, event: DependencyEvent) -> None:
        """
        Print a dependency event.
        """
        output = self._format_event(event)
        print(output, file=self._output)
        self._output.flush()

    def _record_event(
        self,
        stage_name: str,
        status: DependencyStatus,
        error: Exception | None = None,
    ) -> None:
        """
        Record and display a dependency event.
        """
        event = DependencyEvent(
            stage_name=stage_name,
            status=status,
            timestamp=datetime.now(),
            error=error,
            depth=self._depth,
        )
        self._events.append(event)
        self._print_event(event)

    async def enter_dependency(
        self,
        provider: DependencyProvider[SetupInputT, ResourceT],
        setup_input: SetupInputT,
    ) -> ResourceT:
        """
        Enter a dependency with visualization.
        """
        stage_name = provider.stage_name

        try:
            resource = await self._stack.enter_async_context(provider.provide(setup_input))
            self._record_event(stage_name, DependencyStatus.COMPLETED)
            return resource
        except Exception as e:
            self._record_event(stage_name, DependencyStatus.FAILED, error=e)
            raise

    async def enter_composer(
        self,
        composer: DependencyComposer[SetupInputT, ResourcesT],
        setup_input: SetupInputT,
    ) -> ResourcesT:
        """
        Enter a composer with visualization.
        """
        stage_name = composer.stage_name

        # Show composer starting
        self._record_event(stage_name, DependencyStatus.STARTING)
        self._depth += 1

        try:
            # Create a nested visualizing stack for the composer
            nested_stack = VisualizingDependencyStack(
                output=self._output,
                show_timestamps=self._show_timestamps,
            )
            nested_stack._depth = self._depth
            nested_stack._events = self._events  # Share event list

            await self._stack.enter_async_context(nested_stack)
            resources = await nested_stack._stack.enter_async_context(
                composer.compose(nested_stack, setup_input)
            )

            # Don't record completion for composers - only show starting
            return resources
        except Exception as e:
            self._record_event(stage_name, DependencyStatus.FAILED, error=e)
            raise
        finally:
            self._depth -= 1

    async def __aenter__(self) -> VisualizingDependencyStack:
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

    def get_events(self) -> list[DependencyEvent]:
        """
        Get all recorded dependency events.
        """
        return self._events.copy()

    def has_failures(self) -> bool:
        """
        Check if any dependency failed.
        """
        return any(event.status == DependencyStatus.FAILED for event in self._events)

    def print_summary(self) -> None:
        """
        Print a summary of dependency setup.
        """
        print("\n" + "=" * 60, file=self._output)
        print("Summary", file=self._output)
        print("=" * 60, file=self._output)

        completed = len([e for e in self._events if e.status == DependencyStatus.COMPLETED])
        failed = len([e for e in self._events if e.status == DependencyStatus.FAILED])

        print(f"Completed: {completed}", file=self._output)
        print(f"Failed: {failed}", file=self._output)

        if self.has_failures():
            print("\nFailed dependencies:", file=self._output)
            for event in self._events:
                if event.status == DependencyStatus.FAILED:
                    print(f"  - {event.stage_name}: {event.error}", file=self._output)

        print("=" * 60 + "\n", file=self._output)
        self._output.flush()
