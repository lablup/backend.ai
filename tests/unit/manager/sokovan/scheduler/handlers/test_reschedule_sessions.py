"""Unit tests for RescheduleSessionsLifecycleHandler."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.reschedule_sessions import (
    RescheduleSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.types import ScheduleType
from ai.backend.manager.views.sokovan.lifecycle import SessionWithKernels
from ai.backend.manager.views.sokovan.session import TerminatingSessionData


class TestRescheduleSessionsLifecycleHandler:
    """A RESCHEDULING session waits for its kernels to go, then returns to the
    queue. The handler is self-driven, so it always reports no transition."""

    @pytest.fixture
    def handler(
        self,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> RescheduleSessionsLifecycleHandler:
        return RescheduleSessionsLifecycleHandler(
            terminator=mock_terminator,
            repository=mock_repository,
            scheduling_controller=mock_scheduling_controller,
        )

    async def test_live_kernels_are_destroyed_and_checked_again(
        self,
        handler: RescheduleSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        rescheduling_session_live_kernels: SessionWithKernels,
        terminating_session_data_factory: Callable[..., list[TerminatingSessionData]],
    ) -> None:
        """While kernels remain, the destruction request is (re-)sent and the
        session is not requeued yet; the pass is not re-armed, so the agents are
        left to work until its next cycle."""
        sessions = [rescheduling_session_live_kernels]
        terminating_data = terminating_session_data_factory(sessions)
        mock_repository.get_terminating_sessions_by_ids.return_value = terminating_data

        result = await handler.execute(ResourceGroupID(uuid.uuid4()), sessions)

        assert result.successes == []
        mock_terminator.terminate_sessions_for_handler.assert_awaited_once_with(terminating_data)
        mock_scheduling_controller.mark_scheduling_needed.assert_not_awaited()
        mock_scheduling_controller.mark_sessions_status.assert_not_awaited()

    async def test_session_returns_to_pending_once_kernels_are_gone(
        self,
        handler: RescheduleSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        rescheduling_session_terminated_kernels: SessionWithKernels,
    ) -> None:
        """With every kernel terminal the session is re-enqueued and the schedule
        pass is requested."""
        session_id = rescheduling_session_terminated_kernels.session_info.identity.id
        mock_scheduling_controller.mark_sessions_status.return_value = [session_id]

        result = await handler.execute(
            ResourceGroupID(uuid.uuid4()), [rescheduling_session_terminated_kernels]
        )

        assert result.successes == []
        mock_repository.reset_kernels_to_pending_for_sessions.assert_awaited_once()
        call = mock_scheduling_controller.mark_sessions_status.await_args
        assert call.args[0] == [session_id]
        assert call.args[1] == SessionStatus.PENDING
        mock_scheduling_controller.mark_scheduling_needed.assert_any_await([ScheduleType.SCHEDULE])
        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()

    async def test_batch_splits_by_teardown_progress(
        self,
        handler: RescheduleSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        rescheduling_session_live_kernels: SessionWithKernels,
        rescheduling_session_terminated_kernels: SessionWithKernels,
        terminating_session_data_factory: Callable[..., list[TerminatingSessionData]],
    ) -> None:
        """A batch holding both a torn-down session and one still tearing down
        requeues the former and keeps destroying the latter."""
        live = rescheduling_session_live_kernels
        ready = rescheduling_session_terminated_kernels
        terminating_data = terminating_session_data_factory([live])
        mock_repository.get_terminating_sessions_by_ids.return_value = terminating_data

        await handler.execute(ResourceGroupID(uuid.uuid4()), [live, ready])

        mock_repository.get_terminating_sessions_by_ids.assert_awaited_once_with([
            live.session_info.identity.id
        ])
        mock_terminator.terminate_sessions_for_handler.assert_awaited_once_with(terminating_data)
        call = mock_scheduling_controller.mark_sessions_status.await_args
        assert call.args[0] == [ready.session_info.identity.id]
        assert call.args[1] == SessionStatus.PENDING

    async def test_empty_session_list_is_a_noop(
        self,
        handler: RescheduleSessionsLifecycleHandler,
        mock_terminator: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        result = await handler.execute(ResourceGroupID(uuid.uuid4()), [])

        assert result.successes == []
        mock_terminator.terminate_sessions_for_handler.assert_not_awaited()
        mock_scheduling_controller.mark_sessions_status.assert_not_awaited()
