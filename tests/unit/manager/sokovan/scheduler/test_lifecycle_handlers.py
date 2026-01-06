"""
Tests for SessionLifecycleHandler implementations.

Tests the new lifecycle handler pattern following DeploymentCoordinator style.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import AccessKey, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.handlers import (
    CheckCreatingProgressLifecycleHandler,
    CheckPullingProgressLifecycleHandler,
    CheckRunningSessionTerminationLifecycleHandler,
    CheckTerminatingProgressLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerKernelData,
    HandlerSessionData,
    ScheduledSessionData,
    SessionExecutionResult,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def create_handler_session_data(
    status: SessionStatus,
    scaling_group: str = "default",
    kernel_status: KernelStatus = KernelStatus.RUNNING,
    num_kernels: int = 1,
) -> HandlerSessionData:
    """Helper to create test HandlerSessionData."""
    session_id = SessionId(uuid4())
    kernels = [
        HandlerKernelData(
            kernel_id=uuid4(),
            agent_id=None,
            status=kernel_status,
        )
        for _ in range(num_kernels)
    ]
    return HandlerSessionData(
        session_id=session_id,
        creation_id=str(uuid4()),
        access_key=AccessKey("test-key"),
        status=status,
        scaling_group=scaling_group,
        session_type=SessionTypes.INTERACTIVE,
        kernels=kernels,
    )


class TestCheckPullingProgressLifecycleHandler:
    """Tests for CheckPullingProgressLifecycleHandler."""

    @pytest.fixture
    def mock_event_producer(self) -> MagicMock:
        """Mock EventProducer."""
        mock = MagicMock()
        mock.broadcast_events_batch = AsyncMock()
        return mock

    @pytest.fixture
    def handler(self, mock_event_producer: MagicMock) -> CheckPullingProgressLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckPullingProgressLifecycleHandler(mock_event_producer)

    def test_name(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-pulling-progress"

    def test_target_statuses(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert SessionStatus.PREPARING in statuses
        assert SessionStatus.PULLING in statuses

    def test_target_kernel_statuses(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert KernelStatus.PREPARED in kernel_statuses
        assert KernelStatus.RUNNING in kernel_statuses

    def test_success_status(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.PREPARED

    def test_failure_status(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test failure status (None for this handler)."""
        assert handler.failure_status() is None

    def test_stale_status(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test stale status (None for this handler)."""
        assert handler.stale_status() is None

    def test_lock_id(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def test_execute_all_sessions_succeed(
        self, handler: CheckPullingProgressLifecycleHandler
    ) -> None:
        """Test execute marks all sessions as success."""
        sessions: Sequence[HandlerSessionData] = [
            create_handler_session_data(
                SessionStatus.PREPARING,
                kernel_status=KernelStatus.PREPARED,
            ),
            create_handler_session_data(
                SessionStatus.PULLING,
                kernel_status=KernelStatus.RUNNING,
            ),
        ]

        result = await handler.execute(sessions, "default")

        assert len(result.successes) == 2
        assert len(result.failures) == 0
        assert len(result.stales) == 0
        assert len(result.scheduled_data) == 2

    async def test_execute_empty_sessions(
        self, handler: CheckPullingProgressLifecycleHandler
    ) -> None:
        """Test execute with empty sessions."""
        result = await handler.execute([], "default")

        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert len(result.stales) == 0

    async def test_execute_includes_correct_scheduled_data(
        self, handler: CheckPullingProgressLifecycleHandler
    ) -> None:
        """Test execute includes correct scheduled data for post-processing."""
        session = create_handler_session_data(
            SessionStatus.PREPARING,
            kernel_status=KernelStatus.PREPARED,
        )
        sessions: Sequence[HandlerSessionData] = [session]

        result = await handler.execute(sessions, "default")

        assert len(result.scheduled_data) == 1
        scheduled = result.scheduled_data[0]
        assert scheduled.session_id == session.session_id
        assert scheduled.creation_id == session.creation_id
        assert scheduled.access_key == session.access_key
        assert scheduled.reason == "triggered-by-scheduler"


class TestCheckCreatingProgressLifecycleHandler:
    """Tests for CheckCreatingProgressLifecycleHandler."""

    @pytest.fixture
    def mock_event_producer(self) -> MagicMock:
        """Mock EventProducer."""
        mock = MagicMock()
        mock.broadcast_events_batch = AsyncMock()
        return mock

    @pytest.fixture
    def mock_scheduling_controller(self) -> MagicMock:
        """Mock SchedulingController."""
        mock = MagicMock()
        mock.mark_scheduling_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Mock SchedulerRepository."""
        mock = MagicMock()
        mock.get_sessions_for_transition = AsyncMock(return_value=[])
        mock.update_sessions_to_running = AsyncMock()
        return mock

    @pytest.fixture
    def mock_hook_registry(self) -> MagicMock:
        """Mock HookRegistry."""
        mock = MagicMock()
        mock_hook = MagicMock()
        mock_hook.on_transition_to_running = AsyncMock(return_value=None)
        mock.get_hook = MagicMock(return_value=mock_hook)
        return mock

    @pytest.fixture
    def handler(
        self,
        mock_scheduling_controller: MagicMock,
        mock_event_producer: MagicMock,
        mock_repository: MagicMock,
        mock_hook_registry: MagicMock,
    ) -> CheckCreatingProgressLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckCreatingProgressLifecycleHandler(
            mock_scheduling_controller,
            mock_event_producer,
            mock_repository,
            mock_hook_registry,
        )

    def test_name(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-creating-progress"

    def test_target_statuses(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert statuses == [SessionStatus.CREATING]

    def test_target_kernel_statuses(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert kernel_statuses == [KernelStatus.RUNNING]

    def test_success_status(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.RUNNING

    def test_failure_status(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test failure status (None - sessions stay in CREATING on failure)."""
        assert handler.failure_status() is None

    def test_lock_id(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def test_execute_empty_sessions(
        self, handler: CheckCreatingProgressLifecycleHandler
    ) -> None:
        """Test execute with empty sessions returns empty result."""
        result = await handler.execute([], "default")

        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert result.needs_post_processing() is False


class TestCheckTerminatingProgressLifecycleHandler:
    """Tests for CheckTerminatingProgressLifecycleHandler."""

    @pytest.fixture
    def mock_event_producer(self) -> MagicMock:
        """Mock EventProducer."""
        mock = MagicMock()
        mock.broadcast_events_batch = AsyncMock()
        return mock

    @pytest.fixture
    def mock_scheduling_controller(self) -> MagicMock:
        """Mock SchedulingController."""
        mock = MagicMock()
        mock.mark_scheduling_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Mock SchedulerRepository."""
        mock = MagicMock()
        mock.get_sessions_for_transition = AsyncMock(return_value=[])
        mock.update_sessions_to_terminated = AsyncMock()
        mock.invalidate_kernel_related_cache = AsyncMock()
        return mock

    @pytest.fixture
    def mock_hook_registry(self) -> MagicMock:
        """Mock HookRegistry."""
        mock = MagicMock()
        mock_hook = MagicMock()
        mock_hook.on_transition_to_terminated = AsyncMock(return_value=None)
        mock.get_hook = MagicMock(return_value=mock_hook)
        return mock

    @pytest.fixture
    def handler(
        self,
        mock_scheduling_controller: MagicMock,
        mock_event_producer: MagicMock,
        mock_repository: MagicMock,
        mock_hook_registry: MagicMock,
    ) -> CheckTerminatingProgressLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckTerminatingProgressLifecycleHandler(
            mock_scheduling_controller,
            mock_event_producer,
            mock_repository,
            mock_hook_registry,
        )

    def test_name(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-terminating-progress"

    def test_target_statuses(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert statuses == [SessionStatus.TERMINATING]

    def test_target_kernel_statuses(
        self, handler: CheckTerminatingProgressLifecycleHandler
    ) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert kernel_statuses == [KernelStatus.TERMINATED]

    def test_success_status(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.TERMINATED

    def test_failure_status(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test failure status (None - termination always proceeds)."""
        assert handler.failure_status() is None

    def test_lock_id(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def test_execute_empty_sessions(
        self, handler: CheckTerminatingProgressLifecycleHandler
    ) -> None:
        """Test execute with empty sessions returns empty result."""
        result = await handler.execute([], "default")

        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert result.needs_post_processing() is False


class TestCheckRunningSessionTerminationLifecycleHandler:
    """Tests for CheckRunningSessionTerminationLifecycleHandler."""

    @pytest.fixture
    def mock_valkey_schedule(self) -> MagicMock:
        """Mock ValkeyScheduleClient."""
        mock = MagicMock()
        mock.mark_schedule_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Mock SchedulerRepository."""
        mock = MagicMock()
        mock.invalidate_kernel_related_cache = AsyncMock()
        return mock

    @pytest.fixture
    def handler(
        self,
        mock_valkey_schedule: MagicMock,
        mock_repository: MagicMock,
    ) -> CheckRunningSessionTerminationLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckRunningSessionTerminationLifecycleHandler(
            mock_valkey_schedule,
            mock_repository,
        )

    def test_name(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-running-session-termination"

    def test_target_statuses(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert statuses == [SessionStatus.RUNNING]

    def test_target_kernel_statuses(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert kernel_statuses == [KernelStatus.TERMINATED]

    def test_success_status(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.TERMINATING

    def test_failure_status(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test failure status (None for this handler)."""
        assert handler.failure_status() is None

    def test_stale_status(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test stale status (None for this handler)."""
        assert handler.stale_status() is None

    def test_lock_id(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def test_execute_marks_sessions_for_termination(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test execute marks RUNNING sessions with all kernels TERMINATED for termination."""
        sessions: Sequence[HandlerSessionData] = [
            create_handler_session_data(
                SessionStatus.RUNNING,
                kernel_status=KernelStatus.TERMINATED,
            ),
            create_handler_session_data(
                SessionStatus.RUNNING,
                kernel_status=KernelStatus.TERMINATED,
            ),
        ]

        result = await handler.execute(sessions, "default")

        assert len(result.successes) == 2
        assert len(result.failures) == 0
        assert len(result.stales) == 0
        assert len(result.scheduled_data) == 2

    async def test_execute_empty_sessions(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test execute with empty sessions."""
        result = await handler.execute([], "default")

        assert len(result.successes) == 0
        assert result.needs_post_processing() is False

    async def test_execute_scheduled_data_has_abnormal_reason(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test execute sets ABNORMAL_TERMINATION as reason."""
        session = create_handler_session_data(
            SessionStatus.RUNNING,
            kernel_status=KernelStatus.TERMINATED,
        )
        sessions: Sequence[HandlerSessionData] = [session]

        result = await handler.execute(sessions, "default")

        assert len(result.scheduled_data) == 1
        assert result.scheduled_data[0].reason == "ABNORMAL_TERMINATION"


class TestSessionExecutionResult:
    """Tests for SessionExecutionResult dataclass."""

    def test_needs_post_processing_empty(self) -> None:
        """Test needs_post_processing returns False when empty."""
        result = SessionExecutionResult()
        assert result.needs_post_processing() is False

    def test_needs_post_processing_with_data(self) -> None:
        """Test needs_post_processing returns True with scheduled_data."""
        result = SessionExecutionResult()
        result.scheduled_data.append(
            ScheduledSessionData(
                session_id=SessionId(uuid4()),
                creation_id="test",
                access_key=AccessKey("test"),
                reason="test",
            )
        )
        assert result.needs_post_processing() is True

    def test_success_count(self) -> None:
        """Test success_count returns correct count."""
        result = SessionExecutionResult()
        result.successes.append(SessionId(uuid4()))
        result.successes.append(SessionId(uuid4()))
        assert result.success_count() == 2

    def test_merge(self) -> None:
        """Test merge combines two results."""
        result1 = SessionExecutionResult()
        result1.successes.append(SessionId(uuid4()))

        result2 = SessionExecutionResult()
        result2.successes.append(SessionId(uuid4()))
        result2.stales.append(SessionId(uuid4()))

        result1.merge(result2)

        assert len(result1.successes) == 2
        assert len(result1.stales) == 1
