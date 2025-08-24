"""Integration tests for leader election with LeaderTask injection."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_leader.client import ValkeyLeaderClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.leader import (
    AlreadyStartedError,
    LeadershipChecker,
    LeaderTask,
    ValkeyLeaderElection,
)
from ai.backend.common.leader.tasks import EventProducerTask, EventTaskSpec, LeaderCron
from ai.backend.common.leader.valkey_leader_election import ValkeyLeaderElectionConfig


class MockLeaderTask(LeaderTask):
    """Mock implementation of LeaderTask for testing."""

    def __init__(self) -> None:
        self.start_called = False
        self.stop_called = False
        self.leadership_checker: LeadershipChecker | None = None
        self.execution_count = 0
        self._task: asyncio.Task | None = None
        self._stopped = False

    async def start(self, leadership_checker: LeadershipChecker) -> None:
        self.start_called = True
        self.leadership_checker = leadership_checker
        self._stopped = False
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Simulate task execution."""
        while not self._stopped:
            if self.leadership_checker and self.leadership_checker.is_leader:
                self.execution_count += 1
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        self.stop_called = True
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


@pytest.fixture
async def mock_leader_client():
    """Create a mock ValkeyLeaderClient."""
    client = AsyncMock(spec=ValkeyLeaderClient)
    client.acquire_or_renew_leadership = AsyncMock(return_value=False)
    client.release_leadership = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
async def mock_event_producer():
    """Create a mock EventProducer."""
    producer = AsyncMock(spec=EventProducer)
    producer.anycast_event = AsyncMock()
    return producer


@pytest.fixture
async def leader_election_config():
    """Create a ValkeyLeaderElectionConfig."""
    return ValkeyLeaderElectionConfig(
        server_id="test-server-001",
        leader_key="test:leader",
        lease_duration=10,
        renewal_interval=0.5,  # Short interval for testing
    )


@pytest.fixture
async def leader_election(mock_leader_client, leader_election_config):
    """Create a ValkeyLeaderElection instance."""
    return ValkeyLeaderElection(
        leader_client=mock_leader_client,
        config=leader_election_config,
    )


