from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import pytest

from ai.backend.common.dependencies import DependencyProvider


@dataclass
class DependencyLifecycleTracker:
    """

    Tracks lifecycle events for testing dependency cleanup order.
    """

    events: list[str] = field(default_factory=list)

    def record_enter(self, stage_name: str) -> None:
        """

        Record entry into a dependency stage.
        """
        self.events.append(f"enter:{stage_name}")

    def record_exit(self, stage_name: str) -> None:
        """

        Record exit from a dependency stage.
        """
        self.events.append(f"exit:{stage_name}")

    def get_cleanup_order(self) -> list[str]:
        """

        Get the cleanup order (exit events only).
        """
        return [event.split(":")[1] for event in self.events if event.startswith("exit:")]

    def clear(self) -> None:
        """

        Clear all recorded events.
        """
        self.events.clear()


@pytest.fixture
def lifecycle_tracker() -> DependencyLifecycleTracker:
    """

    Fixture providing a lifecycle tracker for testing.
    """
    return DependencyLifecycleTracker()


class MockDependencyProvider(DependencyProvider[Any, str]):
    """

    Mock dependency provider for testing.
    """

    def __init__(
        self, stage_name: str, tracker: DependencyLifecycleTracker, raise_on_enter: bool = False
    ) -> None:
        self._stage_name = stage_name
        self._tracker = tracker
        self._raise_on_enter = raise_on_enter

    @property
    def stage_name(self) -> str:
        """

        Get the stage name for this mock provider.
        """
        return self._stage_name

    @asynccontextmanager
    async def provide(self, setup_input: Any) -> AsyncIterator[str]:
        """

        Provide a mock resource with lifecycle tracking.
        """
        if self._raise_on_enter:
            raise RuntimeError(f"Simulated error in {self._stage_name}")

        self._tracker.record_enter(self._stage_name)
        try:
            yield f"resource:{self._stage_name}"
        finally:
            self._tracker.record_exit(self._stage_name)
