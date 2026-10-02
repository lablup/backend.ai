"""Unit tests for ``SchedulingController.mark_sessions_status`` (BEP-1055)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
from ai.backend.manager.views.sokovan.session import MarkTerminatingResult

_REASON = KernelLifecycleEventReason.PREEMPTED_BY_SCHEDULER


def _build_controller() -> tuple[SchedulingController, AsyncMock, MagicMock, MagicMock]:
    """Controller with every collaborator mocked, plus the mocks under test."""
    repository = AsyncMock()
    event_producer = MagicMock()
    event_producer.broadcast_events_batch = AsyncMock()
    event_producer.anycast_event = AsyncMock()
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

    async def test_transitioned_sessions_are_anycast(self) -> None:
        """Each moved session gets one transition anycast, which drives the session callback."""
        controller, repository, _valkey_schedule, event_producer = _build_controller()
        victims = [SessionId(uuid.uuid4()), SessionId(uuid.uuid4())]
        repository.mark_sessions_status.return_value = victims

        await controller.mark_sessions_status(victims, SessionStatus.PREEMPTED, _REASON)

        anycast = [call.args[0] for call in event_producer.anycast_event.await_args_list]
        assert [(e.session_id, e.status, e.reason) for e in anycast] == [
            (victim, "PREEMPTED", _REASON) for victim in victims
        ]


class TestMarkSessionsForTermination:
    async def test_every_marked_session_is_anycast_with_its_status(self) -> None:
        controller, repository, valkey_schedule, event_producer = _build_controller()
        valkey_schedule.add_force_terminated_sessions = AsyncMock()
        cancelled, terminating, terminated = (SessionId(uuid.uuid4()) for _ in range(3))
        repository.mark_sessions_terminating.return_value = MarkTerminatingResult(
            cancelled_sessions=[cancelled],
            terminating_sessions=[terminating],
            force_terminated_sessions=[terminated],
            skipped_sessions=[SessionId(uuid.uuid4())],
        )

        await controller.mark_sessions_for_termination(
            [cancelled, terminating, terminated], _REASON
        )

        anycast = [call.args[0] for call in event_producer.anycast_event.await_args_list]
        assert [(e.session_id, e.status) for e in anycast] == [
            (cancelled, "CANCELLED"),
            (terminating, "TERMINATING"),
            (terminated, "TERMINATED"),
        ]
        broadcast = event_producer.broadcast_events_batch.await_args.args[0]
        assert [e.status_transition for e in broadcast] == [
            "CANCELLED",
            "TERMINATING",
            "TERMINATED",
        ]
        assert {e.creation_id for e in broadcast} == {""}
