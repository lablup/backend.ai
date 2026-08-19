"""Tests for LocalCron implementation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import cast, override
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.cron import LocalCron, PeriodicTask


class MockTask(PeriodicTask):
    """Mock implementation of PeriodicTask for testing."""

    def __init__(
        self,
        name: str = "mock-task",
        interval: float = 1.0,
        initial_delay: float = 0.0,
        run_timeout: float | None = None,
        run_func: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self._name = name
        self._interval = interval
        self._initial_delay = initial_delay
        self._run_timeout = run_timeout
        self.run_func = run_func or AsyncMock()
        self.run_count = 0

    @override
    async def run(self) -> None:
        """Execute the mock task."""
        self.run_count += 1
        await self.run_func()

    @property
    @override
    def name(self) -> str:
        return self._name

    @property
    @override
    def interval(self) -> float:
        return self._interval

    @property
    @override
    def initial_delay(self) -> float:
        return self._initial_delay

    @property
    @override
    def run_timeout(self) -> float | None:
        return self._run_timeout


@pytest.fixture
async def mock_tasks() -> list[MockTask]:
    """Create mock tasks."""
    return [
        MockTask(name="task1", interval=0.1, initial_delay=0.0),
        MockTask(name="task2", interval=0.2, initial_delay=0.1),
    ]


class TestLocalCron:
    """Test cases for LocalCron."""

    async def test_initialization(self, mock_tasks: list[MockTask]) -> None:
        """Test LocalCron initialization."""
        local_cron = LocalCron(tasks=cast(list[PeriodicTask], mock_tasks))

        assert local_cron._stopped is False
        assert len(local_cron._tasks) == 2
        assert len(local_cron._task_runners) == 0

    async def test_start_stop(self, mock_tasks: list[MockTask]) -> None:
        """Test starting and stopping the cron."""
        local_cron = LocalCron(tasks=cast(list[PeriodicTask], mock_tasks))

        await local_cron.start()

        assert len(local_cron._task_runners) == len(local_cron._tasks)
        assert not local_cron._stopped

        await asyncio.sleep(0.1)

        await local_cron.stop()

        assert local_cron._stopped is True
        assert len(local_cron._task_runners) == 0  # type: ignore[unreachable]

    async def test_tasks_execute_without_leader(self, mock_tasks: list[MockTask]) -> None:
        """Test that tasks execute unconditionally (no leadership gating)."""
        local_cron = LocalCron(tasks=cast(list[PeriodicTask], mock_tasks))

        await local_cron.start()
        await asyncio.sleep(0.5)

        for task in mock_tasks:
            assert task.run_count > 0

        await local_cron.stop()

    async def test_task_restart_on_failure(self) -> None:
        """A task that raises keeps being re-fired on subsequent intervals."""
        failing_task = MockTask(
            name="failing-task",
            interval=0.1,
            initial_delay=0.0,
            run_func=AsyncMock(side_effect=Exception("Task failed")),
        )

        local_cron = LocalCron(tasks=[failing_task])

        await local_cron.start()
        await asyncio.sleep(0.35)

        # Despite raising every time, the loop survives and keeps invoking run().
        assert failing_task.run_count >= 2

        await local_cron.stop()

    async def test_run_timeout_recovers(self) -> None:
        """A hanging run() is cancelled by run_timeout and re-fired next interval."""

        async def _hang() -> None:
            await asyncio.sleep(10)

        hanging_task = MockTask(
            name="hanging-task",
            interval=0.05,
            initial_delay=0.0,
            run_timeout=0.05,
            run_func=_hang,
        )

        local_cron = LocalCron(tasks=[hanging_task])

        await local_cron.start()
        await asyncio.sleep(0.4)

        # Each tick hangs then times out; the loop must keep re-firing.
        assert hanging_task.run_count >= 2

        await local_cron.stop()

    async def test_initial_delay(self) -> None:
        """Test that initial_delay is respected."""
        delayed_task = MockTask(
            name="delayed-task",
            interval=0.1,
            initial_delay=0.3,
        )

        local_cron = LocalCron(tasks=[delayed_task])

        await local_cron.start()

        await asyncio.sleep(0.2)
        assert delayed_task.run_count == 0

        await asyncio.sleep(0.2)
        assert delayed_task.run_count >= 1

        await local_cron.stop()
