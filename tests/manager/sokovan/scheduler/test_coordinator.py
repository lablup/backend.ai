"""
Tests for ScheduleCoordinator.
Tests the coordinator that manages scheduling operations and termination marking.
"""

from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.repositories.schedule.repository import MarkTerminatingResult
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler


@pytest.fixture
def mock_scheduler():
    """Mock Scheduler for testing."""
    mock = MagicMock(spec=Scheduler)
    # Create AsyncMock with support for side_effect
    mock._mark_sessions_for_termination = AsyncMock()
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
def schedule_coordinator(
    mock_scheduler,
    mock_valkey_schedule,
    mock_event_producer,
    mock_scheduler_dispatcher,
):
    """Create ScheduleCoordinator with mocked dependencies."""
    return ScheduleCoordinator(
        valkey_schedule=mock_valkey_schedule,
        scheduler=mock_scheduler,
        event_producer=mock_event_producer,
        scheduler_dispatcher=mock_scheduler_dispatcher,
    )


class TestScheduleCoordinator:
    """Test cases for ScheduleCoordinator."""

    async def test_mark_sessions_for_termination_success(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduler,
        mock_valkey_schedule,
    ):
        """Test successful marking of sessions for termination."""
        # Setup
        session_ids = [str(uuid4()) for _ in range(3)]
        mock_result = MarkTerminatingResult(
            cancelled_sessions=[session_ids[0]],
            terminating_sessions=[session_ids[1], session_ids[2]],
            skipped_sessions=[],
            not_found_sessions=[],
        )
        mock_scheduler._mark_sessions_for_termination.return_value = mock_result

        # Execute
        result = await schedule_coordinator.mark_sessions_for_termination(
            session_ids,
            reason="USER_REQUESTED",
        )

        # Verify
        assert result == mock_result
        mock_scheduler._mark_sessions_for_termination.assert_called_once_with(
            session_ids,
            "USER_REQUESTED",
        )

        # Verify scheduling was requested since sessions were processed
        mock_valkey_schedule.mark_schedule_needed.assert_called_once_with(
            ScheduleType.TERMINATE.value
        )

    async def test_mark_sessions_no_scheduling_when_nothing_processed(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduler,
        mock_valkey_schedule,
    ):
        """Test that no scheduling is requested when no sessions are processed."""
        # Setup
        session_ids = [str(uuid4()) for _ in range(2)]
        mock_result = MarkTerminatingResult(
            cancelled_sessions=[],
            terminating_sessions=[],
            skipped_sessions=session_ids,  # All skipped
            not_found_sessions=[],
        )
        mock_scheduler._mark_sessions_for_termination.return_value = mock_result

        # Execute
        result = await schedule_coordinator.mark_sessions_for_termination(
            session_ids,
            reason="USER_REQUESTED",
        )

        # Verify
        assert result == mock_result
        assert not result.has_processed()

        # No scheduling should be requested
        mock_valkey_schedule.mark_schedule_needed.assert_not_called()

    async def test_request_scheduling_direct(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule,
    ):
        """Test direct scheduling request."""
        # Execute - request different schedule types
        await schedule_coordinator.request_scheduling(ScheduleType.SCHEDULE)
        await schedule_coordinator.request_scheduling(ScheduleType.START)
        await schedule_coordinator.request_scheduling(ScheduleType.TERMINATE)

        # Verify
        assert mock_valkey_schedule.mark_schedule_needed.call_count == 3
        calls = mock_valkey_schedule.mark_schedule_needed.call_args_list
        assert calls[0] == call(ScheduleType.SCHEDULE.value)
        assert calls[1] == call(ScheduleType.START.value)
        assert calls[2] == call(ScheduleType.TERMINATE.value)

    async def test_mark_sessions_with_custom_reason(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduler,
    ):
        """Test marking sessions with different termination reasons."""
        # Setup
        session_id = str(uuid4())
        reasons = [
            "USER_REQUESTED",
            "ADMIN_FORCED",
            "IDLE_TIMEOUT",
            "RESOURCE_LIMIT",
            "SYSTEM_MAINTENANCE",
        ]

        for reason in reasons:
            mock_result = MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[session_id],
                skipped_sessions=[],
                not_found_sessions=[],
            )
            mock_scheduler._mark_sessions_for_termination.return_value = mock_result

            # Execute
            await schedule_coordinator.mark_sessions_for_termination(
                [session_id],
                reason=reason,
            )

            # Verify reason was passed correctly
            mock_scheduler._mark_sessions_for_termination.assert_called_with(
                [session_id],
                reason,
            )

    async def test_mark_sessions_empty_list(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduler,
        mock_valkey_schedule,
    ):
        """Test marking with empty session list."""
        # Setup
        mock_result = MarkTerminatingResult(
            cancelled_sessions=[],
            terminating_sessions=[],
            skipped_sessions=[],
            not_found_sessions=[],
        )
        mock_scheduler._mark_sessions_for_termination.return_value = mock_result

        # Execute
        result = await schedule_coordinator.mark_sessions_for_termination(
            [],  # Empty list
            reason="USER_REQUESTED",
        )

        # Verify
        assert not result.has_processed()
        mock_valkey_schedule.mark_schedule_needed.assert_not_called()

    async def test_mark_sessions_mixed_results(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduler,
        mock_valkey_schedule,
    ):
        """Test marking with mixed results (some found, some not)."""
        # Setup
        existing_sessions = [str(uuid4()) for _ in range(3)]
        non_existing = [str(uuid4()) for _ in range(2)]
        all_sessions = existing_sessions + non_existing

        mock_result = MarkTerminatingResult(
            cancelled_sessions=[existing_sessions[0]],
            terminating_sessions=[existing_sessions[1], existing_sessions[2]],
            skipped_sessions=[],
            not_found_sessions=non_existing,
        )
        mock_scheduler._mark_sessions_for_termination.return_value = mock_result

        # Execute
        result = await schedule_coordinator.mark_sessions_for_termination(
            all_sessions,
            reason="BATCH_CLEANUP",
        )

        # Verify
        assert result.processed_count() == 3  # Only existing sessions processed
        assert len(result.not_found_sessions) == 2

        # Scheduling should be requested for processed sessions
        mock_valkey_schedule.mark_schedule_needed.assert_called_once_with(
            ScheduleType.TERMINATE.value
        )

    async def test_coordinator_exception_handling(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduler,
        mock_valkey_schedule,
    ):
        """Test that coordinator handles exceptions from scheduler."""
        # Setup - scheduler raises exception
        mock_scheduler._mark_sessions_for_termination.side_effect = Exception(
            "Database connection failed"
        )

        # Execute and verify exception is propagated
        with pytest.raises(Exception) as exc_info:
            await schedule_coordinator.mark_sessions_for_termination(
                [str(uuid4())],
                reason="TEST_EXCEPTION",
            )

        assert "Database connection failed" in str(exc_info.value)

        # No scheduling should be requested on error
        mock_valkey_schedule.mark_schedule_needed.assert_not_called()

    async def test_coordinator_concurrent_marking(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduler,
        mock_valkey_schedule,
    ):
        """Test concurrent marking requests."""
        import asyncio

        # Setup
        session_groups = [[str(uuid4()) for _ in range(2)] for _ in range(3)]

        def setup_mock_result(session_ids, reason):
            return MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=session_ids,
                skipped_sessions=[],
                not_found_sessions=[],
            )

        mock_scheduler._mark_sessions_for_termination.side_effect = setup_mock_result

        # Execute concurrent marking
        tasks = [
            schedule_coordinator.mark_sessions_for_termination(
                sessions,
                reason=f"CONCURRENT_{i}",
            )
            for i, sessions in enumerate(session_groups)
        ]
        results = await asyncio.gather(*tasks)

        # Verify
        assert len(results) == 3
        for i, result in enumerate(results):
            assert len(result.terminating_sessions) == 2
            assert result.terminating_sessions == session_groups[i]

        # Should have requested scheduling 3 times
        assert mock_valkey_schedule.mark_schedule_needed.call_count == 3
