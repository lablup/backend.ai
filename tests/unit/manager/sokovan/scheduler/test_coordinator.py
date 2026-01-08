"""
Tests for ScheduleCoordinator.
Tests the coordinator that manages scheduling operations and termination marking.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call, patch
from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.kernel.anycast import (
    KernelCancelledAnycastEvent,
    KernelCreatingAnycastEvent,
    KernelHeartbeatEvent,
    KernelPreparingAnycastEvent,
    KernelPullingAnycastEvent,
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
)
from ai.backend.common.types import AccessKey, AgentId, KernelId, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler import MarkTerminatingResult
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import (
    ScheduleCoordinator,
    SchedulerTaskSpec,
)
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import SchedulerComponents
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


@pytest.fixture
def mock_scheduler_components() -> MagicMock:
    """Mock SchedulerComponents for testing."""
    mock = MagicMock(spec=SchedulerComponents)
    # Add repository attribute for KernelStateEngine initialization
    mock.repository = MagicMock()
    # Add config_provider attribute
    mock_config_provider = MagicMock()
    mock_config_provider.config.manager.session_schedule_lock_lifetime = 60.0
    mock.config_provider = mock_config_provider
    # Add hook_registry for lifecycle handler initialization
    mock_hook = MagicMock()
    mock_hook.on_transition_to_running = AsyncMock(return_value=None)
    mock_hook.on_transition_to_terminated = AsyncMock(return_value=None)
    mock_hook_registry = MagicMock()
    mock_hook_registry.get_hook = MagicMock(return_value=mock_hook)
    mock.hook_registry = mock_hook_registry
    # Add other components
    mock.launcher = MagicMock()
    mock.terminator = MagicMock()
    mock.provisioner = MagicMock()
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
    mock_scheduler_components,
    mock_valkey_schedule,
    mock_event_producer,
    mock_scheduler_dispatcher,
    mock_scheduling_controller,
    mock_lock_factory,
):
    """Create ScheduleCoordinator with mocked dependencies."""
    return ScheduleCoordinator(
        valkey_schedule=mock_valkey_schedule,
        components=mock_scheduler_components,
        scheduling_controller=mock_scheduling_controller,
        event_producer=mock_event_producer,
        lock_factory=mock_lock_factory,
    )


class TestScheduleCoordinator:
    """Test cases for ScheduleCoordinator."""

    async def test_process_if_needed(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule,
    ) -> None:
        """Test process_if_needed method."""
        # Setup mock handler
        mock_handler = MagicMock(spec=SessionLifecycleHandler)
        mock_handler.name = MagicMock(return_value="schedule")
        mock_handler.lock_id = None
        mock_handler.target_statuses = MagicMock(return_value=[SessionStatus.PENDING])
        mock_handler.target_kernel_statuses = MagicMock(return_value=[])
        mock_handler.success_status = MagicMock(return_value=SessionStatus.SCHEDULED)
        mock_handler.failure_status = MagicMock(return_value=None)
        mock_handler.stale_status = MagicMock(return_value=None)
        mock_handler.execute = AsyncMock(return_value=SessionExecutionResult())
        mock_handler.post_process = AsyncMock()

        # Setup repository mock with AsyncMock methods
        mock_repository = MagicMock()
        mock_repository.get_schedulable_scaling_groups = AsyncMock(return_value=["default"])
        mock_repository.get_sessions_for_handler = AsyncMock(return_value=[])
        mock_repository.update_sessions_status_bulk = AsyncMock(return_value=0)

        # Setup valkey_schedule to return True (mark exists)
        mock_valkey_schedule.load_and_delete_schedule_mark = AsyncMock(return_value=True)

        # Set handlers and repository
        schedule_coordinator._lifecycle_handlers = {ScheduleType.SCHEDULE: mock_handler}
        schedule_coordinator._repository = mock_repository

        # Test that process_if_needed calls valkey first, then processes if mark exists
        result = await schedule_coordinator.process_if_needed(ScheduleType.SCHEDULE)

        # Verify valkey was checked
        mock_valkey_schedule.load_and_delete_schedule_mark.assert_called_once_with("schedule")
        assert result is True

    async def test_process_schedule(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule,
    ) -> None:
        """Test process_schedule method."""
        # Setup mock handler
        mock_handler = MagicMock(spec=SessionLifecycleHandler)
        mock_handler.name = MagicMock(return_value="start")
        mock_handler.lock_id = None
        mock_handler.target_statuses = MagicMock(return_value=[SessionStatus.PREPARED])
        mock_handler.target_kernel_statuses = MagicMock(return_value=[])
        mock_handler.success_status = MagicMock(return_value=SessionStatus.CREATING)
        mock_handler.failure_status = MagicMock(return_value=None)
        mock_handler.stale_status = MagicMock(return_value=None)
        mock_handler.execute = AsyncMock(return_value=SessionExecutionResult())
        mock_handler.post_process = AsyncMock()

        # Setup repository mock with AsyncMock methods
        mock_repository = MagicMock()
        mock_repository.get_schedulable_scaling_groups = AsyncMock(return_value=["default"])
        mock_repository.get_sessions_for_handler = AsyncMock(return_value=[])
        mock_repository.update_sessions_status_bulk = AsyncMock(return_value=0)

        # Set handlers and repository
        schedule_coordinator._lifecycle_handlers = {ScheduleType.START: mock_handler}
        schedule_coordinator._repository = mock_repository

        # Test that process_schedule can be called
        result = await schedule_coordinator.process_schedule(ScheduleType.START)

        # Verify processing occurred
        assert result is True
        mock_repository.get_schedulable_scaling_groups.assert_called_once()

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


class TestKernelEventHandlers:
    """Test cases for kernel event handler methods."""

    @pytest.fixture
    def mock_kernel_state_engine(self) -> MagicMock:
        """Create mock KernelStateEngine."""
        mock = MagicMock()
        mock.mark_kernel_pulling = AsyncMock(return_value=True)
        mock.mark_kernel_creating = AsyncMock(return_value=True)
        mock.mark_kernel_running = AsyncMock(return_value=True)
        mock.mark_kernel_preparing = AsyncMock(return_value=True)
        mock.mark_kernel_cancelled = AsyncMock(return_value=True)
        mock.mark_kernel_terminated = AsyncMock(return_value=True)
        mock.update_kernel_heartbeat = AsyncMock(return_value=True)
        mock.update_kernels_to_pulling_for_image = AsyncMock()
        mock.update_kernels_to_prepared_for_image = AsyncMock(return_value=5)
        mock.cancel_kernels_for_failed_image = AsyncMock()
        return mock

    async def test_handle_kernel_pulling_success(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller: MagicMock,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_pulling marks kernel and requests scheduling."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine
        schedule_coordinator._scheduling_controller = mock_scheduling_controller

        kernel_id = KernelId(uuid4())
        event = MagicMock(spec=KernelPullingAnycastEvent)
        event.kernel_id = kernel_id
        event.reason = "Image pulling started"

        # Execute
        result = await schedule_coordinator.handle_kernel_pulling(event)

        # Verify
        assert result is True
        mock_kernel_state_engine.mark_kernel_pulling.assert_called_once_with(
            kernel_id, "Image pulling started"
        )
        mock_scheduling_controller.mark_scheduling_needed.assert_called_once_with(
            ScheduleType.CHECK_PULLING_PROGRESS
        )

    async def test_handle_kernel_pulling_not_marked(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller: MagicMock,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_pulling does not request scheduling when mark fails."""
        # Setup
        mock_kernel_state_engine.mark_kernel_pulling.return_value = False
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine
        schedule_coordinator._scheduling_controller = mock_scheduling_controller

        event = MagicMock(spec=KernelPullingAnycastEvent)
        event.kernel_id = KernelId(uuid4())
        event.reason = "test"

        # Execute
        result = await schedule_coordinator.handle_kernel_pulling(event)

        # Verify
        assert result is False
        mock_scheduling_controller.mark_scheduling_needed.assert_not_called()

    async def test_handle_kernel_creating(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_creating marks kernel."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine

        kernel_id = KernelId(uuid4())
        event = MagicMock(spec=KernelCreatingAnycastEvent)
        event.kernel_id = kernel_id
        event.reason = "Container creating"

        # Execute
        result = await schedule_coordinator.handle_kernel_creating(event)

        # Verify
        assert result is True
        mock_kernel_state_engine.mark_kernel_creating.assert_called_once_with(
            kernel_id, "Container creating"
        )

    async def test_handle_kernel_running_success(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller: MagicMock,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_running marks kernel and requests scheduling."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine
        schedule_coordinator._scheduling_controller = mock_scheduling_controller

        kernel_id = KernelId(uuid4())
        event = MagicMock(spec=KernelStartedAnycastEvent)
        event.kernel_id = kernel_id
        event.reason = "Container started"
        event.creation_info = {}

        # Execute
        result = await schedule_coordinator.handle_kernel_running(event)

        # Verify
        assert result is True
        mock_kernel_state_engine.mark_kernel_running.assert_called_once()
        mock_scheduling_controller.mark_scheduling_needed.assert_called_once_with(
            ScheduleType.CHECK_CREATING_PROGRESS
        )

    async def test_handle_kernel_preparing_success(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller: MagicMock,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_preparing marks kernel and requests scheduling."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine
        schedule_coordinator._scheduling_controller = mock_scheduling_controller

        kernel_id = KernelId(uuid4())
        event = MagicMock(spec=KernelPreparingAnycastEvent)
        event.kernel_id = kernel_id

        # Execute
        result = await schedule_coordinator.handle_kernel_preparing(event)

        # Verify
        assert result is True
        mock_kernel_state_engine.mark_kernel_preparing.assert_called_once_with(kernel_id)
        mock_scheduling_controller.mark_scheduling_needed.assert_called_once_with(
            ScheduleType.CHECK_PRECONDITION
        )

    async def test_handle_kernel_cancelled(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_cancelled marks kernel."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine

        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        event = MagicMock(spec=KernelCancelledAnycastEvent)
        event.kernel_id = kernel_id
        event.session_id = session_id
        event.reason = "User cancelled"

        # Execute
        result = await schedule_coordinator.handle_kernel_cancelled(event)

        # Verify
        assert result is True
        mock_kernel_state_engine.mark_kernel_cancelled.assert_called_once_with(
            kernel_id, session_id, "User cancelled"
        )

    async def test_handle_kernel_terminated_success(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller: MagicMock,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_terminated marks kernel and requests scheduling."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine
        schedule_coordinator._scheduling_controller = mock_scheduling_controller

        kernel_id = KernelId(uuid4())
        event = MagicMock(spec=KernelTerminatedAnycastEvent)
        event.kernel_id = kernel_id
        event.reason = "Normal exit"
        event.exit_code = 0

        # Execute
        result = await schedule_coordinator.handle_kernel_terminated(event)

        # Verify
        assert result is True
        mock_kernel_state_engine.mark_kernel_terminated.assert_called_once_with(
            kernel_id, "Normal exit", 0
        )
        # Should request both CHECK_RUNNING_SESSION_TERMINATION and CHECK_TERMINATING_PROGRESS
        assert mock_scheduling_controller.mark_scheduling_needed.call_count == 2
        calls = mock_scheduling_controller.mark_scheduling_needed.call_args_list
        assert calls[0] == call(ScheduleType.CHECK_RUNNING_SESSION_TERMINATION)
        assert calls[1] == call(ScheduleType.CHECK_TERMINATING_PROGRESS)

    async def test_handle_kernel_heartbeat(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test handle_kernel_heartbeat updates heartbeat."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine

        kernel_id = KernelId(uuid4())
        event = MagicMock(spec=KernelHeartbeatEvent)
        event.kernel_id = kernel_id

        # Execute
        result = await schedule_coordinator.handle_kernel_heartbeat(event)

        # Verify
        assert result is True
        mock_kernel_state_engine.update_kernel_heartbeat.assert_called_once_with(kernel_id)


class TestImageUpdateMethods:
    """Test cases for image-related kernel state update methods."""

    @pytest.fixture
    def mock_kernel_state_engine(self) -> MagicMock:
        """Create mock KernelStateEngine."""
        mock = MagicMock()
        mock.update_kernels_to_pulling_for_image = AsyncMock()
        mock.update_kernels_to_prepared_for_image = AsyncMock(return_value=5)
        mock.cancel_kernels_for_failed_image = AsyncMock()
        return mock

    async def test_update_kernels_to_pulling_for_image(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test update_kernels_to_pulling_for_image delegates to kernel state engine."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine

        agent_id = AgentId("agent-1")
        image = "python:3.9"
        image_ref = "registry.example.com/python:3.9"

        # Execute
        await schedule_coordinator.update_kernels_to_pulling_for_image(
            agent_id, image, image_ref
        )

        # Verify
        mock_kernel_state_engine.update_kernels_to_pulling_for_image.assert_called_once_with(
            agent_id, image, image_ref
        )

    async def test_update_kernels_to_prepared_for_image_with_scheduling(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller: MagicMock,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test update_kernels_to_prepared_for_image requests scheduling when kernels updated."""
        # Setup
        mock_kernel_state_engine.update_kernels_to_prepared_for_image.return_value = 3
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine
        schedule_coordinator._scheduling_controller = mock_scheduling_controller

        agent_id = AgentId("agent-1")
        image = "python:3.9"

        # Execute
        await schedule_coordinator.update_kernels_to_prepared_for_image(agent_id, image)

        # Verify
        mock_kernel_state_engine.update_kernels_to_prepared_for_image.assert_called_once_with(
            agent_id, image, None
        )
        mock_scheduling_controller.mark_scheduling_needed.assert_called_once_with(
            ScheduleType.CHECK_PULLING_PROGRESS
        )

    async def test_update_kernels_to_prepared_for_image_no_scheduling(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_scheduling_controller: MagicMock,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test update_kernels_to_prepared_for_image does not request scheduling when no kernels."""
        # Setup
        mock_kernel_state_engine.update_kernels_to_prepared_for_image.return_value = 0
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine
        schedule_coordinator._scheduling_controller = mock_scheduling_controller

        agent_id = AgentId("agent-1")
        image = "python:3.9"

        # Execute
        await schedule_coordinator.update_kernels_to_prepared_for_image(agent_id, image)

        # Verify
        mock_scheduling_controller.mark_scheduling_needed.assert_not_called()

    async def test_cancel_kernels_for_failed_image(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_kernel_state_engine: MagicMock,
    ) -> None:
        """Test cancel_kernels_for_failed_image delegates to kernel state engine."""
        # Setup
        schedule_coordinator._kernel_state_engine = mock_kernel_state_engine

        agent_id = AgentId("agent-1")
        image = "python:3.9"
        error_msg = "Image pull failed: not found"
        image_ref = "registry.example.com/python:3.9"

        # Execute
        await schedule_coordinator.cancel_kernels_for_failed_image(
            agent_id, image, error_msg, image_ref
        )

        # Verify
        mock_kernel_state_engine.cancel_kernels_for_failed_image.assert_called_once_with(
            agent_id, image, error_msg, image_ref
        )


class TestSchedulerTaskSpec:
    """Test cases for SchedulerTaskSpec."""

    def test_create_if_needed_event(self) -> None:
        """Test create_if_needed_event creates correct event."""
        from ai.backend.common.events.event_types.schedule.anycast import (
            DoSokovanProcessIfNeededEvent,
        )

        spec = SchedulerTaskSpec(
            schedule_type=ScheduleType.SCHEDULE,
            short_interval=2.0,
            long_interval=60.0,
        )

        event = spec.create_if_needed_event()

        assert isinstance(event, DoSokovanProcessIfNeededEvent)
        assert event.schedule_type == "schedule"

    def test_create_process_event(self) -> None:
        """Test create_process_event creates correct event."""
        from ai.backend.common.events.event_types.schedule.anycast import (
            DoSokovanProcessScheduleEvent,
        )

        spec = SchedulerTaskSpec(
            schedule_type=ScheduleType.START,
            short_interval=2.0,
            long_interval=60.0,
        )

        event = spec.create_process_event()

        assert isinstance(event, DoSokovanProcessScheduleEvent)
        assert event.schedule_type == "start"

    def test_short_task_name(self) -> None:
        """Test short_task_name property."""
        spec = SchedulerTaskSpec(schedule_type=ScheduleType.TERMINATE)

        assert spec.short_task_name == "sokovan_process_if_needed_terminate"

    def test_long_task_name(self) -> None:
        """Test long_task_name property."""
        spec = SchedulerTaskSpec(schedule_type=ScheduleType.CHECK_PRECONDITION)

        assert spec.long_task_name == "sokovan_process_schedule_check_precondition"


class TestCreateTaskSpecs:
    """Test cases for create_task_specs method."""

    def test_create_task_specs_returns_event_task_specs(
        self,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        """Test create_task_specs returns list of EventTaskSpec."""
        from ai.backend.common.leader.tasks import EventTaskSpec

        specs = schedule_coordinator.create_task_specs()

        assert isinstance(specs, list)
        assert len(specs) > 0
        for spec in specs:
            assert isinstance(spec, EventTaskSpec)

    def test_create_task_specs_includes_all_schedule_types(
        self,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        """Test create_task_specs includes specs for all schedule types."""
        specs = schedule_coordinator.create_task_specs()
        spec_names = [spec.name for spec in specs]

        # Check that main schedule types are included
        # ScheduleType enum values use underscores (e.g., "check_precondition")
        expected_schedule_types = [
            "schedule",
            "check_precondition",
            "start",
            "terminate",
            "sweep",
            "check_pulling_progress",
            "check_creating_progress",
            "check_terminating_progress",
        ]

        for schedule_type in expected_schedule_types:
            # Should have either short or long task for each type
            assert any(schedule_type in name for name in spec_names), (
                f"Missing spec for {schedule_type}"
            )

    def test_create_task_specs_short_and_long_intervals(
        self,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        """Test create_task_specs creates both short and long interval tasks."""
        specs = schedule_coordinator.create_task_specs()
        spec_names = [spec.name for spec in specs]

        # SCHEDULE type should have both short (if_needed) and long (process) tasks
        schedule_short = any("process_if_needed_schedule" in name for name in spec_names)
        schedule_long = any("process_schedule_schedule" in name for name in spec_names)

        assert schedule_short, "Missing short interval task for SCHEDULE"
        assert schedule_long, "Missing long interval task for SCHEDULE"

    def test_create_task_specs_maintenance_only_long(
        self,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        """Test create_task_specs creates only long interval for maintenance tasks."""
        specs = schedule_coordinator.create_task_specs()
        spec_names = [spec.name for spec in specs]

        # SWEEP should only have long task (maintenance)
        sweep_short = any("process_if_needed_sweep" in name for name in spec_names)
        sweep_long = any("process_schedule_sweep" in name for name in spec_names)

        assert not sweep_short, "SWEEP should not have short interval task"
        assert sweep_long, "Missing long interval task for SWEEP"


class TestLockAcquisition:
    """Test cases for lock acquisition in process_lifecycle_schedule."""

    @pytest.fixture
    def mock_lifecycle_handler_with_lock(self) -> MagicMock:
        """Create mock lifecycle handler with lock_id."""
        mock = MagicMock(spec=SessionLifecycleHandler)
        mock.name = MagicMock(return_value="schedule-sessions")
        mock.lock_id = LockID.LOCKID_SCHEDULE
        mock.target_statuses = MagicMock(return_value=[SessionStatus.PENDING])
        mock.target_kernel_statuses = MagicMock(return_value=[])
        mock.success_status = MagicMock(return_value=SessionStatus.SCHEDULED)
        mock.failure_status = MagicMock(return_value=None)
        mock.stale_status = MagicMock(return_value=None)
        mock.execute = AsyncMock(return_value=SessionExecutionResult())
        mock.post_process = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository_for_lock(self) -> MagicMock:
        """Create mock repository."""
        mock = MagicMock()
        mock.get_schedulable_scaling_groups = AsyncMock(return_value=["default"])
        mock.get_sessions_for_handler = AsyncMock(return_value=[])
        mock.update_sessions_status_bulk = AsyncMock(return_value=0)
        return mock

    async def test_lock_acquired_for_handler_with_lock_id(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_lifecycle_handler_with_lock: MagicMock,
        mock_repository_for_lock: MagicMock,
        mock_lock_factory: MagicMock,
    ) -> None:
        """Test that lock is acquired when handler has lock_id."""
        # Setup
        schedule_coordinator._lifecycle_handlers = {
            ScheduleType.SCHEDULE: mock_lifecycle_handler_with_lock
        }
        schedule_coordinator._repository = mock_repository_for_lock

        # Execute
        await schedule_coordinator.process_lifecycle_schedule(ScheduleType.SCHEDULE)

        # Verify lock was acquired
        mock_lock_factory.assert_called_once_with(
            LockID.LOCKID_SCHEDULE,
            60.0,  # session_schedule_lock_lifetime from config
        )

    async def test_no_lock_for_handler_without_lock_id(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_repository_for_lock: MagicMock,
        mock_lock_factory: MagicMock,
    ) -> None:
        """Test that no lock is acquired when handler has no lock_id."""
        # Setup handler without lock_id
        mock_handler = MagicMock(spec=SessionLifecycleHandler)
        mock_handler.name = MagicMock(return_value="check-progress")
        mock_handler.lock_id = None
        mock_handler.target_statuses = MagicMock(return_value=[SessionStatus.PREPARING])
        mock_handler.target_kernel_statuses = MagicMock(return_value=[])
        mock_handler.success_status = MagicMock(return_value=None)
        mock_handler.failure_status = MagicMock(return_value=None)
        mock_handler.stale_status = MagicMock(return_value=None)
        mock_handler.execute = AsyncMock(return_value=SessionExecutionResult())
        mock_handler.post_process = AsyncMock()

        schedule_coordinator._lifecycle_handlers = {
            ScheduleType.CHECK_PULLING_PROGRESS: mock_handler
        }
        schedule_coordinator._repository = mock_repository_for_lock

        # Execute
        await schedule_coordinator.process_lifecycle_schedule(ScheduleType.CHECK_PULLING_PROGRESS)

        # Verify lock was NOT acquired
        mock_lock_factory.assert_not_called()


class TestProcessIfNeededNoMark:
    """Test cases for process_if_needed when no mark exists."""

    async def test_process_if_needed_returns_false_when_no_mark(
        self,
        schedule_coordinator: ScheduleCoordinator,
        mock_valkey_schedule: MagicMock,
    ) -> None:
        """Test process_if_needed returns False when no schedule mark exists."""
        # Setup valkey_schedule to return False (no mark)
        mock_valkey_schedule.load_and_delete_schedule_mark = AsyncMock(return_value=False)

        # Execute
        result = await schedule_coordinator.process_if_needed(ScheduleType.SCHEDULE)

        # Verify
        assert result is False
        mock_valkey_schedule.load_and_delete_schedule_mark.assert_called_once_with("schedule")
