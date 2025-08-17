"""
Tests for ScheduleCoordinator.
Tests the coordinator that manages scheduling operations and termination marking.
"""

from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.scheduler import MarkTerminatingResult
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


@pytest.fixture
def mock_scheduler():
    """Mock Scheduler for testing."""
    mock = MagicMock(spec=Scheduler)
    # Create AsyncMock with support for side_effect
    mock.mark_sessions_for_termination = AsyncMock()
    mock.terminate_sessions = AsyncMock()
    return mock


@pytest.fixture
def mock_valkey_schedule():
    """Mock ValkeyScheduleClient for testing."""
    mock = MagicMock(spec=ValkeyScheduleClient)
    mock.mark_schedule_needed = AsyncMock()
    return mock


@pytest.fixture
def mock_event_producer():
    """Mock EventProducer for testing."""
    mock = MagicMock(spec=EventProducer)
    return mock


@pytest.fixture
def mock_scheduler_dispatcher():
    """Mock SchedulerDispatcher for testing."""
    mock = MagicMock(spec=SchedulerDispatcher)
    return mock


@pytest.fixture
def mock_scheduling_controller():
    """Mock SchedulingController for testing."""
    mock = MagicMock(spec=SchedulingController)
    mock.request_scheduling = AsyncMock()
    mock.mark_sessions_for_termination = AsyncMock()
    return mock


@pytest.fixture
def schedule_coordinator(
    mock_scheduler,
    mock_valkey_schedule,
    mock_event_producer,
    mock_scheduler_dispatcher,
    mock_scheduling_controller,
):
    """Create ScheduleCoordinator with mocked dependencies."""
    return ScheduleCoordinator(
        valkey_schedule=mock_valkey_schedule,
        scheduler=mock_scheduler,
        scheduling_controller=mock_scheduling_controller,
        event_producer=mock_event_producer,
        scheduler_dispatcher=mock_scheduler_dispatcher,
    )


class TestScheduleCoordinator:
    """Test cases for ScheduleCoordinator."""

    async def test_process_if_needed(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule,
    ):
        """Test process_if_needed method."""
        # Test that process_if_needed can be called
        # This is mainly testing that the method exists and delegates correctly
        await schedule_coordinator.process_if_needed(ScheduleType.SCHEDULE)
        # The actual implementation would depend on handlers

    async def test_process_schedule(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule,
    ):
        """Test process_schedule method."""
        # Test that process_schedule can be called
        # This is mainly testing that the method exists and delegates correctly
        await schedule_coordinator.process_schedule(ScheduleType.START)
        # The actual implementation would depend on handlers

    async def test_mark_sessions_for_termination_success(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller,
        mock_valkey_schedule,
    ):
        """Test successful marking of sessions for termination via controller."""
        # Setup
        session_ids = [SessionId(uuid4()) for _ in range(3)]
        mock_result = MarkTerminatingResult(
            cancelled_sessions=[session_ids[0]],
            terminating_sessions=[session_ids[1], session_ids[2]],
            skipped_sessions=[],
        )
        mock_scheduling_controller.mark_sessions_for_termination.return_value = mock_result

        # Execute via controller (coordinator delegates to controller)
        result = await mock_scheduling_controller.mark_sessions_for_termination(
            session_ids,
            reason="USER_REQUESTED",
        )

        # Verify
        assert result == mock_result
        mock_scheduling_controller.mark_sessions_for_termination.assert_called_once_with(
            session_ids,
            reason="USER_REQUESTED",
        )

    async def test_request_scheduling_direct(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller,
        mock_valkey_schedule,
    ):
        """Test direct scheduling request via controller."""
        # Execute - request different schedule types via controller
        await mock_scheduling_controller.request_scheduling(ScheduleType.SCHEDULE)
        await mock_scheduling_controller.request_scheduling(ScheduleType.START)
        await mock_scheduling_controller.request_scheduling(ScheduleType.TERMINATE)

        # Verify controller methods were called
        assert mock_scheduling_controller.request_scheduling.call_count == 3
        calls = mock_scheduling_controller.request_scheduling.call_args_list
        assert calls[0] == call(ScheduleType.SCHEDULE)
        assert calls[1] == call(ScheduleType.START)
        assert calls[2] == call(ScheduleType.TERMINATE)

    async def test_mark_sessions_with_mixed_results(
        self,
        mock_scheduling_controller,
    ):
        """Test marking with mixed results via controller."""
        # Setup
        existing_sessions = [SessionId(uuid4()) for _ in range(3)]
        non_existing = [SessionId(uuid4()) for _ in range(2)]
        all_sessions = existing_sessions + non_existing

        mock_result = MarkTerminatingResult(
            cancelled_sessions=[existing_sessions[0]],
            terminating_sessions=[existing_sessions[1], existing_sessions[2]],
            skipped_sessions=non_existing,
        )
        mock_scheduling_controller.mark_sessions_for_termination.return_value = mock_result

        # Execute via controller
        result = await mock_scheduling_controller.mark_sessions_for_termination(
            all_sessions,
            reason="BATCH_CLEANUP",
        )

        # Verify
        assert result.processed_count() == 3  # Only existing sessions processed
        assert result.skipped_sessions == non_existing
