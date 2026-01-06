"""
Tests for ScheduleCoordinator.
Tests the coordinator that manages scheduling operations and termination marking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import AccessKey, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler import MarkTerminatingResult
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    pass


@pytest.fixture
def mock_scheduler() -> MagicMock:
    """Mock Scheduler for testing."""
    mock = MagicMock(spec=Scheduler)
    # Create AsyncMock with support for side_effect
    mock.mark_sessions_for_termination = AsyncMock()
    mock.terminate_sessions = AsyncMock()
    # Add _repository attribute for KernelStateEngine initialization
    mock._repository = MagicMock()
    # Add _hook_registry for lifecycle handler initialization
    mock_hook = MagicMock()
    mock_hook.on_transition_to_running = AsyncMock(return_value=None)
    mock_hook.on_transition_to_terminated = AsyncMock(return_value=None)
    mock_hook_registry = MagicMock()
    mock_hook_registry.get_hook = MagicMock(return_value=mock_hook)
    mock._hook_registry = mock_hook_registry
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
    return MagicMock(spec=EventProducer)


@pytest.fixture
def mock_scheduler_dispatcher():
    """Mock SchedulerDispatcher for testing."""
    return MagicMock(spec=SchedulerDispatcher)


@pytest.fixture
def mock_scheduling_controller():
    """Mock SchedulingController for testing."""
    mock = MagicMock(spec=SchedulingController)
    mock.mark_schedule_needed = AsyncMock()
    mock.mark_sessions_for_termination = AsyncMock()
    return mock


@pytest.fixture
def mock_lock_factory():
    """Mock DistributedLockFactory."""
    from ai.backend.manager.types import DistributedLockFactory

    mock = MagicMock(spec=DistributedLockFactory)
    # Make it return an async context manager
    lock_mock = AsyncMock()
    lock_mock.__aenter__ = AsyncMock(return_value=None)
    lock_mock.__aexit__ = AsyncMock(return_value=None)
    mock.return_value = lock_mock
    return mock


@pytest.fixture
def mock_config_provider():
    """Mock ManagerConfigProvider."""
    from ai.backend.manager.config.provider import ManagerConfigProvider

    mock = MagicMock(spec=ManagerConfigProvider)
    # Set up config.manager.session_schedule_lock_lifetime
    mock.config.manager.session_schedule_lock_lifetime = 60.0
    return mock


@pytest.fixture
def schedule_coordinator(
    mock_scheduler,
    mock_valkey_schedule,
    mock_event_producer,
    mock_scheduler_dispatcher,
    mock_scheduling_controller,
    mock_lock_factory,
    mock_config_provider,
):
    """Create ScheduleCoordinator with mocked dependencies."""
    return ScheduleCoordinator(
        valkey_schedule=mock_valkey_schedule,
        scheduler=mock_scheduler,
        scheduling_controller=mock_scheduling_controller,
        event_producer=mock_event_producer,
        lock_factory=mock_lock_factory,
        config_provider=mock_config_provider,
    )


class TestScheduleCoordinator:
    """Test cases for ScheduleCoordinator."""

    async def test_process_if_needed(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule,
    ):
        """Test process_if_needed method."""
        # Create a proper ScheduleResult instance
        mock_result = ScheduleResult()

        # Setup mock handler
        mock_handler = MagicMock()
        mock_handler.name = MagicMock(return_value="schedule")
        mock_handler.lock_id = LockID.LOCKID_SCHEDULE
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_handler.post_process = AsyncMock()

        # Directly set handlers
        schedule_coordinator._schedule_handlers = {ScheduleType.SCHEDULE: mock_handler}

        # Test that process_if_needed can be called
        await schedule_coordinator.process_if_needed(ScheduleType.SCHEDULE)

        # Verify handler was called
        mock_handler.execute.assert_called_once()

    async def test_process_schedule(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule,
    ):
        """Test process_schedule method."""
        # Create a proper ScheduleResult instance
        mock_result = ScheduleResult()

        # Setup mock handler
        mock_handler = MagicMock()
        mock_handler.name = MagicMock(return_value="start")
        mock_handler.lock_id = LockID.LOCKID_START
        mock_handler.execute = AsyncMock(return_value=mock_result)
        mock_handler.post_process = AsyncMock()

        # Directly set handlers
        schedule_coordinator._schedule_handlers = {ScheduleType.START: mock_handler}

        # Test that process_schedule can be called
        await schedule_coordinator.process_schedule(ScheduleType.START)

        # Verify handler was called
        mock_handler.execute.assert_called_once()

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

    async def test_mark_schedule_needed_direct(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller,
        mock_valkey_schedule,
    ):
        """Test direct scheduling request via controller."""
        # Execute - request different schedule types via controller
        await mock_scheduling_controller.mark_schedule_needed(ScheduleType.SCHEDULE)
        await mock_scheduling_controller.mark_schedule_needed(ScheduleType.START)
        await mock_scheduling_controller.mark_schedule_needed(ScheduleType.TERMINATE)

        # Verify controller methods were called
        assert mock_scheduling_controller.mark_schedule_needed.call_count == 3
        calls = mock_scheduling_controller.mark_schedule_needed.call_args_list
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


def create_handler_session_data(
    session_id: SessionId,
    scaling_group: str = "default",
) -> HandlerSessionData:
    """Helper to create test HandlerSessionData."""
    return HandlerSessionData(
        session_id=session_id,
        creation_id=str(uuid4()),
        access_key=AccessKey("test-key"),
        status=SessionStatus.PREPARING,
        scaling_group=scaling_group,
        session_type=SessionTypes.INTERACTIVE,
        kernels=[],
    )


class TestProcessLifecycleSchedule:
    """Test cases for process_lifecycle_schedule method."""

    @pytest.fixture
    def mock_lifecycle_handler(self) -> MagicMock:
        """Create mock lifecycle handler."""
        mock = MagicMock(spec=SessionLifecycleHandler)
        mock.name = MagicMock(return_value="test-handler")
        mock.lock_id = None
        mock.target_statuses = MagicMock(return_value=[SessionStatus.PREPARING])
        mock.target_kernel_statuses = MagicMock(return_value=[KernelStatus.PREPARED])
        mock.success_status = MagicMock(return_value=SessionStatus.PREPARED)
        mock.failure_status = MagicMock(return_value=None)
        mock.stale_status = MagicMock(return_value=None)
        mock.execute = AsyncMock(return_value=SessionExecutionResult())
        mock.post_process = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mock repository."""
        mock = MagicMock()
        mock.get_schedulable_scaling_groups = AsyncMock(return_value=["default"])
        mock.get_sessions_for_handler = AsyncMock(return_value=[])
        mock.update_sessions_status_bulk = AsyncMock(return_value=0)
        return mock

    async def test_process_lifecycle_schedule_no_handler(
        self,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        """Test process_lifecycle_schedule returns False when no handler exists."""
        # Clear lifecycle handlers
        schedule_coordinator._lifecycle_handlers = {}

        result = await schedule_coordinator.process_lifecycle_schedule(
            ScheduleType.CHECK_PULLING_PROGRESS
        )

        assert result is False

    async def test_process_lifecycle_schedule_iterates_scaling_groups(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test process_lifecycle_schedule iterates over scaling groups."""
        # Setup
        schedule_coordinator._lifecycle_handlers = {
            ScheduleType.CHECK_PULLING_PROGRESS: mock_lifecycle_handler
        }
        schedule_coordinator._repository = mock_repository

        # Multiple scaling groups
        mock_repository.get_schedulable_scaling_groups.return_value = ["sg1", "sg2", "sg3"]

        # Return sessions for each scaling group
        session1 = create_handler_session_data(SessionId(uuid4()), "sg1")
        session2 = create_handler_session_data(SessionId(uuid4()), "sg2")
        session3 = create_handler_session_data(SessionId(uuid4()), "sg3")

        mock_repository.get_sessions_for_handler.side_effect = [
            [session1],
            [session2],
            [session3],
        ]

        # Handler returns success for each
        mock_lifecycle_handler.execute.return_value = SessionExecutionResult(
            successes=[session1.session_id]
        )

        result = await schedule_coordinator.process_lifecycle_schedule(
            ScheduleType.CHECK_PULLING_PROGRESS
        )

        assert result is True
        assert mock_repository.get_schedulable_scaling_groups.call_count == 1
        assert mock_repository.get_sessions_for_handler.call_count == 3
        assert mock_lifecycle_handler.execute.call_count == 3

    async def test_process_lifecycle_schedule_skips_empty_sessions(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test process_lifecycle_schedule skips scaling groups with no sessions."""
        # Setup
        schedule_coordinator._lifecycle_handlers = {
            ScheduleType.CHECK_PULLING_PROGRESS: mock_lifecycle_handler
        }
        schedule_coordinator._repository = mock_repository

        mock_repository.get_schedulable_scaling_groups.return_value = ["sg1", "sg2"]
        mock_repository.get_sessions_for_handler.side_effect = [
            [],  # sg1 has no sessions
            [create_handler_session_data(SessionId(uuid4()), "sg2")],  # sg2 has sessions
        ]

        mock_lifecycle_handler.execute.return_value = SessionExecutionResult()

        await schedule_coordinator.process_lifecycle_schedule(ScheduleType.CHECK_PULLING_PROGRESS)

        # Handler execute should only be called once (for sg2)
        assert mock_lifecycle_handler.execute.call_count == 1

    async def test_handle_status_transitions_success(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test _handle_status_transitions applies success status."""
        # Setup
        schedule_coordinator._repository = mock_repository
        session_id = SessionId(uuid4())

        result = SessionExecutionResult(successes=[session_id])

        # Execute
        await schedule_coordinator._handle_status_transitions(mock_lifecycle_handler, result)

        # Verify success status update was called
        mock_repository.update_sessions_status_bulk.assert_called_once_with(
            [session_id],
            [SessionStatus.PREPARING],
            SessionStatus.PREPARED,
        )

    async def test_handle_status_transitions_failure(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test _handle_status_transitions applies failure status."""
        # Setup
        schedule_coordinator._repository = mock_repository
        session_id = SessionId(uuid4())
        mock_lifecycle_handler.failure_status.return_value = SessionStatus.CANCELLED

        from ai.backend.manager.sokovan.scheduler.results import SessionExecutionError

        result = SessionExecutionResult(
            failures=[
                SessionExecutionError(
                    session_id=session_id,
                    reason="test",
                    error_detail="test error",
                )
            ]
        )

        # Execute
        await schedule_coordinator._handle_status_transitions(mock_lifecycle_handler, result)

        # Verify failure status update was called
        mock_repository.update_sessions_status_bulk.assert_called_once_with(
            [session_id],
            [SessionStatus.PREPARING],
            SessionStatus.CANCELLED,
        )

    async def test_handle_status_transitions_stale(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test _handle_status_transitions applies stale status."""
        # Setup
        schedule_coordinator._repository = mock_repository
        session_id = SessionId(uuid4())
        mock_lifecycle_handler.stale_status.return_value = SessionStatus.TERMINATING
        mock_lifecycle_handler.success_status.return_value = None

        result = SessionExecutionResult(stales=[session_id])

        # Execute
        await schedule_coordinator._handle_status_transitions(mock_lifecycle_handler, result)

        # Verify stale status update was called
        mock_repository.update_sessions_status_bulk.assert_called_once_with(
            [session_id],
            [SessionStatus.PREPARING],
            SessionStatus.TERMINATING,
        )

    async def test_handle_status_transitions_no_update_when_status_none(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test _handle_status_transitions doesn't update when status is None."""
        # Setup
        schedule_coordinator._repository = mock_repository
        session_id = SessionId(uuid4())

        # All status methods return None
        mock_lifecycle_handler.success_status.return_value = None
        mock_lifecycle_handler.failure_status.return_value = None
        mock_lifecycle_handler.stale_status.return_value = None

        result = SessionExecutionResult(
            successes=[session_id],
            stales=[session_id],
        )

        # Execute
        await schedule_coordinator._handle_status_transitions(mock_lifecycle_handler, result)

        # Verify no updates were made
        mock_repository.update_sessions_status_bulk.assert_not_called()

    async def test_process_lifecycle_schedule_calls_post_process(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test process_lifecycle_schedule calls post_process when needed."""
        # Setup
        schedule_coordinator._lifecycle_handlers = {
            ScheduleType.CHECK_PULLING_PROGRESS: mock_lifecycle_handler
        }
        schedule_coordinator._repository = mock_repository

        session_id = SessionId(uuid4())
        session = create_handler_session_data(session_id)
        mock_repository.get_sessions_for_handler.return_value = [session]

        from ai.backend.manager.sokovan.scheduler.results import ScheduledSessionData

        # Handler returns result that needs post-processing
        mock_lifecycle_handler.execute.return_value = SessionExecutionResult(
            successes=[session_id],
            scheduled_data=[
                ScheduledSessionData(
                    session_id=session_id,
                    creation_id="test",
                    access_key=AccessKey("test"),
                    reason="test",
                )
            ],
        )

        await schedule_coordinator.process_lifecycle_schedule(ScheduleType.CHECK_PULLING_PROGRESS)

        # Verify post_process was called
        mock_lifecycle_handler.post_process.assert_called_once()

    async def test_process_lifecycle_schedule_merges_results(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test process_lifecycle_schedule merges results from multiple scaling groups."""
        # Setup
        schedule_coordinator._lifecycle_handlers = {
            ScheduleType.CHECK_PULLING_PROGRESS: mock_lifecycle_handler
        }
        schedule_coordinator._repository = mock_repository

        mock_repository.get_schedulable_scaling_groups.return_value = ["sg1", "sg2"]

        session1 = create_handler_session_data(SessionId(uuid4()), "sg1")
        session2 = create_handler_session_data(SessionId(uuid4()), "sg2")

        mock_repository.get_sessions_for_handler.side_effect = [
            [session1],
            [session2],
        ]

        # Each scaling group returns one success
        mock_lifecycle_handler.execute.side_effect = [
            SessionExecutionResult(successes=[session1.session_id]),
            SessionExecutionResult(successes=[session2.session_id]),
        ]

        await schedule_coordinator.process_lifecycle_schedule(ScheduleType.CHECK_PULLING_PROGRESS)

        # Verify update was called with merged results (2 sessions)
        calls = mock_repository.update_sessions_status_bulk.call_args_list
        assert len(calls) == 1
        # The merged result should contain both session IDs
        updated_session_ids = calls[0][0][0]
        assert len(updated_session_ids) == 2
