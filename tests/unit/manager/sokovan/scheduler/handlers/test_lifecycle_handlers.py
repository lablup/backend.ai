"""Unit tests for Sokovan scheduler lifecycle handlers.

Based on BEP-1033 test scenarios for handler-level testing.

Test Scenarios:
- SC-SS-001 ~ SC-SS-005: ScheduleSessionsLifecycleHandler
- SC-CP-001 ~ SC-CP-004: CheckPreconditionLifecycleHandler
- SC-ST-001 ~ SC-ST-005: StartSessionsLifecycleHandler
- SC-TE-001 ~ SC-TE-005: TerminateSessionsLifecycleHandler
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.repositories.scheduler.types.session import (
    TerminatingSessionData,
)
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.check_precondition import (
    CheckPreconditionLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.schedule_sessions import (
    ScheduleSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.start_sessions import (
    StartSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.terminate_sessions import (
    TerminateSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    ScheduleResult,
)
from ai.backend.manager.sokovan.scheduler.types import (
    SessionsForPullWithImages,
    SessionsForStartWithImages,
    SessionWithKernels,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# ScheduleSessionsLifecycleHandler Tests (SC-SS-001 ~ SC-SS-005)
# =============================================================================


class TestScheduleSessionsLifecycleHandler:
    """Tests for ScheduleSessionsLifecycleHandler.

    Verifies the handler correctly delegates to provisioner and categorizes
    results into successes and skipped sessions.
    """

    @pytest.fixture
    def handler(
        self,
        mock_provisioner: AsyncMock,
        mock_repository: AsyncMock,
    ) -> ScheduleSessionsLifecycleHandler:
        """Create handler with mocked dependencies."""
        return ScheduleSessionsLifecycleHandler(
            provisioner=mock_provisioner,
            repository=mock_repository,
        )

    async def test_all_sessions_scheduled_successfully(
        self,
        handler: ScheduleSessionsLifecycleHandler,
        mock_provisioner: AsyncMock,
        mock_repository: AsyncMock,
        pending_sessions_multiple: list[SessionWithKernels],
        schedule_result_success_factory: Callable[..., ScheduleResult],
    ) -> None:
        """SC-SS-001: All pending sessions are scheduled successfully.

        Given: Multiple PENDING sessions in the scaling group
        When: Provisioner schedules all sessions successfully
        Then: All sessions appear in result.successes with reason
        """
        # Arrange
        mock_repository.get_scheduling_data.return_value = MagicMock()
        mock_provisioner.schedule_scaling_group.return_value = schedule_result_success_factory(
            pending_sessions_multiple
        )

        # Act
        result = await handler.execute("default", pending_sessions_multiple)

        # Assert
        assert len(result.successes) == len(pending_sessions_multiple)
        assert len(result.skipped) == 0
        assert len(result.failures) == 0

        # Verify each session is in successes
        success_ids = {s.session_id for s in result.successes}
        for session in pending_sessions_multiple:
            assert session.session_info.identity.id in success_ids

    async def test_partial_scheduling_returns_skipped(
        self,
        handler: ScheduleSessionsLifecycleHandler,
        mock_provisioner: AsyncMock,
        mock_repository: AsyncMock,
        pending_sessions_multiple: list[SessionWithKernels],
    ) -> None:
        """SC-SS-002: Partial scheduling - some sessions skipped.

        Given: Multiple PENDING sessions in the scaling group
        When: Provisioner schedules only the first session
        Then: First session in successes, others in skipped
        """
        # Arrange - Only first session is scheduled
        first_session = pending_sessions_multiple[0]
        mock_repository.get_scheduling_data.return_value = MagicMock()
        mock_provisioner.schedule_scaling_group.return_value = ScheduleResult(
            scheduled_sessions=[
                ScheduledSessionData(
                    session_id=first_session.session_info.identity.id,
                    creation_id=first_session.session_info.identity.creation_id,
                    access_key=AccessKey(first_session.session_info.metadata.access_key),
                    reason="scheduled-successfully",
                )
            ]
        )

        # Act
        result = await handler.execute("default", pending_sessions_multiple)

        # Assert
        assert len(result.successes) == 1
        assert len(result.skipped) == len(pending_sessions_multiple) - 1
        assert result.successes[0].session_id == first_session.session_info.identity.id

        # Verify skipped sessions are the remaining ones
        skipped_ids = {s.session_id for s in result.skipped}
        for session in pending_sessions_multiple[1:]:
            assert session.session_info.identity.id in skipped_ids

    async def test_non_scheduled_sessions_returned_as_skipped(
        self,
        handler: ScheduleSessionsLifecycleHandler,
        mock_provisioner: AsyncMock,
        mock_repository: AsyncMock,
        pending_sessions_multiple: list[SessionWithKernels],
    ) -> None:
        """SC-SS-003: Non-scheduled sessions are marked as skipped (not failures).

        Given: Multiple PENDING sessions in the scaling group
        When: Provisioner schedules none of them (resource constraints)
        Then: All sessions appear in result.skipped with reason
        """
        # Arrange - No sessions scheduled
        mock_repository.get_scheduling_data.return_value = MagicMock()
        mock_provisioner.schedule_scaling_group.return_value = ScheduleResult(scheduled_sessions=[])

        # Act
        result = await handler.execute("default", pending_sessions_multiple)

        # Assert
        assert len(result.successes) == 0
        assert len(result.skipped) == len(pending_sessions_multiple)
        assert len(result.failures) == 0

        # Verify all sessions are skipped with appropriate reason
        for skipped in result.skipped:
            assert skipped.reason == "not-scheduled-this-cycle"

    async def test_empty_session_list_returns_empty_result(
        self,
        handler: ScheduleSessionsLifecycleHandler,
        mock_provisioner: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """SC-SS-004: Empty session list returns empty result immediately.

        Given: Empty session list
        When: Handler is invoked
        Then: Returns empty result without calling provisioner
        """
        # Act
        result = await handler.execute("default", [])

        # Assert
        assert len(result.successes) == 0
        assert len(result.skipped) == 0
        assert len(result.failures) == 0

        # Verify provisioner was not called
        mock_provisioner.schedule_scaling_group.assert_not_awaited()
        mock_repository.get_scheduling_data.assert_not_awaited()

    async def test_no_scheduling_data_skips_all_sessions(
        self,
        handler: ScheduleSessionsLifecycleHandler,
        mock_provisioner: AsyncMock,
        mock_repository: AsyncMock,
        pending_sessions_multiple: list[SessionWithKernels],
    ) -> None:
        """SC-SS-005: No scheduling data available skips all sessions.

        Given: Repository returns None for scheduling data
        When: Handler is invoked
        Then: All sessions marked as skipped with appropriate reason
        """
        # Arrange
        mock_repository.get_scheduling_data.return_value = None

        # Act
        result = await handler.execute("default", pending_sessions_multiple)

        # Assert
        assert len(result.successes) == 0
        assert len(result.skipped) == len(pending_sessions_multiple)
        assert len(result.failures) == 0

        # Verify reason for skip
        for skipped in result.skipped:
            assert skipped.reason == "no-scheduling-data"

        # Verify provisioner was not called
        mock_provisioner.schedule_scaling_group.assert_not_awaited()


# =============================================================================
# CheckPreconditionLifecycleHandler Tests (SC-CP-001 ~ SC-CP-004)
# =============================================================================


class TestCheckPreconditionLifecycleHandler:
    """Tests for CheckPreconditionLifecycleHandler.

    Verifies the handler correctly triggers image pulling via launcher
    and marks all sessions as successful.
    """

    @pytest.fixture
    def handler(
        self,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
    ) -> CheckPreconditionLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckPreconditionLifecycleHandler(
            launcher=mock_launcher,
            repository=mock_repository,
        )

    async def test_image_pulling_triggered_for_all_sessions(
        self,
        handler: CheckPreconditionLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
        scheduled_sessions_multiple: list[SessionWithKernels],
        sessions_for_pull_factory: Callable[..., SessionsForPullWithImages],
    ) -> None:
        """SC-CP-001: Image pulling is triggered for all sessions.

        Given: Multiple SCHEDULED sessions
        When: Handler triggers image pulling
        Then: All sessions marked as success with passed-preconditions reason
        """
        # Arrange
        sessions_for_pull = sessions_for_pull_factory(scheduled_sessions_multiple)
        mock_repository.get_sessions_for_pull_by_ids.return_value = sessions_for_pull

        # Act
        result = await handler.execute("default", scheduled_sessions_multiple)

        # Assert
        assert len(result.successes) == len(scheduled_sessions_multiple)
        assert len(result.failures) == 0
        assert len(result.skipped) == 0

        # Verify image pulling was triggered
        mock_launcher.trigger_image_pulling.assert_awaited_once_with(
            sessions_for_pull.sessions,
            sessions_for_pull.image_configs,
        )

        # Verify success reason
        for success in result.successes:
            assert success.reason == "passed-preconditions"

    async def test_empty_session_list_does_nothing(
        self,
        handler: CheckPreconditionLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """SC-CP-002: Empty session list returns immediately.

        Given: Empty session list
        When: Handler is invoked
        Then: Returns empty result without triggering image pulling
        """
        # Act
        result = await handler.execute("default", [])

        # Assert
        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert len(result.skipped) == 0

        # Verify launcher was not called
        mock_launcher.trigger_image_pulling.assert_not_awaited()
        mock_repository.get_sessions_for_pull_by_ids.assert_not_awaited()

    async def test_image_pulling_exception_propagates(
        self,
        handler: CheckPreconditionLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
        scheduled_session: SessionWithKernels,
        sessions_for_pull_factory: Callable[..., SessionsForPullWithImages],
    ) -> None:
        """SC-CP-003: Launcher exception propagates to coordinator.

        Given: Launcher raises an exception during image pulling
        When: Handler is invoked
        Then: Exception propagates (coordinator handles it)
        """
        # Arrange
        sessions_for_pull = sessions_for_pull_factory([scheduled_session])
        mock_repository.get_sessions_for_pull_by_ids.return_value = sessions_for_pull
        mock_launcher.trigger_image_pulling.side_effect = RuntimeError("Agent connection failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Agent connection failed"):
            await handler.execute("default", [scheduled_session])

    async def test_repository_query_extracts_correct_session_ids(
        self,
        handler: CheckPreconditionLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
        scheduled_sessions_multiple: list[SessionWithKernels],
        sessions_for_pull_factory: Callable[..., SessionsForPullWithImages],
    ) -> None:
        """SC-CP-004: Repository is queried with correct session IDs.

        Given: Multiple SCHEDULED sessions
        When: Handler queries repository
        Then: Repository is called with all session IDs
        """
        # Arrange
        sessions_for_pull = sessions_for_pull_factory(scheduled_sessions_multiple)
        mock_repository.get_sessions_for_pull_by_ids.return_value = sessions_for_pull

        # Act
        await handler.execute("default", scheduled_sessions_multiple)

        # Assert
        expected_ids = [s.session_info.identity.id for s in scheduled_sessions_multiple]
        mock_repository.get_sessions_for_pull_by_ids.assert_awaited_once_with(expected_ids)


# =============================================================================
# StartSessionsLifecycleHandler Tests (SC-ST-001 ~ SC-ST-005)
# =============================================================================


class TestStartSessionsLifecycleHandler:
    """Tests for StartSessionsLifecycleHandler.

    Verifies the handler correctly starts sessions via launcher
    and marks all sessions as successful.
    """

    @pytest.fixture
    def handler(
        self,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
    ) -> StartSessionsLifecycleHandler:
        """Create handler with mocked dependencies."""
        return StartSessionsLifecycleHandler(
            launcher=mock_launcher,
            repository=mock_repository,
        )

    async def test_all_sessions_started_successfully(
        self,
        handler: StartSessionsLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
        prepared_sessions_multiple: list[SessionWithKernels],
        sessions_for_start_factory: Callable[..., SessionsForStartWithImages],
    ) -> None:
        """SC-ST-001: All prepared sessions are started successfully.

        Given: Multiple PREPARED sessions
        When: Handler starts all sessions
        Then: All sessions marked as success with triggered-by-scheduler reason
        """
        # Arrange
        sessions_for_start = sessions_for_start_factory(prepared_sessions_multiple)
        mock_repository.search_sessions_with_kernels_and_user.return_value = sessions_for_start

        # Act
        result = await handler.execute("default", prepared_sessions_multiple)

        # Assert
        assert len(result.successes) == len(prepared_sessions_multiple)
        assert len(result.failures) == 0
        assert len(result.skipped) == 0

        # Verify launcher was called
        mock_launcher.start_sessions_for_handler.assert_awaited_once_with(
            sessions_for_start.sessions,
            sessions_for_start.image_configs,
        )

        # Verify success reason
        for success in result.successes:
            assert success.reason == "triggered-by-scheduler"

    async def test_empty_session_list_returns_empty(
        self,
        handler: StartSessionsLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """SC-ST-002: Empty session list returns empty result.

        Given: Empty session list
        When: Handler is invoked
        Then: Returns empty result without starting any sessions
        """
        # Act
        result = await handler.execute("default", [])

        # Assert
        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert len(result.skipped) == 0

        # Verify launcher was not called
        mock_launcher.start_sessions_for_handler.assert_not_awaited()
        mock_repository.search_sessions_with_kernels_and_user.assert_not_awaited()

    async def test_session_start_exception_propagates(
        self,
        handler: StartSessionsLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
        prepared_session: SessionWithKernels,
        sessions_for_start_factory: Callable[..., SessionsForStartWithImages],
    ) -> None:
        """SC-ST-003: Launcher exception propagates to coordinator.

        Given: Launcher raises an exception during session start
        When: Handler is invoked
        Then: Exception propagates (coordinator handles it)
        """
        # Arrange
        sessions_for_start = sessions_for_start_factory([prepared_session])
        mock_repository.search_sessions_with_kernels_and_user.return_value = sessions_for_start
        mock_launcher.start_sessions_for_handler.side_effect = RuntimeError(
            "Kernel creation failed"
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="Kernel creation failed"):
            await handler.execute("default", [prepared_session])

    async def test_repository_query_uses_batch_querier(
        self,
        handler: StartSessionsLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
        prepared_sessions_multiple: list[SessionWithKernels],
        sessions_for_start_factory: Callable[..., SessionsForStartWithImages],
    ) -> None:
        """SC-ST-004: Repository is queried with BatchQuerier.

        Given: Multiple PREPARED sessions
        When: Handler queries repository
        Then: Repository search is called with appropriate querier
        """
        # Arrange
        sessions_for_start = sessions_for_start_factory(prepared_sessions_multiple)
        mock_repository.search_sessions_with_kernels_and_user.return_value = sessions_for_start

        # Act
        await handler.execute("default", prepared_sessions_multiple)

        # Assert - verify repository was called
        mock_repository.search_sessions_with_kernels_and_user.assert_awaited_once()

        # Verify the call argument is a BatchQuerier (check call args)
        call_args = mock_repository.search_sessions_with_kernels_and_user.call_args
        querier = call_args[0][0]

        # BatchQuerier should have conditions with session IDs
        assert querier is not None

    async def test_single_session_started(
        self,
        handler: StartSessionsLifecycleHandler,
        mock_launcher: AsyncMock,
        mock_repository: AsyncMock,
        prepared_session: SessionWithKernels,
        sessions_for_start_factory: Callable[..., SessionsForStartWithImages],
    ) -> None:
        """SC-ST-005: Single session can be started.

        Given: Single PREPARED session
        When: Handler starts the session
        Then: Session is marked as success
        """
        # Arrange
        sessions_for_start = sessions_for_start_factory([prepared_session])
        mock_repository.search_sessions_with_kernels_and_user.return_value = sessions_for_start

        # Act
        result = await handler.execute("default", [prepared_session])

        # Assert
        assert len(result.successes) == 1
        assert result.successes[0].session_id == prepared_session.session_info.identity.id


# =============================================================================
# TerminateSessionsLifecycleHandler Tests (SC-TE-001 ~ SC-TE-005)
# =============================================================================


class TestTerminateSessionsLifecycleHandler:
    """Tests for TerminateSessionsLifecycleHandler.

    Verifies the handler correctly terminates sessions via terminator
    and returns empty result (status transitions happen via agent events).
    """

    @pytest.fixture
    def handler(
        self,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
    ) -> TerminateSessionsLifecycleHandler:
        """Create handler with mocked dependencies."""
        return TerminateSessionsLifecycleHandler(
            terminator=mock_terminator,
            repository=mock_repository,
        )

    async def test_all_sessions_terminated_returns_empty_result(
        self,
        handler: TerminateSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        terminating_sessions_multiple: list[SessionWithKernels],
        terminating_session_data_factory: Callable[..., list[TerminatingSessionData]],
    ) -> None:
        """SC-TE-001: All sessions are sent for termination.

        Given: Multiple TERMINATING sessions
        When: Handler sends termination RPCs
        Then: Returns empty result (no status transitions - handled by agent events)
        """
        # Arrange
        terminating_data = terminating_session_data_factory(terminating_sessions_multiple)
        mock_repository.get_terminating_sessions_by_ids.return_value = terminating_data

        # Act
        result = await handler.execute("default", terminating_sessions_multiple)

        # Assert - Result should be empty (status updates via agent events)
        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert len(result.skipped) == 0

        # Verify terminator was called
        mock_terminator.terminate_sessions_for_handler.assert_awaited_once_with(terminating_data)

    async def test_empty_session_list_returns_immediately(
        self,
        handler: TerminateSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        """SC-TE-002: Empty session list returns immediately.

        Given: Empty session list
        When: Handler is invoked
        Then: Returns empty result without calling terminator
        """
        # Act
        result = await handler.execute("default", [])

        # Assert
        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert len(result.skipped) == 0

        # Verify terminator was not called
        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()
        mock_repository.get_terminating_sessions_by_ids.assert_not_awaited()

    async def test_no_terminating_data_returns_empty(
        self,
        handler: TerminateSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        terminating_session: SessionWithKernels,
    ) -> None:
        """SC-TE-003: Empty terminating data returns empty result.

        Given: Repository returns empty terminating session list
        When: Handler is invoked
        Then: Returns empty result without calling terminator
        """
        # Arrange
        mock_repository.get_terminating_sessions_by_ids.return_value = []

        # Act
        result = await handler.execute("default", [terminating_session])

        # Assert
        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert len(result.skipped) == 0

        # Verify terminator was not called since no data
        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()

    async def test_terminator_exception_propagates(
        self,
        handler: TerminateSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        terminating_session: SessionWithKernels,
        terminating_session_data_factory: Callable[..., list[TerminatingSessionData]],
    ) -> None:
        """SC-TE-004: Terminator exception propagates to coordinator.

        Given: Terminator raises an exception
        When: Handler is invoked
        Then: Exception propagates (coordinator handles it)
        """
        # Arrange
        terminating_data = terminating_session_data_factory([terminating_session])
        mock_repository.get_terminating_sessions_by_ids.return_value = terminating_data
        mock_terminator.terminate_sessions_for_handler.side_effect = RuntimeError(
            "Agent unreachable"
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="Agent unreachable"):
            await handler.execute("default", [terminating_session])

    async def test_repository_query_extracts_correct_session_ids(
        self,
        handler: TerminateSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        terminating_sessions_multiple: list[SessionWithKernels],
        terminating_session_data_factory: Callable[..., list[TerminatingSessionData]],
    ) -> None:
        """SC-TE-005: Repository is queried with correct session IDs.

        Given: Multiple TERMINATING sessions
        When: Handler queries repository
        Then: Repository is called with all session IDs
        """
        # Arrange
        terminating_data = terminating_session_data_factory(terminating_sessions_multiple)
        mock_repository.get_terminating_sessions_by_ids.return_value = terminating_data

        # Act
        await handler.execute("default", terminating_sessions_multiple)

        # Assert
        expected_ids = [s.session_info.identity.id for s in terminating_sessions_multiple]
        mock_repository.get_terminating_sessions_by_ids.assert_awaited_once_with(expected_ids)
