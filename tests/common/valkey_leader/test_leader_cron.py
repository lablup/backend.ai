"""Tests for LeaderCron implementation."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.types import AbstractAnycastEvent
from ai.backend.common.leader import LeadershipChecker
from ai.backend.common.leader.tasks import (
    EventProducerTask,
    EventTaskSpec,
    LeaderCron,
    PeriodicTask,
)


class MockTask(PeriodicTask):
    """Mock implementation of PeriodicTask for testing."""

    def __init__(
        self,
        name: str = "mock-task",
        interval: float = 1.0,
        initial_delay: float = 0.0,
        run_func: AsyncMock | None = None,
    ):
        self._name = name
        self._interval = interval
        self._initial_delay = initial_delay
        self.run_func = run_func or AsyncMock()
        self.run_count = 0

    async def run(self) -> None:
        """Execute the mock task."""
        self.run_count += 1
        await self.run_func()

    @property
    def name(self) -> str:
        """Task name."""
        return self._name

    @property
    def interval(self) -> float:
        """Interval."""
        return self._interval

    @property
    def initial_delay(self) -> float:
        """Initial delay."""
        return self._initial_delay


@pytest.fixture
async def mock_event_producer():
    """Create a mock EventProducer."""
    producer = AsyncMock(spec=EventProducer)
    producer.anycast_event = AsyncMock()
    return producer


@pytest.fixture
async def mock_event():
    """Create a mock event."""
    event = create_autospec(AbstractAnycastEvent, instance=True)
    return event


@pytest.fixture
async def mock_tasks():
    """Create mock tasks."""
    return [
        MockTask(name="task1", interval=0.1, initial_delay=0.0),
        MockTask(name="task2", interval=0.2, initial_delay=0.1),
    ]


@pytest.fixture
async def leader_cron(mock_tasks):
    """Create a LeaderCron instance with mock tasks."""
    return LeaderCron(tasks=mock_tasks)


@pytest.fixture
async def event_tasks(mock_event_producer, mock_event):
    """Create EventProducerTask instances."""
    tasks = []
    for i in range(2):
        spec = EventTaskSpec(
            name=f"event-task-{i}",
            event_factory=MagicMock(return_value=mock_event),
            interval=0.1,
            initial_delay=0.0,
        )
        tasks.append(EventProducerTask(spec, mock_event_producer))
    return tasks


@pytest.fixture
async def leader_cron_with_event_tasks(event_tasks):
    """Create a LeaderCron with EventTasks."""
    return LeaderCron(tasks=event_tasks)


class TestLeaderCron:
    """Test cases for LeaderCron."""

    async def test_initialization(self, mock_tasks):
        """Test LeaderCron initialization."""
        leader_cron = LeaderCron(tasks=mock_tasks)

        assert leader_cron._stopped is False
        assert len(leader_cron._tasks) == 2
        assert len(leader_cron._task_runners) == 0

    async def test_start_stop(self, leader_cron):
        """Test starting and stopping the cron."""
        # Create a mock leadership checker
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = False

        # Start the cron
        await leader_cron.start(leadership_checker)

        # Verify state
        assert len(leader_cron._task_runners) == len(leader_cron._tasks)
        assert not leader_cron._stopped
        assert leader_cron._leadership_checker == leadership_checker

        # Give it a moment to run
        await asyncio.sleep(0.1)

        # Stop the cron
        await leader_cron.stop()

        # Verify everything was stopped
        assert leader_cron._stopped is True
        assert len(leader_cron._task_runners) == 0

    async def test_tasks_execute_as_leader(self, mock_tasks):
        """Test that tasks execute when server is leader."""
        # Create LeaderCron with mock tasks
        leader_cron = LeaderCron(tasks=mock_tasks)

        # Set up leadership checker to return True
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = True

        # Start the cron
        await leader_cron.start(leadership_checker)

        # Wait for tasks to execute
        await asyncio.sleep(0.5)

        # Verify tasks were executed
        for task in mock_tasks:
            assert task.run_count > 0

        # Stop the cron
        await leader_cron.stop()

    async def test_no_task_execution_as_follower(self, mock_tasks):
        """Test that tasks don't execute when server is not leader."""
        # Create LeaderCron with mock tasks
        leader_cron = LeaderCron(tasks=mock_tasks)

        # Set up leadership checker to return False
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = False

        # Start the cron
        await leader_cron.start(leadership_checker)

        # Wait a bit
        await asyncio.sleep(0.3)

        # Verify no tasks were executed
        for task in mock_tasks:
            assert task.run_count == 0

        # Stop the cron
        await leader_cron.stop()

    async def test_event_tasks_produce_events(
        self,
        leader_cron_with_event_tasks,
        mock_event_producer,
    ):
        """Test that EventTasks produce events when leader."""
        # Set up as leader
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = True

        # Start the cron
        await leader_cron_with_event_tasks.start(leadership_checker)

        # Wait for event production
        await asyncio.sleep(0.5)

        # Verify events were produced
        assert mock_event_producer.anycast_event.call_count >= 4

        # Stop the cron
        await leader_cron_with_event_tasks.stop()

    async def test_leadership_change_during_execution(self, mock_tasks):
        """Test behavior when leadership changes during execution."""
        # Create LeaderCron with mock tasks
        leader_cron = LeaderCron(tasks=mock_tasks)

        # Create a mock leadership checker with mutable state
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = False

        # Start the cron
        await leader_cron.start(leadership_checker)

        # Initially not leader - no execution
        await asyncio.sleep(0.2)
        initial_counts = [task.run_count for task in mock_tasks]
        assert all(count == 0 for count in initial_counts)

        # Become leader
        leadership_checker.is_leader = True
        await asyncio.sleep(0.3)

        # Now tasks should execute
        mid_counts = [task.run_count for task in mock_tasks]
        assert all(count > 0 for count in mid_counts)

        # Lose leadership
        leadership_checker.is_leader = False
        current_counts = [task.run_count for task in mock_tasks]
        await asyncio.sleep(0.3)

        # Should stop executing new tasks
        final_counts = [task.run_count for task in mock_tasks]
        assert final_counts == current_counts  # No new executions

        # Stop the cron
        await leader_cron.stop()

    async def test_task_restart_on_failure(self, mock_event_producer):
        """Test that tasks are restarted if they fail."""
        # Create a task that will fail
        failing_task = MockTask(
            name="failing-task",
            interval=0.1,
            initial_delay=0.0,
            run_func=AsyncMock(side_effect=Exception("Task failed")),
        )

        leader_cron = LeaderCron(tasks=[failing_task])

        # Set up as leader
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = True

        # Start the cron
        await leader_cron.start(leadership_checker)

        # Wait a bit for task to fail and potentially restart
        await asyncio.sleep(0.3)

        # Task should have been called despite failures
        assert failing_task.run_func.call_count >= 1

        # Stop the cron
        await leader_cron.stop()

    async def test_initial_delay(self, mock_event_producer):
        """Test that initial_delay is respected."""
        # Create task with initial delay
        delayed_task = MockTask(
            name="delayed-task",
            interval=0.1,
            initial_delay=0.3,
        )

        leader_cron = LeaderCron(tasks=[delayed_task])

        # Set up as leader
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = True

        # Start the cron
        await leader_cron.start(leadership_checker)

        # Wait less than initial delay
        await asyncio.sleep(0.2)

        # Should not have executed yet
        assert delayed_task.run_count == 0

        # Wait past initial delay
        await asyncio.sleep(0.2)

        # Now should have executed
        assert delayed_task.run_count >= 1

        # Stop the cron
        await leader_cron.stop()

    async def test_mixed_task_types(self, mock_event_producer, mock_event):
        """Test LeaderCron with mixed PeriodicTask types."""
        # Create different types of tasks
        mock_task = MockTask(name="mock-task", interval=0.1)

        spec = EventTaskSpec(
            name="event-task",
            event_factory=MagicMock(return_value=mock_event),
            interval=0.1,
            initial_delay=0.0,
        )
        event_task = EventProducerTask(spec, mock_event_producer)

        # Create LeaderCron with mixed tasks
        leader_cron = LeaderCron(tasks=[mock_task, event_task])

        # Set up as leader
        leadership_checker = MagicMock(spec=LeadershipChecker)
        leadership_checker.is_leader = True

        # Start the cron
        await leader_cron.start(leadership_checker)

        # Wait for execution
        await asyncio.sleep(0.3)

        # Verify both task types executed
        assert mock_task.run_count > 0
        assert mock_event_producer.anycast_event.call_count > 0

        # Stop the cron
        await leader_cron.stop()
