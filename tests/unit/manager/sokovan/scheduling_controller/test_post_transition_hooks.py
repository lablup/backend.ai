"""Tests for the post-transition hooks ``SchedulingController`` runs after it commits
session status transitions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.hooks.post_transition import (
    PostTransitionHook,
    PostTransitionHookRegistry,
)
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
from ai.backend.manager.views.sokovan.session import (
    MarkTerminatingResult,
    SessionStatusTransition,
)

_REASON = KernelLifecycleEventReason.USER_REQUESTED


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def hook() -> AsyncMock:
    return AsyncMock(spec=PostTransitionHook)


@pytest.fixture
def failing_hook() -> AsyncMock:
    failing = AsyncMock(spec=PostTransitionHook)
    failing.on_transitioned.side_effect = RuntimeError("post-transition hook failure")
    return failing


@pytest.fixture
def event_producer() -> MagicMock:
    producer = MagicMock()
    producer.broadcast_events_batch = AsyncMock()
    return producer


@pytest.fixture
def controller(
    repository: AsyncMock,
    hook: AsyncMock,
    failing_hook: AsyncMock,
    event_producer: MagicMock,
) -> SchedulingController:
    registry = PostTransitionHookRegistry()
    registry.register_for_all_transitions(failing_hook)
    registry.register_for_all_transitions(hook)
    valkey_schedule = MagicMock()
    valkey_schedule.mark_schedules_needed_batch = AsyncMock()
    valkey_schedule.add_force_terminated_sessions = AsyncMock()
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
            post_transition_hooks=registry,
        )
    )


def _transition(from_status: SessionStatus, to_status: SessionStatus) -> SessionStatusTransition:
    return SessionStatusTransition(
        session_id=SessionId(uuid4()), from_status=from_status, to_status=to_status
    )


class TestSchedulingControllerPostTransitionHooks:
    async def test_mark_sessions_status_runs_hooks_for_changed_sessions(
        self,
        controller: SchedulingController,
        repository: AsyncMock,
        hook: AsyncMock,
        event_producer: MagicMock,
    ) -> None:
        changed = _transition(SessionStatus.RUNNING, SessionStatus.PREEMPTED)
        unchanged = _transition(SessionStatus.PREEMPTED, SessionStatus.PREEMPTED)
        repository.mark_sessions_status.return_value = [changed, unchanged]

        marked = await controller.mark_sessions_status(
            [changed.session_id, unchanged.session_id], SessionStatus.PREEMPTED, _REASON
        )

        assert marked == [changed.session_id, unchanged.session_id]
        hook.on_transitioned.assert_awaited_once_with([changed])
        event_producer.broadcast_events_batch.assert_awaited_once()

    async def test_mark_sessions_for_termination_runs_hooks_per_target_status(
        self,
        controller: SchedulingController,
        repository: AsyncMock,
        hook: AsyncMock,
        event_producer: MagicMock,
    ) -> None:
        cancelled = _transition(SessionStatus.PENDING, SessionStatus.CANCELLED)
        terminating = _transition(SessionStatus.RUNNING, SessionStatus.TERMINATING)
        repository.mark_sessions_terminating.return_value = MarkTerminatingResult(
            cancelled_sessions=[cancelled.session_id],
            terminating_sessions=[terminating.session_id],
            force_terminated_sessions=[],
            skipped_sessions=[SessionId(uuid4())],
            transitions=[cancelled, terminating],
        )

        await controller.mark_sessions_for_termination(
            [cancelled.session_id, terminating.session_id], _REASON
        )

        assert hook.on_transitioned.await_args_list == [
            (([cancelled],),),
            (([terminating],),),
        ]
        event_producer.broadcast_events_batch.assert_awaited_once()
