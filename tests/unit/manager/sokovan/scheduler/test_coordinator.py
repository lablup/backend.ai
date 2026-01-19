"""Unit tests for Sokovan ScheduleCoordinator.

Based on BEP-1033 test scenarios for coordinator-level testing.

Test Scenarios:
- SC-CO-001 ~ SC-CO-008: FailureClassification
- SC-CO-009 ~ SC-CO-013: HookExecution
- SC-CO-014 ~ SC-CO-019: StatusTransition
- SC-CO-020 ~ SC-CO-025: PostProcessors
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
    StatusTransitions,
    TransitionStatus,
)
from ai.backend.manager.defs import SERVICE_MAX_RETRIES
from ai.backend.manager.sokovan.scheduler.coordinator import (
    FailureClassificationResult,
    ScheduleCoordinator,
)
from ai.backend.manager.sokovan.scheduler.post_processors import PostProcessorContext
from ai.backend.manager.sokovan.scheduler.results import (
    KernelExecutionResult,
    KernelTransitionInfo,
    SessionExecutionResult,
    SessionTransitionInfo,
)

# =============================================================================
# Test Fixtures
# =============================================================================


def _create_session_with_kernels(
    session_id: SessionId,
    status: SessionStatus = SessionStatus.PREPARING,
    phase_attempts: int = 0,
    phase_started_at: datetime | None = None,
) -> MagicMock:
    """Create a mock SessionWithKernels for testing."""
    mock = MagicMock()
    mock.session_info.identity.id = session_id
    mock.session_info.lifecycle.status = status
    mock.phase_attempts = phase_attempts
    mock.phase_started_at = phase_started_at
    mock.kernel_infos = []
    return mock


def _create_session_transition_info(
    session_id: SessionId | None = None,
    from_status: SessionStatus = SessionStatus.PREPARING,
    reason: str | None = "test-reason",
) -> SessionTransitionInfo:
    """Create a SessionTransitionInfo for testing."""
    return SessionTransitionInfo(
        session_id=session_id or SessionId(uuid4()),
        from_status=from_status,
        reason=reason,
        creation_id=str(uuid4()),
        access_key=AccessKey("test-key"),
    )


# =============================================================================
# TestScheduleCoordinatorFailureClassification Tests (SC-CO-001 ~ SC-CO-008)
# =============================================================================


class TestScheduleCoordinatorFailureClassification:
    """Tests for failure classification logic in ScheduleCoordinator.

    The coordinator classifies failures into:
    - give_up: phase_attempts >= SERVICE_MAX_RETRIES
    - expired: timeout exceeded based on STATUS_TIMEOUT_MAP
    - need_retry: default (can be retried)
    """

    def test_give_up_on_max_attempts_exceeded(self) -> None:
        """SC-CO-001: Give up when max attempts exceeded.

        Given: Session with phase_attempts >= SERVICE_MAX_RETRIES
        When: Coordinator classifies failures
        Then: Session is classified as give_up
        """
        # Arrange
        session_id = SessionId(uuid4())
        failure = _create_session_transition_info(session_id=session_id)

        session = _create_session_with_kernels(
            session_id=session_id,
            status=SessionStatus.PREPARING,
            phase_attempts=SERVICE_MAX_RETRIES,  # At max retries
        )

        # Act - Directly test the classification method
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[failure],
            sessions=[session],
        )

        # Assert
        assert len(result.give_up) == 1
        assert len(result.expired) == 0
        assert len(result.need_retry) == 0
        assert result.give_up[0].session_id == session_id

    def test_expired_on_timeout_exceeded(self) -> None:
        """SC-CO-002: Expire when timeout exceeded.

        Given: Session in PREPARING status for longer than STATUS_TIMEOUT_MAP threshold
        When: Coordinator classifies failures
        Then: Session is classified as expired
        """
        # Arrange
        session_id = SessionId(uuid4())
        failure = _create_session_transition_info(
            session_id=session_id,
            from_status=SessionStatus.PREPARING,
        )

        # Session started 20 minutes ago (exceeds 15 minute threshold)
        past_time = datetime.now(tzutc()) - timedelta(minutes=20)
        session = _create_session_with_kernels(
            session_id=session_id,
            status=SessionStatus.PREPARING,
            phase_attempts=0,
            phase_started_at=past_time,
        )

        # Act
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[failure],
            sessions=[session],
        )

        # Assert
        assert len(result.give_up) == 0
        assert len(result.expired) == 1
        assert len(result.need_retry) == 0
        assert result.expired[0].session_id == session_id

    def test_need_retry_on_retryable_failure(self) -> None:
        """SC-CO-003: Need retry for retryable failures.

        Given: Session with low phase_attempts and within timeout
        When: Coordinator classifies failures
        Then: Session is classified as need_retry
        """
        # Arrange
        session_id = SessionId(uuid4())
        failure = _create_session_transition_info(session_id=session_id)

        # Session just started, low attempts
        recent_time = datetime.now(tzutc()) - timedelta(minutes=1)
        session = _create_session_with_kernels(
            session_id=session_id,
            status=SessionStatus.PREPARING,
            phase_attempts=1,
            phase_started_at=recent_time,
        )

        # Act
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[failure],
            sessions=[session],
        )

        # Assert
        assert len(result.give_up) == 0
        assert len(result.expired) == 0
        assert len(result.need_retry) == 1
        assert result.need_retry[0].session_id == session_id

    def test_give_up_takes_priority_over_expired(self) -> None:
        """SC-CO-004: Give up takes priority over expired.

        Given: Session with max attempts exceeded AND timeout exceeded
        When: Coordinator classifies failures
        Then: Session is classified as give_up (priority over expired)
        """
        # Arrange
        session_id = SessionId(uuid4())
        failure = _create_session_transition_info(session_id=session_id)

        # Both conditions met: max retries AND timeout
        past_time = datetime.now(tzutc()) - timedelta(minutes=20)
        session = _create_session_with_kernels(
            session_id=session_id,
            status=SessionStatus.PREPARING,
            phase_attempts=SERVICE_MAX_RETRIES,
            phase_started_at=past_time,
        )

        # Act
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[failure],
            sessions=[session],
        )

        # Assert - give_up takes priority
        assert len(result.give_up) == 1
        assert len(result.expired) == 0
        assert len(result.need_retry) == 0

    def test_mixed_classification_results(self) -> None:
        """SC-CO-005: Mixed failures are classified correctly.

        Given: Three failures with different conditions
        When: Coordinator classifies failures
        Then: Each is correctly classified
        """
        # Arrange
        # Session 1: Max retries exceeded -> give_up
        session_id_1 = SessionId(uuid4())
        failure_1 = _create_session_transition_info(session_id=session_id_1)
        session_1 = _create_session_with_kernels(
            session_id=session_id_1,
            phase_attempts=SERVICE_MAX_RETRIES,
        )

        # Session 2: Timeout exceeded -> expired
        session_id_2 = SessionId(uuid4())
        failure_2 = _create_session_transition_info(session_id=session_id_2)
        past_time = datetime.now(tzutc()) - timedelta(minutes=20)
        session_2 = _create_session_with_kernels(
            session_id=session_id_2,
            status=SessionStatus.PREPARING,
            phase_attempts=1,
            phase_started_at=past_time,
        )

        # Session 3: Neither condition -> need_retry
        session_id_3 = SessionId(uuid4())
        failure_3 = _create_session_transition_info(session_id=session_id_3)
        recent_time = datetime.now(tzutc()) - timedelta(minutes=1)
        session_3 = _create_session_with_kernels(
            session_id=session_id_3,
            phase_attempts=1,
            phase_started_at=recent_time,
        )

        # Act
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[failure_1, failure_2, failure_3],
            sessions=[session_1, session_2, session_3],
        )

        # Assert
        assert len(result.give_up) == 1
        assert len(result.expired) == 1
        assert len(result.need_retry) == 1

    def test_empty_failures_returns_empty_result(self) -> None:
        """SC-CO-006: Empty failures list returns empty result.

        Given: Empty failures list
        When: Coordinator classifies failures
        Then: All classification lists are empty
        """
        # Act
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[],
            sessions=[],
        )

        # Assert
        assert len(result.give_up) == 0
        assert len(result.expired) == 0
        assert len(result.need_retry) == 0

    def test_session_not_found_skipped(self) -> None:
        """SC-CO-007: Failure without matching session is skipped.

        Given: Failure with session_id not in sessions list
        When: Coordinator classifies failures
        Then: That failure is not included in any classification
        """
        # Arrange
        failure = _create_session_transition_info(session_id=SessionId(uuid4()))
        # No matching session in the list

        # Act
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[failure],
            sessions=[],  # Empty - no matching session
        )

        # Assert
        assert len(result.give_up) == 0
        assert len(result.expired) == 0
        assert len(result.need_retry) == 0

    def test_status_without_timeout_not_expired(self) -> None:
        """SC-CO-008: Status not in timeout map is not expired.

        Given: Session in status without timeout threshold (e.g., PENDING)
        When: Coordinator classifies failures
        Then: Session is classified as need_retry (not expired)
        """
        # Arrange
        session_id = SessionId(uuid4())
        failure = _create_session_transition_info(
            session_id=session_id,
            from_status=SessionStatus.PENDING,  # Not in STATUS_TIMEOUT_MAP
        )

        # Session started long ago, but PENDING has no timeout
        past_time = datetime.now(tzutc()) - timedelta(hours=2)
        session = _create_session_with_kernels(
            session_id=session_id,
            status=SessionStatus.PENDING,
            phase_attempts=1,
            phase_started_at=past_time,
        )

        # Act
        result = ScheduleCoordinator._classify_failures(
            None,  # type: ignore[arg-type]
            failures=[failure],
            sessions=[session],
        )

        # Assert - PENDING has no timeout, so it's need_retry
        assert len(result.give_up) == 0
        assert len(result.expired) == 0
        assert len(result.need_retry) == 1


# =============================================================================
# TestScheduleCoordinatorHookExecution Tests (SC-CO-009 ~ SC-CO-013)
# =============================================================================


class TestScheduleCoordinatorHookExecution:
    """Tests for hook execution in ScheduleCoordinator.

    Hooks are executed before status transitions for specific target statuses.
    """

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create a mock coordinator with necessary dependencies."""
        coordinator = MagicMock(spec=ScheduleCoordinator)
        coordinator._hook_registry = MagicMock()
        coordinator._repository = AsyncMock()
        return coordinator

    def _setup_execute_single_hook(
        self,
        mock_coordinator: MagicMock,
        mock_hook: AsyncMock,
    ) -> None:
        """Configure _execute_single_hook to actually invoke the hook.

        When testing _execute_transition_hooks with a mock coordinator,
        internal calls to self._execute_single_hook go to the mock.
        This helper sets up the mock to properly invoke the hook.
        """

        async def execute_single_hook_impl(session: MagicMock, status: SessionStatus) -> None:
            hook = mock_coordinator._hook_registry.get_hook(status)
            if hook:
                await hook.execute(session)

        mock_coordinator._execute_single_hook = AsyncMock(side_effect=execute_single_hook_impl)

    async def test_hook_executed_for_status_with_hook(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-009: Hook is executed when status has a registered hook.

        Given: Target status has a hook registered
        When: Sessions transition to that status
        Then: Hook is executed for each session
        """
        # Arrange
        mock_hook = AsyncMock()
        mock_coordinator._hook_registry.get_hook.return_value = mock_hook
        self._setup_execute_single_hook(mock_coordinator, mock_hook)

        sessions = [
            _create_session_transition_info(session_id=SessionId(uuid4())) for _ in range(3)
        ]

        # Create mock full session data
        mock_full_sessions = [MagicMock() for _ in sessions]
        for mock_session, info in zip(mock_full_sessions, sessions, strict=True):
            mock_session.session_info.identity.id = info.session_id

        mock_coordinator._repository.search_sessions_with_kernels_for_handler = AsyncMock(
            return_value=mock_full_sessions
        )

        # Call the actual method
        await ScheduleCoordinator._execute_transition_hooks(
            mock_coordinator,
            sessions,
            SessionStatus.RUNNING,
        )

        # Assert
        assert mock_hook.execute.await_count == len(sessions)

    async def test_no_hook_for_status_without_hook(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-010: No hook execution when status has no registered hook.

        Given: Target status has no hook registered
        When: Sessions transition to that status
        Then: No hook is executed, sessions pass through
        """
        # Arrange
        mock_coordinator._hook_registry.get_hook.return_value = None
        self._setup_execute_single_hook(mock_coordinator, None)  # type: ignore[arg-type]

        session_info = _create_session_transition_info(session_id=SessionId(uuid4()))
        sessions = [session_info]

        # Create mock full session data
        mock_full_session = MagicMock()
        mock_full_session.session_info.identity.id = session_info.session_id

        mock_coordinator._repository.search_sessions_with_kernels_for_handler = AsyncMock(
            return_value=[mock_full_session]
        )

        # Act
        result = await ScheduleCoordinator._execute_transition_hooks(
            mock_coordinator,
            sessions,
            SessionStatus.SCHEDULED,
        )

        # Assert - When no hook, sessions pass through successfully
        assert len(result.successful_sessions) == 1
        assert result.successful_sessions[0].session_id == session_info.session_id

    async def test_hook_failure_excludes_session(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-011: Hook failure excludes session from transition.

        Given: Hook fails for one session
        When: Processing transitions
        Then: Failed session is excluded from successful_sessions
        """
        # Arrange
        mock_hook = AsyncMock()
        mock_hook.execute.side_effect = [None, RuntimeError("Hook failed"), None]
        mock_coordinator._hook_registry.get_hook.return_value = mock_hook
        self._setup_execute_single_hook(mock_coordinator, mock_hook)

        sessions = [
            _create_session_transition_info(session_id=SessionId(uuid4())) for _ in range(3)
        ]

        mock_full_sessions = [MagicMock() for _ in sessions]
        for mock_session, info in zip(mock_full_sessions, sessions, strict=True):
            mock_session.session_info.identity.id = info.session_id

        mock_coordinator._repository.search_sessions_with_kernels_for_handler = AsyncMock(
            return_value=mock_full_sessions
        )

        # Act
        result = await ScheduleCoordinator._execute_transition_hooks(
            mock_coordinator,
            sessions,
            SessionStatus.RUNNING,
        )

        # Assert - Second session should be excluded
        assert len(result.successful_sessions) == 2
        assert result.successful_sessions[0].session_id == sessions[0].session_id
        assert result.successful_sessions[1].session_id == sessions[2].session_id

    async def test_empty_sessions_returns_empty_result(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-012: Empty sessions list returns empty result.

        Given: Empty sessions list
        When: Execute hooks
        Then: Empty result is returned
        """
        # Act
        result = await ScheduleCoordinator._execute_transition_hooks(
            mock_coordinator,
            [],
            SessionStatus.RUNNING,
        )

        # Assert
        assert result.successful_sessions == []
        assert result.full_session_data == []

    async def test_hook_receives_full_session_data(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-013: Hook receives full session data.

        Given: Sessions with kernel data
        When: Executing hooks
        Then: Hook receives full SessionWithKernels data
        """
        # Arrange
        mock_hook = AsyncMock()
        mock_coordinator._hook_registry.get_hook.return_value = mock_hook
        self._setup_execute_single_hook(mock_coordinator, mock_hook)

        session_info = _create_session_transition_info(session_id=SessionId(uuid4()))

        mock_full_session = MagicMock()
        mock_full_session.session_info.identity.id = session_info.session_id
        mock_full_session.kernel_infos = [MagicMock(), MagicMock()]

        mock_coordinator._repository.search_sessions_with_kernels_for_handler = AsyncMock(
            return_value=[mock_full_session]
        )

        # Act
        await ScheduleCoordinator._execute_transition_hooks(
            mock_coordinator,
            [session_info],
            SessionStatus.RUNNING,
        )

        # Assert
        mock_hook.execute.assert_awaited_once_with(mock_full_session)


# =============================================================================
# TestScheduleCoordinatorStatusTransition Tests (SC-CO-014 ~ SC-CO-019)
# =============================================================================


class TestScheduleCoordinatorStatusTransition:
    """Tests for status transition logic in ScheduleCoordinator.

    Tests the _handle_result and _apply_transition methods.
    """

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create a mock coordinator with necessary dependencies."""
        coordinator = MagicMock(spec=ScheduleCoordinator)
        coordinator._repository = AsyncMock()
        coordinator._kernel_state_engine = AsyncMock()
        coordinator._event_producer = AsyncMock()
        return coordinator

    async def test_success_transition_applied(
        self,
        mock_coordinator: MagicMock,
        status_transitions_with_all_outcomes: StatusTransitions,
    ) -> None:
        """SC-CO-014: Success transitions are applied correctly.

        Given: SessionExecutionResult with successes
        When: Handle result is called
        Then: Sessions transition to success status
        """
        # Arrange
        mock_handler = MagicMock()
        mock_handler.name.return_value = "test_handler"
        mock_handler.status_transitions.return_value = status_transitions_with_all_outcomes

        session_info = _create_session_transition_info(session_id=SessionId(uuid4()))
        result = SessionExecutionResult(
            successes=[session_info],
            failures=[],
            skipped=[],
        )

        session = _create_session_with_kernels(
            session_id=session_info.session_id,
        )

        # Mock _classify_failures to return empty result (no failures to classify)
        mock_coordinator._classify_failures = MagicMock(
            return_value=FailureClassificationResult(give_up=[], expired=[], need_retry=[])
        )
        mock_coordinator._apply_transition = AsyncMock()
        mock_coordinator._broadcast_transition_events = AsyncMock()

        # Act
        await ScheduleCoordinator._handle_result(
            mock_coordinator,
            handler=mock_handler,
            result=result,
            records={},
            sessions=[session],
        )

        # Assert - _apply_transition should be called for successes
        mock_coordinator._apply_transition.assert_awaited()
        # Get the first call's positional arguments
        # _apply_transition(handler_name, session_infos, transition, scheduling_result, records)
        call_args = mock_coordinator._apply_transition.call_args_list[0].args
        assert call_args[0] == "test_handler"  # handler_name
        assert call_args[1] == [session_info]  # session_infos
        assert call_args[2] == status_transitions_with_all_outcomes.success  # transition
        assert call_args[3] == SchedulingResult.SUCCESS  # scheduling_result

    async def test_failure_classified_and_transitioned(
        self,
        mock_coordinator: MagicMock,
        status_transitions_with_all_outcomes: StatusTransitions,
    ) -> None:
        """SC-CO-015: Failures are classified and transitioned correctly.

        Given: SessionExecutionResult with failures
        When: Handle result is called
        Then: Failures are classified and appropriate transitions applied
        """
        # Arrange
        mock_handler = MagicMock()
        mock_handler.name.return_value = "test_handler"
        mock_handler.status_transitions.return_value = status_transitions_with_all_outcomes

        session_id = SessionId(uuid4())
        failure_info = _create_session_transition_info(session_id=session_id)
        result = SessionExecutionResult(
            successes=[],
            failures=[failure_info],
            skipped=[],
        )

        session = _create_session_with_kernels(
            session_id=session_id,
            phase_attempts=SERVICE_MAX_RETRIES,  # Will be classified as give_up
        )

        # Create the classification result that _classify_failures would return
        expected_classification = FailureClassificationResult(
            give_up=[failure_info],
            expired=[],
            need_retry=[],
        )
        mock_coordinator._classify_failures = MagicMock(return_value=expected_classification)
        mock_coordinator._apply_transition = AsyncMock()
        mock_coordinator._broadcast_transition_events = AsyncMock()

        # Act
        classified = await ScheduleCoordinator._handle_result(
            mock_coordinator,
            handler=mock_handler,
            result=result,
            records={},
            sessions=[session],
        )

        # Assert
        assert classified is not None
        assert len(classified.give_up) == 1
        # Verify _apply_transition was called for give_up
        mock_coordinator._apply_transition.assert_awaited()

    async def test_skipped_recorded_without_status_change(
        self,
        mock_coordinator: MagicMock,
        status_transitions_with_all_outcomes: StatusTransitions,
    ) -> None:
        """SC-CO-016: Skipped sessions are recorded without status change.

        Given: SessionExecutionResult with skipped sessions
        When: Handle result is called
        Then: Skipped sessions are recorded in history without status change
        """
        # Arrange
        mock_handler = MagicMock()
        mock_handler.name.return_value = "test_handler"
        mock_handler.status_transitions.return_value = status_transitions_with_all_outcomes

        skipped_info = _create_session_transition_info(session_id=SessionId(uuid4()))
        result = SessionExecutionResult(
            successes=[],
            failures=[],
            skipped=[skipped_info],
        )

        mock_coordinator._classify_failures = MagicMock(
            return_value=FailureClassificationResult(give_up=[], expired=[], need_retry=[])
        )
        mock_coordinator._apply_transition = AsyncMock()
        mock_coordinator._record_skipped_history = AsyncMock()

        # Act
        await ScheduleCoordinator._handle_result(
            mock_coordinator,
            handler=mock_handler,
            result=result,
            records={},
            sessions=[],
        )

        # Assert
        mock_coordinator._record_skipped_history.assert_awaited_once()

    async def test_empty_result_no_transitions(
        self,
        mock_coordinator: MagicMock,
        status_transitions_with_all_outcomes: StatusTransitions,
    ) -> None:
        """SC-CO-017: Empty result causes no transitions.

        Given: Empty SessionExecutionResult
        When: Handle result is called
        Then: No transitions are applied
        """
        # Arrange
        mock_handler = MagicMock()
        mock_handler.name.return_value = "test_handler"
        mock_handler.status_transitions.return_value = status_transitions_with_all_outcomes

        result = SessionExecutionResult(
            successes=[],
            failures=[],
            skipped=[],
        )

        mock_coordinator._apply_transition = AsyncMock()
        mock_coordinator._record_skipped_history = AsyncMock()

        # Act
        classified = await ScheduleCoordinator._handle_result(
            mock_coordinator,
            handler=mock_handler,
            result=result,
            records={},
            sessions=[],
        )

        # Assert
        mock_coordinator._apply_transition.assert_not_awaited()
        mock_coordinator._record_skipped_history.assert_not_awaited()
        assert classified is None

    async def test_kernel_reset_on_pending_transition(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-018: Kernel status reset when session transitions to PENDING.

        Given: Session transitioning to PENDING with kernel=PENDING
        When: Apply transition is called
        Then: Kernels are reset to PENDING
        """
        # Arrange
        session_info = _create_session_transition_info(session_id=SessionId(uuid4()))
        transition = TransitionStatus(
            session=SessionStatus.PENDING,
            kernel=KernelStatus.PENDING,
        )

        mock_coordinator._repository.update_with_history = AsyncMock(return_value=1)
        mock_coordinator._apply_kernel_pending_resets = AsyncMock()

        # Act
        await ScheduleCoordinator._apply_transition(
            mock_coordinator,
            handler_name="test_handler",
            session_infos=[session_info],
            transition=transition,
            scheduling_result=SchedulingResult.NEED_RETRY,
            records={},
        )

        # Assert
        mock_coordinator._apply_kernel_pending_resets.assert_awaited_once()

    async def test_no_kernel_reset_for_non_pending_transition(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-019: No kernel reset for non-PENDING transitions.

        Given: Session transitioning to SCHEDULED
        When: Apply transition is called
        Then: Kernels are not reset
        """
        # Arrange
        session_info = _create_session_transition_info(session_id=SessionId(uuid4()))
        transition = TransitionStatus(
            session=SessionStatus.SCHEDULED,
            kernel=KernelStatus.SCHEDULED,
        )

        mock_coordinator._repository.update_with_history = AsyncMock(return_value=1)
        mock_coordinator._apply_kernel_pending_resets = AsyncMock()

        # Act
        await ScheduleCoordinator._apply_transition(
            mock_coordinator,
            handler_name="test_handler",
            session_infos=[session_info],
            transition=transition,
            scheduling_result=SchedulingResult.SUCCESS,
            records={},
        )

        # Assert
        mock_coordinator._apply_kernel_pending_resets.assert_not_awaited()


# =============================================================================
# TestScheduleCoordinatorPostProcessors Tests (SC-CO-020 ~ SC-CO-025)
# =============================================================================


class TestScheduleCoordinatorPostProcessors:
    """Tests for post-processor execution in ScheduleCoordinator."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create a mock coordinator with post-processors."""
        coordinator = MagicMock(spec=ScheduleCoordinator)
        coordinator._post_processors = []
        coordinator._kernel_post_processors = []
        return coordinator

    async def test_all_post_processors_called(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-020: All post-processors are called.

        Given: Multiple post-processors configured
        When: Run post-processors is called
        Then: All post-processors are executed
        """
        # Arrange
        mock_pp_1 = AsyncMock()
        mock_pp_2 = AsyncMock()
        mock_pp_3 = AsyncMock()
        mock_coordinator._post_processors = [mock_pp_1, mock_pp_2, mock_pp_3]

        result = SessionExecutionResult(
            successes=[_create_session_transition_info()],
            failures=[],
            skipped=[],
        )

        # Act
        await ScheduleCoordinator._run_post_processors(
            mock_coordinator,
            result=result,
            target_statuses={SessionStatus.SCHEDULED},
        )

        # Assert
        mock_pp_1.execute.assert_awaited_once()
        mock_pp_2.execute.assert_awaited_once()
        mock_pp_3.execute.assert_awaited_once()

    async def test_post_processor_receives_context(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-021: Post-processor receives correct context.

        Given: Post-processor configured
        When: Run post-processors is called
        Then: Post-processor receives PostProcessorContext with result and target_statuses
        """
        # Arrange
        mock_pp = AsyncMock()
        mock_coordinator._post_processors = [mock_pp]

        result = SessionExecutionResult(
            successes=[_create_session_transition_info()],
            failures=[],
            skipped=[],
        )
        target_statuses = {SessionStatus.SCHEDULED, SessionStatus.RUNNING}

        # Act
        await ScheduleCoordinator._run_post_processors(
            mock_coordinator,
            result=result,
            target_statuses=target_statuses,
        )

        # Assert
        call_args = mock_pp.execute.call_args
        context = call_args[0][0]
        assert isinstance(context, PostProcessorContext)
        assert context.result == result
        assert context.target_statuses == target_statuses

    async def test_post_processor_failure_logged_not_thrown(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-022: Post-processor failure is logged but not thrown.

        Given: Post-processor that raises an exception
        When: Run post-processors is called
        Then: Exception is caught and logged, not propagated
        """
        # Arrange
        mock_pp_success = AsyncMock()
        mock_pp_failure = AsyncMock()
        mock_pp_failure.execute.side_effect = RuntimeError("Post-processor failed")
        mock_pp_success_2 = AsyncMock()

        mock_coordinator._post_processors = [mock_pp_success, mock_pp_failure, mock_pp_success_2]

        result = SessionExecutionResult(
            successes=[_create_session_transition_info()],
            failures=[],
            skipped=[],
        )

        # Act - Should not raise
        await ScheduleCoordinator._run_post_processors(
            mock_coordinator,
            result=result,
            target_statuses={SessionStatus.SCHEDULED},
        )

        # Assert - All post-processors were called
        mock_pp_success.execute.assert_awaited_once()
        mock_pp_failure.execute.assert_awaited_once()
        mock_pp_success_2.execute.assert_awaited_once()

    async def test_empty_post_processors_no_error(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-023: Empty post-processors list causes no error.

        Given: No post-processors configured
        When: Run post-processors is called
        Then: No error occurs
        """
        # Arrange
        mock_coordinator._post_processors = []

        result = SessionExecutionResult(
            successes=[_create_session_transition_info()],
            failures=[],
            skipped=[],
        )

        # Act - Should not raise
        await ScheduleCoordinator._run_post_processors(
            mock_coordinator,
            result=result,
            target_statuses={SessionStatus.SCHEDULED},
        )

        # Assert - No exception raised

    async def test_kernel_post_processors_called(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """SC-CO-024: Kernel post-processors are called for kernel handlers.

        Given: Kernel post-processors configured
        When: Run kernel post-processors is called
        Then: All kernel post-processors are executed
        """
        # Arrange
        mock_kpp_1 = AsyncMock()
        mock_kpp_2 = AsyncMock()
        mock_coordinator._kernel_post_processors = [mock_kpp_1, mock_kpp_2]

        result = KernelExecutionResult(
            successes=[
                KernelTransitionInfo(
                    kernel_id=KernelId(uuid4()),
                    from_status=KernelStatus.RUNNING,
                )
            ],
            failures=[],
        )

        # Act
        await ScheduleCoordinator._run_kernel_post_processors(
            mock_coordinator,
            result=result,
            target_statuses={KernelStatus.TERMINATED},
        )

        # Assert
        mock_kpp_1.execute.assert_awaited_once()
        mock_kpp_2.execute.assert_awaited_once()

    def test_collect_target_statuses_from_result(
        self,
        status_transitions_with_all_outcomes: StatusTransitions,
    ) -> None:
        """SC-CO-025: Target statuses are collected from result.

        Given: Result with successes and classified failures
        When: Collect target statuses is called
        Then: All relevant target statuses are collected
        """
        # Arrange
        successes = [_create_session_transition_info()]
        classified = FailureClassificationResult(
            give_up=[_create_session_transition_info()],
            expired=[_create_session_transition_info()],
            need_retry=[_create_session_transition_info()],
        )

        # Act
        target_statuses = ScheduleCoordinator._collect_target_statuses(
            None,  # type: ignore[arg-type]
            transitions=status_transitions_with_all_outcomes,
            successes=successes,
            classified=classified,
        )

        # Assert
        assert SessionStatus.SCHEDULED in target_statuses  # Success transition
        assert SessionStatus.CANCELLED in target_statuses  # give_up and expired transition
        assert SessionStatus.PENDING in target_statuses  # need_retry transition