class TestLeaderTaskIntegration:
    """Test cases for LeaderTask integration with ValkeyLeaderElection."""

    async def test_task_registration(self, leader_election):
        """Test registering LeaderTask instances."""
        task1 = MockLeaderTask()
        task2 = MockLeaderTask()

        leader_election.register_task(task1)
        leader_election.register_task(task2)

        assert len(leader_election._leader_tasks) == 2
        assert task1 in leader_election._leader_tasks
        assert task2 in leader_election._leader_tasks

    async def test_task_registration_after_start_fails(self, leader_election):
        """Test that registering tasks after start() raises RuntimeError."""
        task1 = MockLeaderTask()

        # Register a task before start is fine
        leader_election.register_task(task1)

        # Start the election
        await leader_election.start()

        # Try to register another task after start
        task2 = MockLeaderTask()
        with pytest.raises(
            AlreadyStartedError, match="Cannot register tasks after leader election has started"
        ):
            leader_election.register_task(task2)

        # Stop the election
        await leader_election.stop()

    async def test_tasks_start_on_election_start(self, leader_election):
        """Test that all registered tasks start when election starts."""
        task1 = MockLeaderTask()
        task2 = MockLeaderTask()

        leader_election.register_task(task1)
        leader_election.register_task(task2)

        # Start election
        await leader_election.start()

        # Verify tasks were started
        assert task1.start_called
        assert task2.start_called
        assert task1.leadership_checker is not None
        assert task2.leadership_checker is not None

        # Stop election
        await leader_election.stop()

    async def test_tasks_stop_on_election_stop(self, leader_election):
        """Test that all tasks stop when election stops."""
        task1 = MockLeaderTask()
        task2 = MockLeaderTask()

        leader_election.register_task(task1)
        leader_election.register_task(task2)

        # Start and stop election
        await leader_election.start()
        await leader_election.stop()

        # Verify tasks were stopped
        assert task1.stop_called
        assert task2.stop_called

    async def test_tasks_execute_when_leader(self, leader_election, mock_leader_client):
        """Test that tasks execute only when instance is leader."""
        # Configure to become leader
        mock_leader_client.acquire_or_renew_leadership.return_value = True

        task = MockLeaderTask()
        leader_election.register_task(task)

        # Start election
        await leader_election.start()

        # Wait for leadership acquisition and task execution
        await asyncio.sleep(1.5)

        # Verify task executed
        assert task.execution_count > 0

        # Stop election
        await leader_election.stop()

    async def test_tasks_dont_execute_when_not_leader(self, leader_election, mock_leader_client):
        """Test that tasks don't execute when instance is not leader."""
        # Configure to never become leader
        mock_leader_client.acquire_or_renew_leadership.return_value = False

        task = MockLeaderTask()
        leader_election.register_task(task)

        # Start election
        await leader_election.start()

        # Wait a bit
        await asyncio.sleep(1.0)

        # Verify task didn't execute
        assert task.execution_count == 0

        # Stop election
        await leader_election.stop()

    async def test_leader_cron_integration(
        self, leader_election, mock_leader_client, mock_event_producer
    ):
        """Test LeaderCron integration with ValkeyLeaderElection."""
        # Configure to become leader
        mock_leader_client.acquire_or_renew_leadership.return_value = True

        # Create event tasks
        event = MagicMock()
        event_factory = MagicMock(return_value=event)
        spec = EventTaskSpec(
            name="test-event",
            event_factory=event_factory,
            interval=0.2,
            initial_delay=0.0,
        )
        event_task = EventProducerTask(spec, mock_event_producer)

        # Create LeaderCron with tasks
        leader_cron = LeaderCron(tasks=[event_task])

        # Register LeaderCron with election
        leader_election.register_task(leader_cron)

        # Start election
        await leader_election.start()

        # Wait for event production
        await asyncio.sleep(1.0)

        # Verify events were produced
        assert event_factory.call_count >= 3
        assert mock_event_producer.anycast_event.call_count >= 3

        # Stop election
        await leader_election.stop()

    async def test_multiple_leader_tasks(
        self, leader_election, mock_leader_client, mock_event_producer
    ):
        """Test managing multiple different LeaderTask types."""
        # Configure to become leader
        mock_leader_client.acquire_or_renew_leadership.return_value = True

        # Create different types of tasks
        mock_task = MockLeaderTask()

        # Create event task for LeaderCron
        event = MagicMock()
        event_factory = MagicMock(return_value=event)
        spec = EventTaskSpec(
            name="periodic-event",
            event_factory=event_factory,
            interval=0.2,
            initial_delay=0.0,
        )
        event_task = EventProducerTask(spec, mock_event_producer)
        leader_cron = LeaderCron(tasks=[event_task])

        # Register both tasks with election
        leader_election.register_task(mock_task)
        leader_election.register_task(leader_cron)

        # Start election
        await leader_election.start()

        # Wait for execution
        await asyncio.sleep(1.0)

        # Verify both tasks executed
        assert mock_task.execution_count > 0
        assert event_factory.call_count >= 3

        # Stop election
        await leader_election.stop()

        # Verify both stopped
        assert mock_task.stop_called

    async def test_leadership_change_affects_tasks(self, leader_election, mock_leader_client):
        """Test that leadership changes affect task execution."""
        # Start as non-leader, then become leader, then lose leadership
        mock_leader_client.acquire_or_renew_leadership.side_effect = [
            False,
            False,
            True,
            True,
            False,
            False,
        ]

        task = MockLeaderTask()
        leader_election.register_task(task)

        # Start election
        await leader_election.start()

        # Initially not leader
        await asyncio.sleep(1.0)
        initial_count = task.execution_count
        assert initial_count == 0

        # Become leader (after 2 renewal cycles)
        await asyncio.sleep(1.5)
        mid_count = task.execution_count
        assert mid_count > 0

        # Lose leadership (after 4 renewal cycles)
        await asyncio.sleep(1.5)
        final_count = task.execution_count

        # Wait to ensure no more executions
        await asyncio.sleep(0.5)
        assert task.execution_count == final_count

        # Stop election
        await leader_election.stop()
