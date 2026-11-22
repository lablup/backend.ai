"""Unit tests for the placement timeout path of ``SchedulingController``."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
from ai.backend.manager.views.sokovan.session import PlacementTimeoutRecord


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def event_producer() -> MagicMock:
    producer = MagicMock()
    producer.broadcast_events_batch = AsyncMock()
    return producer


@pytest.fixture
def valkey_schedule() -> MagicMock:
    valkey = MagicMock()
    valkey.mark_schedules_needed_batch = AsyncMock()
    return valkey


@pytest.fixture
def controller(
    repository: AsyncMock, event_producer: MagicMock, valkey_schedule: MagicMock
) -> SchedulingController:
    return SchedulingController(
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


@pytest.fixture
def session_id() -> SessionId:
    return SessionId(uuid.uuid4())


class TestHandlePlacementTimeout:
    async def test_recorded_timeout_is_broadcast_and_arms_rescheduling(
        self,
        controller: SchedulingController,
        repository: AsyncMock,
        event_producer: MagicMock,
        valkey_schedule: MagicMock,
        session_id: SessionId,
    ) -> None:
        record = PlacementTimeoutRecord(session_id=session_id, attempts=1)
        repository.record_placement_timeout.return_value = record

        result = await controller.handle_placement_timeout(session_id, "unschedulable", "no node")

        assert result == record
        repository.record_placement_timeout.assert_awaited_once_with(
            session_id, "unschedulable", "no node"
        )
        (event,) = event_producer.broadcast_events_batch.await_args.args[0]
        assert event.status_transition == str(SessionStatus.RESCHEDULING)
        assert event.reason == KernelLifecycleEventReason.PLACEMENT_TIMEOUT
        valkey_schedule.mark_schedules_needed_batch.assert_awaited_once_with([
            ScheduleType.RESCHEDULING.value
        ])

    async def test_ignored_timeout_changes_nothing(
        self,
        controller: SchedulingController,
        repository: AsyncMock,
        event_producer: MagicMock,
        valkey_schedule: MagicMock,
        session_id: SessionId,
    ) -> None:
        repository.record_placement_timeout.return_value = None

        assert await controller.handle_placement_timeout(session_id, "unschedulable", None) is None
        event_producer.broadcast_events_batch.assert_not_awaited()
        valkey_schedule.mark_schedules_needed_batch.assert_not_awaited()


class TestCancelReschedulingSessions:
    async def test_cancelled_sessions_are_broadcast(
        self,
        controller: SchedulingController,
        repository: AsyncMock,
        event_producer: MagicMock,
        session_id: SessionId,
    ) -> None:
        repository.cancel_rescheduling_sessions.return_value = [session_id]

        cancelled = await controller.cancel_rescheduling_sessions(
            [session_id], KernelLifecycleEventReason.PLACEMENT_TIMEOUT
        )

        assert cancelled == [session_id]
        (event,) = event_producer.broadcast_events_batch.await_args.args[0]
        assert event.status_transition == str(SessionStatus.CANCELLED)
