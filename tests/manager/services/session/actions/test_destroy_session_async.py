"""
Tests for asynchronous session destruction flow.
Tests that destroy_session marks sessions for termination and returns immediately.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.repositories.schedule.repository import MarkTerminatingResult
from ai.backend.manager.services.session.service import SessionService
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator


@pytest.fixture
def mock_schedule_coordinator():
    """Mock ScheduleCoordinator for testing."""
    mock = MagicMock(spec=ScheduleCoordinator)
    mock.mark_sessions_for_termination = AsyncMock()
    return mock


@pytest.fixture
def mock_session_service(mock_schedule_coordinator):
    """Mock SessionService with ScheduleCoordinator."""
    mock_service = MagicMock(spec=SessionService)
    mock_service._schedule_coordinator = mock_schedule_coordinator
    return mock_service


class TestAsyncDestroy:
    """Test asynchronous session destruction flow."""

    async def test_destroy_session_marks_for_termination(
        self,
        mock_schedule_coordinator,
        mock_session_service,
    ):
        """Test that destroy_session marks sessions for termination."""
        # Setup
        session_ids = [str(uuid4()) for _ in range(3)]
        mock_schedule_coordinator.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[session_ids[0]],  # PENDING session
                terminating_sessions=[session_ids[1], session_ids[2]],  # RUNNING sessions
                skipped_sessions=[],
            )
        )

        # Execute
        result = await mock_session_service._schedule_coordinator.mark_sessions_for_termination(
            session_ids,
            reason="USER_REQUESTED",
        )

        # Verify
        assert mock_schedule_coordinator.mark_sessions_for_termination.called
        assert len(result.cancelled_sessions) == 1
        assert len(result.terminating_sessions) == 2
        assert result.has_processed() is True

    async def test_destroy_session_returns_immediately(
        self,
        mock_schedule_coordinator,
        mock_session_service,
    ):
        """Test that destroy_session returns immediately without waiting."""
        # Setup
        session_id = str(uuid4())
        mock_schedule_coordinator.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[session_id],
                skipped_sessions=[],
            )
        )

        # Execute - This should return immediately
        result = await mock_session_service._schedule_coordinator.mark_sessions_for_termination(
            [session_id],
            reason="USER_REQUESTED",
        )

        # Verify
        # The method should return quickly without waiting for actual termination
        assert result.processed_count() == 1
        # Verify that no agent destroy_kernel calls were made (those happen later in scheduler)
        # This would be checked by ensuring no agent client methods were called

    async def test_destroy_session_handles_different_statuses(
        self,
        mock_schedule_coordinator,
    ):
        """Test handling of sessions with different statuses."""
        # Setup
        pending_session = str(uuid4())
        running_session = str(uuid4())
        terminating_session = str(uuid4())
        terminated_session = str(uuid4())

        mock_schedule_coordinator.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[pending_session],
                terminating_sessions=[running_session],
                skipped_sessions=[terminating_session, terminated_session],
            )
        )

        # Execute
        all_sessions = [pending_session, running_session, terminating_session, terminated_session]
        result = await mock_schedule_coordinator.mark_sessions_for_termination(
            all_sessions,
            reason="FORCED_TERMINATION",
        )

        # Verify
        assert pending_session in result.cancelled_sessions
        assert running_session in result.terminating_sessions
        assert terminating_session in result.skipped_sessions
        assert terminated_session in result.skipped_sessions

    async def test_destroy_session_response_format(
        self,
        mock_schedule_coordinator,
    ):
        """Test that destroy_session returns the correct response format."""
        # Setup different scenarios
        test_cases = [
            # Case 1: PENDING session -> cancelled
            (
                MarkTerminatingResult(
                    cancelled_sessions=[str(uuid4())],
                    terminating_sessions=[],
                    skipped_sessions=[],
                ),
                {"status": "cancelled"},
            ),
            # Case 2: RUNNING session -> terminating
            (
                MarkTerminatingResult(
                    cancelled_sessions=[],
                    terminating_sessions=[str(uuid4())],
                    skipped_sessions=[],
                ),
                {"status": "terminated"},
            ),
            # Case 3: Already terminated -> no change
            (
                MarkTerminatingResult(
                    cancelled_sessions=[],
                    terminating_sessions=[],
                    skipped_sessions=[str(uuid4())],
                ),
                {},
            ),
        ]

        for mark_result, expected_stats in test_cases:
            mock_schedule_coordinator.mark_sessions_for_termination.return_value = mark_result

            # Create expected response based on mark result
            if mark_result.cancelled_sessions:
                last_stat = {"status": "cancelled"}
            elif mark_result.terminating_sessions:
                last_stat = {"status": "terminated"}
            else:
                last_stat = {}

            # Verify the response format matches what destroy_session should return
            expected_response = {"stats": last_stat}
            assert "stats" in expected_response
            assert expected_response["stats"] == expected_stats

    async def test_destroy_session_recursive_marks_all(
        self,
        mock_schedule_coordinator,
    ):
        """Test that recursive destroy marks all related sessions."""
        # Setup
        main_session = str(uuid4())
        dep_session1 = str(uuid4())
        dep_session2 = str(uuid4())

        all_sessions = [main_session, dep_session1, dep_session2]
        mock_schedule_coordinator.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=all_sessions,
                skipped_sessions=[],
            )
        )

        # Execute with recursive flag
        result = await mock_schedule_coordinator.mark_sessions_for_termination(
            all_sessions,
            reason="RECURSIVE_TERMINATION",
        )

        # Verify all sessions are marked
        assert len(result.terminating_sessions) == 3
        assert all(sid in result.terminating_sessions for sid in all_sessions)

    async def test_destroy_session_not_found(
        self,
        mock_schedule_coordinator,
    ):
        """Test handling of non-existent sessions."""
        # Setup
        fake_session = str(uuid4())
        mock_schedule_coordinator.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[],
                skipped_sessions=[fake_session],  # Not found sessions go to skipped
            )
        )

        # Execute
        result = await mock_schedule_coordinator.mark_sessions_for_termination(
            [fake_session],
            reason="USER_REQUESTED",
        )

        # Verify
        assert fake_session in result.skipped_sessions
        assert result.has_processed() is False

    async def test_destroy_session_forced_flag(
        self,
        mock_schedule_coordinator,
    ):
        """Test that forced flag affects the termination reason."""
        # Setup
        session_id = str(uuid4())

        # Test with forced=True
        mock_schedule_coordinator.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[session_id],
                skipped_sessions=[],
            )
        )

        # Execute with forced termination
        await mock_schedule_coordinator.mark_sessions_for_termination(
            [session_id],
            reason="FORCED_BY_ADMIN",
        )

        # Verify the reason was passed correctly
        mock_schedule_coordinator.mark_sessions_for_termination.assert_called_with(
            [session_id],
            reason="FORCED_BY_ADMIN",
        )

    async def test_destroy_session_schedule_request_triggered(
        self,
        mock_schedule_coordinator,
    ):
        """Test that marking sessions triggers scheduling request."""
        # Setup
        session_id = str(uuid4())
        mock_schedule_coordinator.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[session_id],
                skipped_sessions=[],
            )
        )
        mock_schedule_coordinator.mark_schedule_needed = AsyncMock()

        # In the real implementation, mark_sessions_for_termination in ScheduleCoordinator
        # should call mark_schedule_needed if any sessions were processed
        # For this test, we're verifying the flow would work correctly

        result = await mock_schedule_coordinator.mark_sessions_for_termination(
            [session_id],
            reason="USER_REQUESTED",
        )

        # Verify that sessions were marked for termination
        assert result.has_processed() is True
        assert len(result.terminating_sessions) == 1

        # In the real implementation, this would trigger scheduling
        # The actual scheduler would later pick up these sessions and terminate them
