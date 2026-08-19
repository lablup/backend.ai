"""Unit tests for PreemptSessionsLifecycleHandler (BEP-1055 eviction)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import PreemptionMode
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.preempt_sessions import (
    PreemptSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.types import ScheduleType
from ai.backend.manager.views.sokovan.lifecycle import SessionWithKernels

_REASON = "PREEMPTED_BY_SCHEDULER"


class TestPreemptSessionsLifecycleHandler:
    """The handler only routes victims by the resource group's preemption mode;
    the follow-up work belongs to the target status' own handler."""

    @pytest.fixture
    def handler(
        self,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> PreemptSessionsLifecycleHandler:
        return PreemptSessionsLifecycleHandler(
            repository=mock_repository,
            scheduling_controller=mock_scheduling_controller,
        )

    async def test_terminate_mode_sends_victims_to_termination(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        preempted_sessions_multiple: list[SessionWithKernels],
    ) -> None:
        """Terminate mode hands the victims to the standard termination path with
        the preemption reason; the handler itself reports no transition."""
        mock_repository.get_resource_group_preemption_mode.return_value = PreemptionMode.TERMINATE

        result = await handler.execute(ResourceGroupID(uuid.uuid4()), preempted_sessions_multiple)

        assert result.successes == []
        assert result.failures == []
        assert result.skipped == []
        expected_ids = [s.session_info.identity.id for s in preempted_sessions_multiple]
        call = mock_scheduling_controller.mark_sessions_for_termination.await_args
        assert call.args[0] == expected_ids
        assert call.kwargs["reason"] == _REASON
        mock_scheduling_controller.mark_sessions_status.assert_not_awaited()

    async def test_reschedule_mode_sends_victims_to_rescheduling(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        preempted_sessions_multiple: list[SessionWithKernels],
    ) -> None:
        """Reschedule mode moves the victims to RESCHEDULING under the same
        reason and requests that pass."""
        mock_repository.get_resource_group_preemption_mode.return_value = PreemptionMode.RESCHEDULE

        result = await handler.execute(ResourceGroupID(uuid.uuid4()), preempted_sessions_multiple)

        assert result.successes == []
        expected_ids = [s.session_info.identity.id for s in preempted_sessions_multiple]
        mock_scheduling_controller.mark_sessions_status.assert_awaited_once_with(
            expected_ids, SessionStatus.RESCHEDULING, reason=_REASON
        )
        mock_scheduling_controller.mark_scheduling_needed.assert_any_await([
            ScheduleType.RESCHEDULING
        ])
        mock_scheduling_controller.mark_sessions_for_termination.assert_not_awaited()

    async def test_empty_session_list_is_a_noop(
        self,
        handler: PreemptSessionsLifecycleHandler,
        mock_repository: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """With no victims the pass does nothing — not even a mode lookup."""
        result = await handler.execute(ResourceGroupID(uuid.uuid4()), [])

        assert result.successes == []
        mock_repository.get_resource_group_preemption_mode.assert_not_awaited()
        mock_scheduling_controller.mark_sessions_for_termination.assert_not_awaited()
        mock_scheduling_controller.mark_sessions_status.assert_not_awaited()
