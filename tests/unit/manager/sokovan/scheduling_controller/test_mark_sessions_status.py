"""Unit tests for ``SchedulingController.mark_sessions_status`` (BEP-1055)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)

_REASON = "PREEMPTED_BY_SCHEDULER"


def _build_controller() -> tuple[SchedulingController, AsyncMock, MagicMock, MagicMock]:
    """Controller with every collaborator mocked, plus the mocks under test."""
    repository = AsyncMock()
    event_producer = MagicMock()
    event_producer.broadcast_events_batch = AsyncMock()
    valkey_schedule = MagicMock()
    valkey_schedule.mark_schedules_needed_batch = AsyncMock()

    controller = SchedulingController(
        SchedulingControllerArgs(
            repository=repository,
            config_provider=MagicMock(),
            storage_manager=MagicMock(),
            event_producer=event_producer,
            valkey_schedule=valkey_schedule,
            network_plugin_ctx=MagicMock(),
            hook_plugin_ctx=MagicMock(),
            agent_selector=MagicMock(),
        )
    )
    return controller, repository, valkey_schedule, event_producer


class TestMarkSessionsStatus:
    async def test_transitioned_sessions_are_broadcast(self) -> None:
        """Sessions the repository moved are broadcast with the target status."""
        controller, repository, _valkey_schedule, event_producer = _build_controller()
        victims = [SessionId(uuid.uuid4()), SessionId(uuid.uuid4())]
        repository.mark_sessions_status.return_value = victims

        result = await controller.mark_sessions_status(victims, SessionStatus.PREEMPTED, _REASON)

        assert result == victims
        repository.mark_sessions_status.assert_awaited_once_with(
            victims, SessionStatus.PREEMPTED, _REASON
        )

        broadcast_events = event_producer.broadcast_events_batch.await_args.args[0]
        assert [event.session_id for event in broadcast_events] == victims
        for event in broadcast_events:
            assert event.status_transition == str(SessionStatus.PREEMPTED)
            assert event.reason == _REASON

    async def test_no_transitioned_session_is_a_noop(self) -> None:
        """When nothing transitioned, no broadcast is made."""
        controller, repository, _valkey_schedule, event_producer = _build_controller()
        repository.mark_sessions_status.return_value = []

        result = await controller.mark_sessions_status(
            [SessionId(uuid.uuid4())], SessionStatus.PREEMPTED, _REASON
        )

        assert result == []
        event_producer.broadcast_events_batch.assert_not_awaited()
